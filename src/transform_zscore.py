from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, struct, array, lit, to_json, from_json, explode, when, isnan, isnull, collect_list
)
from pyspark.sql.types import (
    StructType, StringType, DoubleType, TimestampType, ArrayType
)
import os

def main():
    """
    Hàm chính để chạy pipeline tính toán Z-score bằng stream-stream join.
    Joins data từ btc-price và btc-price-moving topics để tính Z-score cho mỗi window.
    """
    # === Cấu hình Kafka ===
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    PRICE_TOPIC = "btc-price"
    MOVING_TOPIC = "btc-price-moving"
    OUTPUT_TOPIC = "btc-price-zscore"

    # 1) Tạo SparkSession với cấu hình tối ưu cho stream-stream joins
    spark_master = os.getenv('SPARK_MASTER', 'local[*]')
    
    spark = SparkSession.builder \
        .appName("ZScore_StreamStream_Join") \
        .master(spark_master) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .config("spark.sql.streaming.checkpointLocation", "/app/checkpoints") \
        .config("spark.driver.memory", "1g") \
        .config("spark.executor.memory", "1g") \
        .config("spark.driver.maxResultSize", "512m") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"✅ Spark Session created successfully!")
    print(f"🔗 Spark Master: {spark_master}")
    print(f"📡 Kafka Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"💾 Checkpoint Location: /app/checkpoints")
    print(f"🔄 Stream-Stream Join: {PRICE_TOPIC} + {MOVING_TOPIC} → {OUTPUT_TOPIC}")

    # 2) Schema cho btc-price topic
    price_schema = StructType() \
        .add("symbol", StringType()) \
        .add("price", DoubleType()) \
        .add("event_time", TimestampType())

    # 3) Schema cho btc-price-moving topic
    window_schema = StructType() \
        .add("window", StringType()) \
        .add("avg_price", DoubleType()) \
        .add("std_price", DoubleType())
    
    moving_schema = StructType() \
        .add("timestamp", TimestampType()) \
        .add("symbol", StringType()) \
        .add("windows", ArrayType(window_schema))

    # 4) Đọc stream từ btc-price topic
    df_price = (
        spark.readStream
             .format("kafka")
             .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
             .option("subscribe", PRICE_TOPIC)
             .option("startingOffsets", "latest")
             .option("maxOffsetsPerTrigger", 1000)
             .option("failOnDataLoss", "false")
             .load()
             .selectExpr("CAST(value AS STRING) as json_str")
             .select(from_json("json_str", price_schema).alias("data"))
             .select(
                 col("data.symbol").alias("symbol"),
                 col("data.price").alias("current_price"),
                 col("data.event_time").alias("event_time")
             )
             .withWatermark("event_time", "30 seconds")
    )

    # 5) Đọc stream từ btc-price-moving topic
    df_moving = (
        spark.readStream
             .format("kafka")
             .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
             .option("subscribe", MOVING_TOPIC)
             .option("startingOffsets", "latest")
             .option("maxOffsetsPerTrigger", 1000)
             .option("failOnDataLoss", "false")
             .load()
             .selectExpr("CAST(value AS STRING) as json_str")
             .select(from_json("json_str", moving_schema).alias("data"))
             .select(
                 col("data.symbol").alias("symbol"),
                 col("data.timestamp").alias("timestamp"),
                 col("data.windows").alias("windows")
             )
             .withWatermark("timestamp", "30 seconds")
    )

    # 6) Flatten windows array để dễ join
    df_moving_flat = (
        df_moving
        .select(
            col("symbol"),
            col("timestamp"),
            explode("windows").alias("window_data")
        )
        .select(
            col("symbol"),
            col("timestamp"),
            col("window_data.window").alias("window"),
            col("window_data.avg_price").alias("avg_price"),
            col("window_data.std_price").alias("std_price")
        )
    )

    # 7) Stream-stream join với watermarking
    # Join condition: cùng symbol và timestamp gần nhau (trong vòng 1 phút)
    joined_df = (
        df_price.alias("price")
        .join(
            df_moving_flat.alias("moving"),
            (col("price.symbol") == col("moving.symbol")) &
            (col("price.event_time") == col("moving.timestamp")),
            "inner"
        )
        .select(
            col("price.symbol").alias("symbol"),
            col("price.event_time").alias("timestamp"),
            col("price.current_price").alias("current_price"),
            col("moving.window").alias("window"),
            col("moving.avg_price").alias("avg_price"),
            col("moving.std_price").alias("std_price")
        )
    )

    # 8) Tính Z-score với edge case handling
    df_zscore = joined_df.select(
        col("symbol"),
        col("timestamp"),
        col("window"),
        col("current_price"),
        col("avg_price"),
        col("std_price"),
        # Z-score calculation với edge case handling
        when(
            (col("std_price").isNull()) | 
            (isnan(col("std_price"))) | 
            (col("std_price") == 0.0),
            lit(0.0)  # Nếu std = 0 hoặc null thì Z-score = 0
        ).otherwise(
            (col("current_price") - col("avg_price")) / col("std_price")
        ).alias("zscore_price")
    )

    # 9) Group lại theo symbol, timestamp để tạo array các Z-scores
    df_zscore_grouped = (
        df_zscore
        .groupBy("symbol", "timestamp")
        .agg(
            collect_list(
                struct(
                    col("window").alias("window"),
                    col("zscore_price").alias("zscore_price")
                )
            ).alias("zscores")
        )
    )

    # 10) Format kết quả theo yêu cầu
    df_output = df_zscore_grouped.select(
        to_json(
            struct(
                col("timestamp"),
                col("symbol"),
                col("zscores")
            )
        ).alias("value")
    )

    # 11) Xuất kết quả ra Kafka topic btc-price-zscore
    query = (
        df_output.writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("topic", OUTPUT_TOPIC)
        .option("checkpointLocation", "./checkpoints/zscore_stream_join")
        .outputMode("append")
        .trigger(processingTime="10 seconds")  # Process every 10 seconds
        .start()
    )

    print("🚀 Z-Score Stream-Stream Join started!")
    print("📊 Computing Z-scores for windows: 30s, 1m, 5m, 15m, 30m, 1h")
    print("💡 Edge cases handled: std_price = 0 or null → zscore = 0")
    print("🔄 Press Ctrl+C to stop...")

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n🛑 Stopping Z-Score computation...")
        query.stop()
        spark.stop()

if __name__ == "__main__":
    main()
