
import requests
import json
import os
from kafka import KafkaProducer
from datetime import datetime, timezone
import time
import threading
from queue import Queue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

producer = None

def get_kafka_producer(): #Để đảm bảo luôn kết nối đến Kafka producer duy nhất
    global producer
    if producer is None:
        kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        logger.info(f"Connecting to Kafka at: {kafka_servers}")

        producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            batch_size=16384,  
            linger_ms=5,    
            compression_type='gzip',
            buffer_memory=33554432,  
            retries=3,       
            acks=1       
        )
    return producer

latest_price = None
price_lock = threading.Lock()
price_queue = Queue(maxsize=1) 

def get_price(): # Lấy giá từ API
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
        response = requests.get(url, timeout=2)
        data = response.json()
        data['price'] = float(data['price'])
        return data
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        return None

def price_fetcher():
    global latest_price
    while True:
        try:
            price_data = get_price()
            if price_data:
                with price_lock:
                    latest_price = price_data
                
                if not price_queue.empty():
                    price_queue.get_nowait() 
                price_queue.put_nowait(price_data)  
                        
        except Exception as e:
            logger.error(f"Price fetcher error: {e}")
        time.sleep(0.05)

def create_message_with_timestamp(price_data):
    if price_data is None:
        return None

    data = price_data.copy()

    now = datetime.now(timezone.utc)
    rounded_ms = (now.microsecond // 100000) * 100 
    rounded_time = now.replace(microsecond=rounded_ms * 1000)

    timestamp = rounded_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    data['event_time'] = timestamp
    return data

def message_sender():    
    while True:
        try:
            current_price = None

            if not price_queue.empty():
                current_price = price_queue.get_nowait()
            else:
                with price_lock:
                    current_price = latest_price
            
            if current_price:
                message = create_message_with_timestamp(current_price)
                if message:
                    get_kafka_producer().send('btc-price', value=message)

            else:
                dummy_message = {
                    "symbol": "BTCUSDT",
                    "price": 0.0,
                    "event_time": datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
                }
                get_kafka_producer().send('btc-price', value=dummy_message)
                
        except Exception as e:
            logger.error(f"Message sender error: {e}")
        
        time.sleep(0.1) 

# Main execution
if __name__ == "__main__":
    logger.info("Starting BTC Price Extractor with parallel processing...")

    #Tạo một thread để fetch price liên tục
    price_thread = threading.Thread(target=price_fetcher, daemon=True)
    price_thread.start()

    time.sleep(1) # Chờ price_thread
    
    try:
        message_sender() # Vòng lặp gửi data
    except KeyboardInterrupt:
        logger.info("Stopping BTC Price Extractor...")
        get_kafka_producer().flush() 
        get_kafka_producer().close()
