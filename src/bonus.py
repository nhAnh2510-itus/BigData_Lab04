"""
Bonus Implementation: Shortest Windows of Negative Outcomes

This module implements a Spark Structured Streaming application that finds the shortest
windows of negative outcomes for each Bitcoin price record. For each price record p with
timestamp t, it finds the first occurrence of:
1. A higher price in the 20-second window (t, t+20]
2. A lower price in the 20-second window (t, t+20]

The results are published to separate Kafka topics with time differences in seconds.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, expr, to_json, struct, lit, 
    unix_timestamp, current_timestamp, date_format,
    collect_list, size, filter as spark_filter, sort_array,
    coalesce, array_min, explode, posexplode
)
from pyspark.sql.types import (
    StructType, StringType, DoubleType, TimestampType, 
    FloatType, ArrayType, IntegerType
)
import os


def create_spark_session():
    """Create and configure Spark session for streaming"""
    spark_master = os.getenv('SPARK_MASTER', 'local[*]')
    
    spark = SparkSession.builder \
        .appName("BTC_Shortest_Windows_Analysis") \
        .master(spark_master) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .config("spark.sql.streaming.checkpointLocation", "/app/checkpoints/bonus_windows") \
        .config("spark.driver.memory", "1g") \
        .config("spark.executor.memory", "1g") \
        .config("spark.driver.maxResultSize", "512m") \
        .config("spark.sql.streaming.stateStore.maintenanceInterval", "30s") \
        .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def create_input_stream(spark, kafka_servers):
    """Create input stream from Kafka btc-price topic"""
    schema = StructType() \
        .add("symbol", StringType()) \
        .add("price", DoubleType()) \
        .add("event_time", TimestampType())

    return (
        spark.readStream
             .format("kafka")
             .option("kafka.bootstrap.servers", kafka_servers)
             .option("subscribe", "btc-price")
             .option("startingOffsets", "latest")
             .option("maxOffsetsPerTrigger", "200")
             .load()
             .selectExpr("CAST(value AS STRING) as json_string", "timestamp as kafka_timestamp")
             .select(
                 expr("from_json(json_string, 'symbol string, price double, event_time timestamp') as data"),
                 col("kafka_timestamp")
             )
             .select(
                 col("data.symbol").alias("symbol"),
                 col("data.price").alias("price"),
                 col("data.event_time").alias("event_time")
             )
             .filter(col("price").isNotNull() & col("event_time").isNotNull())
             .withWatermark("event_time", "10 seconds")  # 10 seconds late data tolerance
             .withColumn("timestamp_seconds", unix_timestamp(col("event_time")).cast(DoubleType()))
    )


def find_windows_with_foreachbatch(df):
    """
    Use foreachBatch to process each batch and find shortest windows.
    This approach gives us more control over the complex logic.
    """
    
    def process_batch(batch_df, batch_id):
        """Process each batch to find shortest windows"""
        if batch_df.count() == 0:
            return
            
        print(f"Processing batch {batch_id} with {batch_df.count()} records")
        
        # Collect all data for processing
        data = batch_df.collect()
        
        # Create results list
        higher_results = []
        lower_results = []
        
        # Process each record to find windows
        for i, base_record in enumerate(data):
            base_price = base_record['price']
            base_time = base_record['event_time']
            base_timestamp = base_record['timestamp_seconds']
            
            # Find higher and lower prices within 20 seconds
            higher_times = []
            lower_times = []
            
            for j, future_record in enumerate(data):
                if i == j:  # Skip same record
                    continue
                    
                future_price = future_record['price']
                future_timestamp = future_record['timestamp_seconds']
                
                # Check if within 20-second window
                time_diff = future_timestamp - base_timestamp
                if 0 < time_diff <= 20.0:
                    if future_price > base_price:
                        higher_times.append(time_diff)
                    elif future_price < base_price:
                        lower_times.append(time_diff)
            
            # Find shortest windows
            higher_window = min(higher_times) if higher_times else 20.0
            lower_window = min(lower_times) if lower_times else 20.0
            
            # Create results
            timestamp_iso = base_time.isoformat() + 'Z' if base_time else None
            
            higher_results.append({
                "timestamp": timestamp_iso,
                "higher_window": float(higher_window)
            })
            
            lower_results.append({
                "timestamp": timestamp_iso,
                "lower_window": float(lower_window)
            })
        
        # Convert to DataFrames and write to Kafka if we have results
        if higher_results:
            # Create DataFrame for higher results
            higher_schema = StructType() \
                .add("timestamp", StringType()) \
                .add("higher_window", FloatType())
            
            higher_df = batch_df.sparkSession.createDataFrame(higher_results, higher_schema)
            higher_json_df = higher_df.select(
                to_json(struct(col("timestamp"), col("higher_window"))).alias("value")
            )
            
            # Write to Kafka
            higher_json_df.write \
                .format("kafka") \
                .option("kafka.bootstrap.servers", os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')) \
                .option("topic", "btc-price-higher") \
                .save()
            
            print(f"✅ Published {len(higher_results)} higher window records")
        
        if lower_results:
            # Create DataFrame for lower results
            lower_schema = StructType() \
                .add("timestamp", StringType()) \
                .add("lower_window", FloatType())
            
            lower_df = batch_df.sparkSession.createDataFrame(lower_results, lower_schema)
            lower_json_df = lower_df.select(
                to_json(struct(col("timestamp"), col("lower_window"))).alias("value")
            )
            
            # Write to Kafka
            lower_json_df.write \
                .format("kafka") \
                .option("kafka.bootstrap.servers", os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')) \
                .option("topic", "btc-price-lower") \
                .save()
            
            print(f"✅ Published {len(lower_results)} lower window records")
    
    return process_batch


def main():
    """Main function to run the shortest windows analysis"""
    
    # Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    print("🚀 Starting BTC Shortest Windows Analysis...")
    print(f"📡 Kafka Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"📊 Input Topic: btc-price")
    print(f"📤 Output Topics: btc-price-higher, btc-price-lower")
    print(f"⏱️  Window Size: 20 seconds")
    print(f"🕐 Late Data Tolerance: 10 seconds")
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Create input stream
        input_stream = create_input_stream(spark, KAFKA_BOOTSTRAP_SERVERS)
        
        # Debug: Print schema
        print("📋 Input Stream Schema:")
        input_stream.printSchema()
        
        # Process using foreachBatch
        print("⚙️  Setting up window analysis...")
        process_batch_func = find_windows_with_foreachbatch(input_stream)
        
        # Start the streaming query
        query = (
            input_stream.writeStream
            .foreachBatch(process_batch_func)
            .outputMode("append")
            .trigger(processingTime="5 seconds")
            .option("checkpointLocation", "/app/checkpoints/bonus_windows/main")
            .start()
        )
        
        print("✅ Stream started successfully!")
        print("📊 Processing Bitcoin price windows...")
        print("🔄 Press Ctrl+C to stop")
        
        # Wait for termination
        query.awaitTermination()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping streams...")
        spark.streams.active.foreach(lambda stream: stream.stop())
        print("✅ Streams stopped successfully!")
        
    except Exception as e:
        print(f"❌ Error in streaming: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        spark.stop()
        print("🏁 Spark session stopped")


if __name__ == "__main__":
    main()
