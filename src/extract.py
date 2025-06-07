
import requests
import json
from kafka import KafkaProducer
from datetime import datetime
import time

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def get_price():
    url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
    response = requests.get(url)
    #data = response.json()

    data = response.json()
    data['price'] = float(data['price'])  # ép về float cho đúng schema

    timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
    data['event_time'] = timestamp
    return data

while True:
    try:
        price_data = get_price()
        producer.send('btc-price', value=price_data)
        print("Sent:", price_data)
    except Exception as e:
        print("Error:", e)
    time.sleep(0.1)  # 100ms
