# 🚀 BigData Lab04 - Real-time Bitcoin ETL Pipeline

Dự án này thực hiện một pipeline ETL (Extract-Transform-Load) hoàn chỉnh để phân tích streaming data về giá Bitcoin (BTCUSDT) từ API Binance sử dụng **Apache Kafka**, **Apache Spark**, và **MongoDB**.

## 🎯 Tổng quan

Pipeline bao gồm 3 giai đoạn chính:

1. **📥 Extract**: Thu thập dữ liệu giá Bitcoin từ Binance API và đẩy vào Kafka
2. **⚙️ Transform**: Xử lý dữ liệu với 2 phương pháp:
   - **Moving Statistics**: Thống kê di động (moving averages, standard deviation)
   - **Z-Score Analysis**: Phân tích Z-Score để phát hiện anomaly
3. **📤 Load**: Lưu trữ kết quả đã xử lý vào MongoDB

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Binance API   │───▶│     Extract     │───▶│   Kafka Topic   │───▶│   Transform     │
│   (BTC Price)   │    │   (Python)      │    │  'btc-price'    │    │   (PySpark)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │                       │
                                                       ▼                       │
                                              ┌─────────────────┐               │
                                              │   Bonus.py      │               │
                                              │ (Window Analysis)│               │
                                              └─────────────────┘               │
                                                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │
│    MongoDB      │◀───│      Load       │◀───│   Kafka Topics  │◀──────────────┘
│   (Results)     │    │   (Python)      │    │'btc-price-*'    │
└─────────────────┘    └─────────────────┘    │'btc-price-higher'│
                                              │'btc-price-lower' │
                                              └─────────────────┘
```

## 🛠 Yêu cầu hệ thống

- **Docker** và **Docker Compose** (v2.0+)
- **Ít nhất 4GB RAM** cho các container
- **Ít nhất 2GB disk space** còn trống
- **Kết nối internet** để download images và data từ Binance

## 📦 Cài đặt và khởi động

### 1. Clone repository và chuẩn bị

```bash
git clone <repository-url>
cd BigData_Lab04

# Đảm bảo các script có quyền execute
chmod +x *.sh
```

### 2. Khởi động infrastructure

```bash
# Khởi động tất cả services (Kafka, MongoDB, Spark)
./start-docker.sh
```

Script này sẽ:
- ✅ Kiểm tra Docker và Docker Compose
- 🔨 Build Python application image
- 🚀 Khởi động Zookeeper, Kafka, MongoDB, Spark
- 📋 Tạo Kafka topics cần thiết
- ⏳ Đợi services sẵn sàng

### 3. Thiết lập MongoDB (tùy chọn)

```bash
# Tạo collections và indexes cho MongoDB
./setup-mongodb.sh
```

### 4. Chạy ETL Pipeline

```bash
# Menu tương tác để chọn component
./run-python-app.sh
```

## 🎮 Cách sử dụng

### 🚀 Quick Start - Full Pipeline

1. Khởi động infrastructure:
   ```bash
   ./start-docker.sh
   ```

2. Chạy Full ETL Pipeline:
   ```bash
   ./run-python-app.sh
   # Chọn option 7: Full Pipeline
   ```

3. Theo dõi qua Web UI:
   - **Kafka UI**: http://localhost:8080
   - **Spark Master**: http://localhost:8081
   - **Spark Worker**: http://localhost:8082

### 📋 Chạy từng component riêng lẻ

#### 1. Extract (Data Ingestion)
```bash
./run-python-app.sh
# Chọn option 1: Extract
```
- Thu thập giá Bitcoin từ Binance API mỗi 100ms
- Gửi vào Kafka topic `btc-price`
- Định dạng JSON với timestamp ISO8601

#### 2. Transform Moving Statistics
```bash
./run-python-app.sh  
# Chọn option 2: Transform Moving Stats
```
- Đọc từ topic `btc-price`
- Tính moving averages và standard deviations
- Multiple time windows: 30s, 1m, 5m, 15m, 30m, 1h
- Gửi kết quả vào topic `btc-price-moving`

#### 3. Transform Z-Score Analysis
```bash
./run-python-app.sh
# Chọn option 3: Transform Z-Score  
```
- Phát hiện anomaly trong giá Bitcoin
- Tính Z-score để identify outliers
- Gửi kết quả vào topic `btc-price-zscore`

#### 4. Load (Data Storage)
```bash
./run-python-app.sh
# Chọn option 4: Load
```
- Lưu dữ liệu từ Kafka vào MongoDB
- Tự động phân chia theo time windows
- Collections: `btc-price-*-30s`, `btc-price-*-1m`, etc.

#### 5. Bonus Analysis (Shortest Windows)
```bash
./run-python-app.sh
# Chọn option 5: Bonus
```
- Phân tích shortest windows của negative outcomes
- Tìm thời gian đến giá cao hơn/thấp hơn trong window 20s
- Gửi kết quả vào topics `btc-price-higher` và `btc-price-lower`
- Late data tolerance: 10 giây

## 📊 Monitoring và Debug

### Web UI Interfaces

| Service | URL | Mô tả |
|---------|-----|-------|
| Kafka UI | http://localhost:8083 | Quản lý Kafka topics, messages |
| Spark Master | http://localhost:8081 | Spark cluster status |
| Spark Worker | http://localhost:8082 | Worker node status |

### Command Line Monitoring

```bash
# Xem messages trong Kafka topic
./run-python-app.sh
# Chọn option 8: Monitor Topics

# Xem logs của services
docker compose logs -f kafka
docker compose logs -f spark-master
docker logs extract-service

# MongoDB shell
./run-python-app.sh  
# Chọn option 9: MongoDB Shell

# Hoặc trực tiếp:
docker exec -it mongodb mongosh bigdata_lab04 -u admin -p password123
```

### Kiểm tra dữ liệu trong MongoDB

```javascript
// Xem moving statistics
db['btc-price-moving-1m'].find().limit(5).pretty()

// Xem z-score analysis  
db['btc-price-zscore-1m'].find().limit(5).pretty()

// Count documents
db['btc-price-moving-1m'].countDocuments()
```

## 🔧 Cấu trúc dự án

```
BigData_Lab04/
├── 📁 src/                          # Mã nguồn Python ETL
│   ├── extract.py                   # Data ingestion từ Binance API
│   ├── transform_moving_stats.py    # PySpark moving statistics
│   ├── transform_zscore.py          # PySpark Z-score analysis  
│   ├── load.py                      # Load data vào MongoDB
│   └── bonus.py                     # Bonus: Trend analysis
├── 📁 docs/                         # Tài liệu và báo cáo
├── 📁 checkpoints/                  # Spark streaming checkpoints
├── 🐳 Dockerfile                    # Python app container
├── 🐳 docker-compose.yml            # Multi-service orchestration
├── 📋 requirements.txt              # Python dependencies  
├── 🚀 start-docker.sh               # Khởi động infrastructure
├── 🐍 run-python-app.sh             # Menu chạy ETL components
├── 🛑 stop-docker.sh                # Dừng tất cả services
├── 🗄️ setup-mongodb.sh              # Thiết lập MongoDB
└── 📖 README.md                     # File này
```

## ⚙️ Cấu hình

### Environment Variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Kafka cluster endpoint |
| `MONGO_HOST` | `mongodb` | MongoDB hostname |
| `MONGO_PORT` | `27017` | MongoDB port |
| `MONGO_DB` | `bigdata_lab04` | Database name |
| `SPARK_MASTER` | `spark://spark-master:7077` | Spark cluster URL |

### Kafka Topics

| Topic | Mô tả | Producer | Consumer |
|-------|-------|----------|----------|
| `btc-price` | Raw Bitcoin price data | extract.py | transform_*.py, bonus.py |
| `btc-price-moving` | Moving statistics results | transform_moving_stats.py | load.py |
| `btc-price-zscore` | Z-score analysis results | transform_zscore.py | load.py |
| `btc-price-higher` | Higher price windows (bonus) | bonus.py | load.py |
| `btc-price-lower` | Lower price windows (bonus) | bonus.py | load.py |

### MongoDB Collections

| Collection | Mô tả | Time Window |
|------------|-------|-------------|
| `btc-price-moving-30s` | Moving stats 30 seconds | 30s |
| `btc-price-moving-1m` | Moving stats 1 minute | 1m |
| `btc-price-zscore-1m` | Z-score 1 minute | 1m |
| `btc-price-higher-windows` | Higher price windows (bonus) | Real-time |
| `btc-price-lower-windows` | Lower price windows (bonus) | Real-time |
| ... | ... | ... |

## 🐛 Troubleshooting

### Vấn đề thường gặp

#### 1. Docker containers không khởi động
```bash
# Kiểm tra trạng thái
docker compose ps

# Xem logs chi tiết
docker compose logs <service-name>

# Restart infrastructure
./stop-docker.sh
./start-docker.sh
```

#### 2. Kafka connection failed
```bash
# Kiểm tra Kafka health
docker compose exec kafka kafka-topics --list --bootstrap-server kafka:29092

# Test connectivity từ Python container
docker compose run --rm python-app python -c "
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['kafka:29092'])
print('✅ Kafka connection OK')
"
```

#### 3. PySpark jobs failing
```bash
# Kiểm tra Spark Master UI
open http://localhost:8081

# Xem Spark logs
docker compose logs -f spark-master
docker compose logs -f spark-worker

# Test PySpark
docker compose run --rm python-app python -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('Test').getOrCreate()
print('✅ PySpark OK')
"
```

#### 4. MongoDB connection issues
```bash
# Test MongoDB connection
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check MongoDB logs
docker compose logs -f mongodb
```

### Reset toàn bộ

```bash
# Dừng và xóa tất cả data
./stop-docker.sh
# Chọn option 2: Xóa volumes

# Khởi động lại từ đầu
./start-docker.sh
./setup-mongodb.sh
```

## 📈 Performance Tuning

### Kafka Configuration
- Tăng `batch_size` trong producer để improve throughput
- Điều chỉnh `linger_ms` để balance latency vs throughput

### Spark Configuration
- Tăng `spark.sql.shuffle.partitions` cho datasets lớn
- Điều chỉnh `spark.driver.memory` và `spark.executor.memory`

### MongoDB Configuration
- Sử dụng indexes phù hợp cho queries
- Xem xét sharding cho volume lớn

## 🚦 Dừng hệ thống

```bash
# Dừng tất cả services
./stop-docker.sh

# Options:
# 1. Giữ dữ liệu (restart nhanh)
# 2. Xóa volumes (reset hoàn toàn) 
# 3. Dọn dẹp Docker images
```

## 📚 Tài liệu tham khảo

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)

## 📝 License

[MIT License](LICENSE)

---

**🎉 Happy Data Engineering!** 

Nếu gặp vấn đề, hãy check logs và sử dụng monitoring tools để debug.
