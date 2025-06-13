# 🚀 Quick Start Guide

## Khởi động nhanh (5 phút)

### 1. Khởi động infrastructure
```bash
./start-docker.sh
```
⏳ Đợi ~2 phút để tất cả services khởi động

### 2. Chạy Full ETL Pipeline
```bash
./run-python-app.sh
# Chọn: 7 (Full Pipeline)
```

### 3. Theo dõi kết quả
- **Kafka UI**: http://localhost:8083
- **Spark UI**: http://localhost:8080

### 4. Kiểm tra dữ liệu
```bash
./run-python-app.sh
# Chọn: 9 (MongoDB Shell)

# Trong MongoDB shell:
db['btc-price-moving-1m'].find().limit(3).pretty()
```

### 5. Dừng hệ thống
```bash
./stop-docker.sh
```

## 🔧 Debug Commands

```bash
# Xem trạng thái containers
docker compose ps

# Xem logs
docker compose logs -f kafka
docker logs extract-service

# Monitor Kafka topics
./run-python-app.sh # → Option 8

# Test PySpark
docker compose run --rm python-app python -c "from pyspark.sql import SparkSession; print('OK')"
```

## 🆘 Troubleshooting

**Problem**: Containers không khởi động
```bash
./stop-docker.sh  # Option 2: Reset volumes
./start-docker.sh
```

**Problem**: Kafka connection failed
```bash
docker compose restart kafka
sleep 30
```

**Problem**: PySpark jobs failing
```bash
# Check Spark UI: http://localhost:8081
docker compose logs -f spark-master
```
