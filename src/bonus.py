import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    expr,
    from_json,
    to_json,
    struct,
    when,
    lit,
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
    spark_master = os.getenv('SPARK_MASTER', 'local[*]')
    
    return (
        SparkSession.builder
        .appName("BTC_Shortest_Windows_Analysis_Fixed")
        .master(spark_master)
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.streaming.stateStore.maintenanceInterval", "60s")
        .getOrCreate()
    )

def find_shortest_windows_and_publish(spark, kafka_servers):
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
        .withColumn("join_key", lit("btc"))
    )

    left_stream = price_stream.alias("left")
    right_stream = price_stream.alias("right")

    joined_stream = left_stream.join(
        right_stream,
        expr("""
            left.join_key = right.join_key AND 
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
        .option("checkpointLocation", "./checkpoint/bonus_windows")
        .outputMode("append")
        .start()
    )

    spark.streams.awaitAnyTermination()


def main():
    """Main function to orchestrate the Spark application"""
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    spark = None
    try:
        spark = create_spark_session()
        find_shortest_windows_and_publish(spark, KAFKA_BOOTSTRAP_SERVERS)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        if spark:
            spark.stop()



if __name__ == "__main__":
    main()