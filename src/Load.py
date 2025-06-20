from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType, ArrayType
)

# 1. Tạo SparkSession
spark = SparkSession.builder \
    .appName("KafkaZScoreToMongo") \
    .config("spark.mongodb.write.connection.uri", "mongodb+srv://") \
    .getOrCreate()

# 2. Schema tương ứng với dữ liệu zscore
zscore_schema = StructType([
    StructField("timestamp", TimestampType()),
    StructField("symbol", StringType()),
    StructField("zscores", ArrayType(
        StructType([
            StructField("window", StringType()),
            StructField("zscore_price", DoubleType())
        ])
    ))
])

# 3. Đọc dữ liệu từ Kafka topic "btc-price-zscore"
df = (
    spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "3.88.194.149:9092")
        .option("subscribe", "btc-price-zscore")
        .option("startingOffsets", "latest")
        .load()
        .selectExpr("CAST(value AS STRING) AS json_str")
        .select(from_json(col("json_str"), zscore_schema).alias("data"))
        .select("data.*")
)

# 4. Ghi dữ liệu vào MongoDB
df.writeStream \
    .format("mongodb") \
    .option("checkpointLocation", "/home/nguyen1712004/checkpoint/mongo-zscore") \
    .option("spark.mongodb.write.connection.uri", "mongodb+srv://") \
    .option("spark.mongodb.write.database", "crypto") \
    .option("spark.mongodb.write.collection", "btc-price-zscore") \
    .outputMode("append") \
    .start()

spark.streams.awaitAnyTermination()

