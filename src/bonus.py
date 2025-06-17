# btc_windows_analysis_fixed.py

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    expr,
    from_json,
    to_json,
    struct,
    when,
    lit,  # <--- THAY ĐỔI: Import hàm lit
    min as spark_min,
)
from pyspark.sql.types import (
    StructType,
    StringType,
    DoubleType,
    TimestampType,
    FloatType,
)

def create_spark_session():
    """
    Creates and configures a Spark session optimized for structured streaming
    with Kafka and stateful operations.
    """
    spark_master = os.getenv('SPARK_MASTER', 'local[*]')
    
    return (
        SparkSession.builder
        .appName("BTC_Shortest_Windows_Analysis_Fixed")
        .master(spark_master)
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.streaming.stateStore.maintenanceInterval", "60s")
        # .config("spark.sql.adaptive.enabled", "true") # This setting is not for streaming
        .getOrCreate()
    )

def find_shortest_windows_and_publish(spark, kafka_servers):
    """
    Reads the btc-price stream, finds the shortest negative outcome windows
    using a stream-stream self-join, and publishes results to Kafka.
    """
    price_schema = (
        StructType()
        .add("symbol", StringType())
        .add("price", DoubleType())
        .add("event_time", TimestampType())
    )

    price_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_servers)
        .option("subscribe", "btc-price")
        .option("startingOffsets", "latest")
        .load()
        .select(from_json(col("value").cast("string"), price_schema).alias("data"))
        .select("data.*")
        .filter(col("price").isNotNull() & col("event_time").isNotNull())
        .withWatermark("event_time", "10 seconds")
        # <--- THAY ĐỔI: Thêm cột khóa giả để thỏa mãn điều kiện join
        .withColumn("join_key", lit("btc"))
    )

    left_stream = price_stream.alias("left")
    right_stream = price_stream.alias("right")

    # <--- THAY ĐỔI: Cập nhật điều kiện join để bao gồm equality predicate
    joined_stream = left_stream.join(
        right_stream,
        expr("""
            -- 1. Equality predicate (BẮT BUỘC)
            left.join_key = right.join_key AND 
            -- 2. Time-range condition
            right.event_time > left.event_time AND
            right.event_time <= left.event_time + interval 20 seconds
        """),
        "leftOuter"
    )

    shortest_windows = joined_stream.groupBy(
        col("left.event_time"), col("left.price")
    ).agg(
        spark_min(when(col("right.price") > col("left.price"), col("right.event_time"))).alias("first_higher_ts"),
        spark_min(when(col("right.price") < col("left.price"), col("right.event_time"))).alias("first_lower_ts")
    )

    results = shortest_windows.withColumn(
        "higher_window",
        when(
            col("first_higher_ts").isNotNull(),
            col("first_higher_ts").cast("double") - col("event_time").cast("double")
        ).otherwise(20.0)
    ).withColumn(
        "lower_window",
        when(
            col("first_lower_ts").isNotNull(),
            col("first_lower_ts").cast("double") - col("event_time").cast("double")
        ).otherwise(20.0)
    ).select(
        col("event_time").alias("timestamp"),
        col("higher_window").cast(FloatType()),
        col("lower_window").cast(FloatType())
    )

    higher_output_stream = results.select(
        to_json(
            struct(col("timestamp"), col("higher_window"))
        ).alias("value")
    )

    query_higher = (
        higher_output_stream.writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_servers)
        .option("topic", "btc-price-higher")
        .option("checkpointLocation", "/tmp/checkpoints/btc_windows_higher")
        .outputMode("append")
        .start()
    )

    lower_output_stream = results.select(
        to_json(
            struct(col("timestamp"), col("lower_window"))
        ).alias("value")
    )
    
    query_lower = (
        lower_output_stream.writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_servers)
        .option("topic", "btc-price-lower")
        .option("checkpointLocation", "/tmp/checkpoints/btc_windows_lower")
        .outputMode("append")
        .start()
    )
    
    print("🚀 Started publishing to 'btc-price-higher' and 'btc-price-lower' topics.")
    print("✅ Both streaming queries are running in parallel.")
    
    spark.streams.awaitAnyTermination()


def main():
    """Main function to orchestrate the Spark application"""
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    spark = None
    try:
        spark = create_spark_session()
        print("✅ Spark session created successfully.")
        find_shortest_windows_and_publish(spark, KAFKA_BOOTSTRAP_SERVERS)
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if spark:
            print("🏁 Stopping Spark session...")
            spark.stop()
            print("✅ Spark session stopped.")


if __name__ == "__main__":
    main()