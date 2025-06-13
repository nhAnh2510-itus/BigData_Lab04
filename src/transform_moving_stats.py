from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    window, avg, stddev, col, struct, array, lit, to_json, from_json
)
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType
import os

def main():
    """
    Hàm chính để chạy pipeline tính toán thống kê trượt.
    """
    # === Cấu hình Kafka ===
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    INPUT_TOPIC = "btc-price"
    OUTPUT_TOPIC = "btc-price-moving"

    # 1) Tạo SparkSession với cấu hình tối ưu cho Docker
    spark_master = os.getenv('SPARK_MASTER', 'local[*]')
    
    spark = SparkSession.builder \
        .appName("MovingStats_Tumbling_WithJoins") \
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

    # 2) Định nghĩa schema và đọc stream, gắn watermark sớm
    schema = StructType() \
        .add("symbol", StringType()) \
        .add("price", DoubleType()) \
        .add("event_time", TimestampType())

    df_raw = (
        spark.readStream
             .format("kafka")
             .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
             .option("subscribe", INPUT_TOPIC)
             .option("startingOffsets", "latest")
             .option("maxOffsetsPerTrigger", 1000)
             .option("failOnDataLoss", "false")
             .load()
             .selectExpr("CAST(value AS STRING) as json_str")
             .select(from_json("json_str", schema).alias("data"))
             .select("data.symbol", "data.price", "data.event_time")
    )

    # 3) Tạo các DataFrame stats với tumbling window - đầy đủ theo yêu cầu
    stats30s = (
        df_raw
          .withWatermark("event_time", "10 seconds")
          .groupBy(window("event_time", "30 seconds", "10 seconds"), col("symbol"))
          .agg(avg("price").alias("avg_30s"), stddev("price").alias("std_30s"))
          .select(
              col("symbol"),
              col("window.end").alias("timestamp"),
              col("avg_30s"),
              col("std_30s")
          )
    )

    stats1m = (
        df_raw
          .withWatermark("event_time", "10 seconds")
          .groupBy(window("event_time", "1 minute", "10 seconds"), col("symbol"))
          .agg(avg("price").alias("avg_1m"), stddev("price").alias("std_1m"))
          .select(
              col("symbol"),
              col("window.end").alias("timestamp"),
              col("avg_1m"),
              col("std_1m")
          )
    )

    stats5m = (
        df_raw
          .withWatermark("event_time", "10 seconds")
          .groupBy(window("event_time", "5 minutes", "10 seconds"), col("symbol"))
          .agg(avg("price").alias("avg_5m"), stddev("price").alias("std_5m"))
          .select(
              col("symbol"),
              col("window.end").alias("timestamp"),
              col("avg_5m"),
              col("std_5m")
          )
    )

    stats15m = (
        df_raw
          .withWatermark("event_time", "10 seconds")
          .groupBy(window("event_time", "15 minutes", "10 seconds"), col("symbol"))
          .agg(avg("price").alias("avg_15m"), stddev("price").alias("std_15m"))
          .select(
              col("symbol"),
              col("window.end").alias("timestamp"),
              col("avg_15m"),
              col("std_15m")
          )
    )

    stats30m = (
        df_raw
          .withWatermark("event_time", "10 seconds")
          .groupBy(window("event_time", "30 minutes", "10 seconds"), col("symbol"))
          .agg(avg("price").alias("avg_30m"), stddev("price").alias("std_30m"))
          .select(
              col("symbol"),
              col("window.end").alias("timestamp"),
              col("avg_30m"),
              col("std_30m")
          )
    )

    stats1h = (
        df_raw
          .withWatermark("event_time", "10 seconds")
          .groupBy(window("event_time", "1 hour", "10 seconds"), col("symbol"))
          .agg(avg("price").alias("avg_1h"), stddev("price").alias("std_1h"))
          .select(
              col("symbol"),
              col("window.end").alias("timestamp"),
              col("avg_1h"),
              col("std_1h")
          )
    )

    # 5) Join tất cả các window
    joined = (
        stats30s
          .join(stats1m, on=["symbol", "timestamp"], how="inner")
          .join(stats5m, on=["symbol", "timestamp"], how="inner")
          .join(stats15m, on=["symbol", "timestamp"], how="inner")
          .join(stats30m, on=["symbol", "timestamp"], how="inner")
          .join(stats1h, on=["symbol", "timestamp"], how="inner")
          .select(
              col("symbol"),
              col("timestamp"),
              array(
                struct(lit("30s").alias("window"),
                       col("avg_30s").alias("avg_price"),
                       col("std_30s").alias("std_price")),
                struct(lit("1m").alias("window"),
                       col("avg_1m").alias("avg_price"),
                       col("std_1m").alias("std_price")),
                struct(lit("5m").alias("window"),
                       col("avg_5m").alias("avg_price"),
                       col("std_5m").alias("std_price")),
                struct(lit("15m").alias("window"),
                       col("avg_15m").alias("avg_price"),
                       col("std_15m").alias("std_price")),
                struct(lit("30m").alias("window"),
                       col("avg_30m").alias("avg_price"),
                       col("std_30m").alias("std_price")),
                struct(lit("1h").alias("window"),
                       col("avg_1h").alias("avg_price"),
                       col("std_1h").alias("std_price"))
              ).alias("windows")
          )
    )

    # 6) Chuyển thành JSON và xuất ra Kafka
    output = joined.select(
        to_json(struct(col("timestamp"), col("symbol"), col("windows"))).alias("value")
    )

    # Ghi ra Kafka
    query = output.writeStream \
          .format("kafka") \
          .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
          .option("topic", OUTPUT_TOPIC) \
          .option("checkpointLocation", "./checkpoints/moving_stats_full") \
          .outputMode("append") \
          .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()