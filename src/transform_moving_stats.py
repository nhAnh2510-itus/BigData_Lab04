
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, stddev, to_timestamp, lit
from pyspark.sql.types import StructType, StringType, FloatType
from functools import reduce
from pyspark.sql import DataFrame

print("Starting Spark Streaming - All Windows")

# 1. Schema JSON từ extract.py
schema = StructType() \
    .add("symbol", StringType()) \
    .add("price", FloatType()) \
    .add("event_time", StringType())

# 2. Tạo SparkSession
spark = SparkSession.builder \
    .appName("BTC Moving Stats - All Sliding Windows") \
    .getOrCreate()

# 3. Đọc stream từ Kafka topic 'btc-price'
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "btc-price") \
    .load()

# 4. Parse JSON và chuyển event_time thành timestamp
json_df = df.select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_time", to_timestamp("event_time"))

# 5. Danh sách sliding windows: { label: (window_duration, slide_duration) }
windows = {
    "30s":  ("30 seconds", "10 seconds"),
    "1m":   ("1 minute",    "10 seconds"),
    "5m":   ("5 minutes",   "30 seconds"),
    "15m":  ("15 minutes",  "1 minute"),
    "30m":  ("30 minutes",  "5 minutes"),
    "1h":   ("1 hour",      "10 minutes")
}

windowed_dfs = []

# 6. Tính trung bình và stddev cho từng loại cửa sổ
for label, (window_duration, slide_duration) in windows.items():
    agg_df = json_df.withWatermark("event_time", "10 seconds") \
        .groupBy(window(col("event_time"), window_duration, slide_duration)) \
        .agg(
            avg("price").alias("avg_price"),
            stddev("price").alias("std_price")
        ) \
        .withColumn("symbol", lit("BTCUSDT")) \
        .withColumn("window_label", lit(label)) \
        .select(
            col("window.start").alias("timestamp"),
            col("window.end").alias("window_end"),
            col("symbol"),
            col("avg_price"),
            col("std_price"),
            col("window_label").alias("window")
        )
    windowed_dfs.append(agg_df)

# 7. Gộp kết quả từ tất cả các cửa sổ lại
final_df = reduce(DataFrame.unionAll, windowed_dfs)

# 8. Ghi kết quả ra console để kiểm thử
query = final_df.writeStream \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 100) \
    .outputMode("append") \
    .start()

query.awaitTermination()
