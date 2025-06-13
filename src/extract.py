
import requests
import json
import os
from kafka import KafkaProducer
from datetime import datetime, timezone
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global producer variable
producer = None

def get_kafka_producer():
    """Tạo và trả về Kafka producer với config được lấy từ environment variables"""
    global producer
    if producer is None:
        # Lấy Kafka bootstrap servers từ environment variable hoặc dùng localhost
        kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        logger.info(f"Connecting to Kafka at: {kafka_servers}")
        
        # Kafka producer với optimized configs
        producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            batch_size=16384,  # Integer, not string
            linger_ms=5,       # Integer, not string
            compression_type='gzip',  # Use gzip instead of snappy (more widely available)
            buffer_memory=33554432,  # Integer, not string
            retries=3,         # Integer, not string
            acks=1             # Integer 1, not string '1'
        )
    return producer

# Shared variables
latest_price = None
price_lock = threading.Lock()
price_queue = Queue(maxsize=100)  # Buffer for price data

def get_price():
    """Fetch price from Binance API"""
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
        response = requests.get(url, timeout=2)  # 2s timeout
        data = response.json()
        data['price'] = float(data['price'])  # ép về float cho đúng schema
        return data
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        return None

def price_fetcher():
    """Background thread để fetch price liên tục"""
    global latest_price
    while True:
        try:
            price_data = get_price()
            if price_data:
                with price_lock:
                    latest_price = price_data
                # Đưa vào queue để buffer
                if not price_queue.full():
                    price_queue.put(price_data)
        except Exception as e:
            logger.error(f"Price fetcher error: {e}")
        time.sleep(0.05)  # Fetch mỗi 50ms để có dữ liệu fresh

def create_message_with_timestamp(price_data):
    """Tạo message với timestamp chính xác"""
    if price_data is None:
        return None
    
    # Copy data để không modify original
    data = price_data.copy()
    
    # Lấy timestamp hiện tại và làm tròn theo yêu cầu Lab
    now = datetime.now(timezone.utc)
    # Làm tròn milliseconds xuống thành s.s00 (tức là bỏ phần cuối 2 chữ số)
    rounded_ms = (now.microsecond // 100000) * 100  # Làm tròn xuống 100ms
    rounded_time = now.replace(microsecond=rounded_ms * 1000)
    
    # Format theo ISO8601 như yêu cầu
    timestamp = rounded_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    data['event_time'] = timestamp
    return data

def message_sender():
    """Main thread để send message mỗi 100ms chính xác"""
    message_count = 0
    start_time = time.time()
    
    while True:
        try:
            # Lấy dữ liệu price mới nhất
            current_price = None
            
            # Ưu tiên lấy từ queue (fresher data)
            if not price_queue.empty():
                current_price = price_queue.get_nowait()
            else:
                # Fallback to latest_price nếu queue empty
                with price_lock:
                    current_price = latest_price
            
            if current_price:
                # Tạo message với timestamp hiện tại
                message = create_message_with_timestamp(current_price)
                if message:
                    get_kafka_producer().send('btc-price', value=message)
                    message_count += 1
                    
                    if message_count % 50 == 0:  # Log mỗi 5 giây
                        elapsed = time.time() - start_time
                        rate = message_count / elapsed
                        logger.info(f"Sent {message_count} messages, rate: {rate:.2f} msg/s")
                        print("Latest sent:", message)
            else:
                logger.warning("No price data available, sending dummy message")
                # Send dummy message để maintain rate
                dummy_message = {
                    "symbol": "BTCUSDT",
                    "price": 0.0,
                    "event_time": datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
                }
                get_kafka_producer().send('btc-price', value=dummy_message)
                
        except Exception as e:
            logger.error(f"Message sender error: {e}")
        
        # Sleep để maintain 100ms interval chính xác
        time.sleep(0.1)

# Main execution
if __name__ == "__main__":
    logger.info("Starting BTC Price Extractor with parallel processing...")
    
    # Start background price fetcher thread
    price_thread = threading.Thread(target=price_fetcher, daemon=True)
    price_thread.start()
    
    # Wait a bit for initial price data
    time.sleep(1)
    
    try:
        # Start main message sender loop
        message_sender()
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping price extractor...")
        get_kafka_producer().flush()  # Ensure all messages are sent
        get_kafka_producer().close()
