
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, stddev, to_timestamp, lit, collect_list, struct, to_json
from pyspark.sql.types import StructType, StringType, FloatType
from functools import reduce
from pyspark.sql import DataFrame

print("Starting Spark Streaming - Moving Stats (Step 1)")

# 1. Schema JSON từ extract.py
schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", FloatType()) \
    .add("event_time", StringType())

# 2. Tạo SparkSession với optimization configs
spark = SparkSession.builder \
    .appName("BTC Moving Stats - Step 1") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .config("spark.sql.streaming.kafka.consumer.cache.capacity", "256") \
    .config("spark.sql.streaming.kafka.consumer.cache.enabled", "true") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.sql.streaming.maxFilesPerTrigger", "100") \
    .getOrCreate()

# 3. Lấy Kafka bootstrap servers từ environment variable
KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')

# 4. Đọc stream từ Kafka topic 'btc-price'
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVERS) \
    .option("subscribe", "btc-price") \
    .load()

# 5. Parse JSON và chuyển event_time thành timestamp
json_df = df.select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_time", to_timestamp("event_time"))

# 6. Optimized sliding windows - reduced slide duration để giảm computation
# Cấu hình slide duration hợp lý để có đủ dữ liệu và không quá nhiều output
windows = {
    "30s":  ("30 seconds", "10 seconds"),  # Slide mỗi 10s cho window 30s
    "1m":   ("1 minute",   "20 seconds"),  # Slide mỗi 20s cho window 1m
    "5m":   ("5 minutes",  "1 minute"),    # Slide mỗi 1m cho window 5m
    "15m":  ("15 minutes", "3 minutes"),   # Slide mỗi 3m cho window 15m
    "30m":  ("30 minutes", "5 minutes"),   # Slide mỗi 5m cho window 30m
    "1h":   ("1 hour",     "10 minutes")   # Slide mỗi 10m cho window 1h
}

windowed_dfs = []

# 7. Tính moving average và std cho từng window với reduced watermark
for label, (window_duration, slide_duration) in windows.items():
    agg_df = json_df.withWatermark("event_time", "5 seconds") \
        .groupBy(window(col("event_time"), window_duration, slide_duration)) \
        .agg(
            avg("price").alias("avg_price"),
            stddev("price").alias("std_price")
        ) \
        .withColumn("window_label", lit(label)) \
        .select(
            col("window.start").alias("timestamp"),
            col("window_label").alias("window"),
            col("avg_price"),
            col("std_price")
        )
    windowed_dfs.append(agg_df)

# 8. Union tất cả windows lại
all_windows_df = reduce(DataFrame.unionAll, windowed_dfs)

# 9. Group by timestamp để tạo JSON format theo yêu cầu Lab
final_df = all_windows_df.groupBy("timestamp") \
    .agg(
        lit("BTCUSDT").alias("symbol"),
        collect_list(
            struct(
                col("window").alias("window"),
                col("avg_price").alias("avg_price"), 
                col("std_price").alias("std_price")
            )
        ).alias("windows")
    ) \
    .select(
        col("timestamp").cast("string").alias("timestamp"),
        col("symbol"),
        col("windows")
    )

# 10. Chuyển thành JSON và ghi vào Kafka topic btc-price-moving
json_output = final_df.select(
    to_json(struct(
        col("timestamp"),
        col("symbol"),
        col("windows")
    )).alias("value")
)

# 11. Ghi vào topic btc-price-moving với optimized configs
query = json_output.writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVERS) \
    .option("topic", "btc-price-moving") \
    .option("kafka.batch.size", "16384") \
    .option("kafka.linger.ms", "5") \
    .option("kafka.compression.type", "gzip") \
    .option("kafka.buffer.memory", "33554432") \
    .option("checkpointLocation", "/tmp/checkpoint-moving-stats") \
    .outputMode("update") \
    .trigger(processingTime='5 seconds') \
    .start()

# 12. Console output với reduced frequency để giảm overhead
console_query = final_df.writeStream \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 10) \
    .outputMode("update") \
    .trigger(processingTime='30 seconds') \
    .start()

print("✅ Transform Step 1 started: Computing moving averages and sending to btc-price-moving topic")

# Chờ cả hai queries
try:
    query.awaitTermination()
except KeyboardInterrupt:
    print("\n🛑 Stopping Transform Step 1...")
    query.stop()
    console_query.stop()
    spark.stop()
