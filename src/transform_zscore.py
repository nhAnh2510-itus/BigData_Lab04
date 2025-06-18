from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    window, avg, stddev, col, struct, array, lit, to_json, from_json,expr
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType,
    TimestampType, ArrayType
)


# 1) Tạo SparkSession
spark = SparkSession.builder \
        .appName("ZScore_StreamStream_Join") \
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


schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", DoubleType()) \
    .add("event_time", TimestampType())

windowElemSchema = StructType([
    StructField("window", StringType(), nullable=False),
    StructField("avg_price", DoubleType(), nullable=True),
    StructField("std_price", DoubleType(), nullable=True),
])

# Schema tổng cho bản tin moving-stats
movingStatsSchema = StructType([
    StructField("timestamp", TimestampType(), nullable=False),
    StructField("symbol",    StringType(),    nullable=False),
    StructField("windows",   ArrayType(windowElemSchema), nullable=False),
])


df_raw = (
    spark.readStream
         .format("kafka")
         .option("kafka.bootstrap.servers", "localhost:9092")
         .option("subscribe", "btc-price")
         .option("startingOffsets", "latest")
         .load()
         .selectExpr("CAST(value AS STRING) as json_str")
         .select(from_json("json_str", schema).alias("data"))
         .select("data.symbol", "data.price", "data.event_time")
         .withWatermark("event_time", "1 minute")
)



df_moving = (
    spark.readStream
         .format("kafka")
         .option("kafka.bootstrap.servers", "localhost:9092")
         .option("subscribe", "btc-price-moving")
         .load()
         .selectExpr("CAST(value AS STRING) AS json_str")
         .select(from_json(col("json_str"), movingStatsSchema).alias("data"))
         .select("data.*")
         .withWatermark("timestamp", "30 seconds")
)



from pyspark.sql.functions import col, expr


raw   = df_raw  .alias("raw")   
mov   = df_moving.alias("mov")  


joined = raw.join(mov, on="symbol", how="inner") \
            .where(
               (col("event_time") >= expr("mov.timestamp - INTERVAL 0.1 SECOND")) &
               (col("event_time") <= expr("mov.timestamp + INTERVAL 0.1 SECOND"))
            )


# 3) Tiếp tục explode + compute zscore…



# Sau join, bạn có: df_raw.price, df_moving.windows

result = joined.withColumn(
    "zscores",
    expr("""
      transform(
        windows,
        w -> struct(
          w.window AS window,
          (price - w.avg_price) / w.std_price AS zscore_price
        )
      )
    """)
).select(
    col("event_time").alias("timestamp"),
    col("symbol"),
    col("zscores")
)




# Chuyển thành JSON đúng format, và đặt tên là "value"

output = result.select(
    to_json(struct("timestamp", "symbol", "zscores")).alias("value")
)


output.writeStream \
          .format("kafka") \
          .option("kafka.bootstrap.servers", "localhost:9092") \
          .option("topic", "btc-price-zscore") \
          .option("checkpointLocation", "C:\\users\\admin\\checkpoint_1\\console") \
          .outputMode("append") \
          .start()

spark.streams.awaitAnyTermination()

## spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5 --master local[*] C:\sparkCourse\Zscore.py

