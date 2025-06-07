# 🐳 Hướng dẫn sử dụng Docker cho BigData Lab04

## 📋 Yêu cầu hệ thống
- Docker Engine (phiên bản mới có Docker Compose tích hợp)
- Ít nhất 4GB RAM
- Ít nhất 2GB dung lượng trống

## 🚀 Khởi động nhanh (Quick Start)

### 1. Khởi động Kafka Infrastructure
```bash
./start-docker.sh
```

### 2. Chạy Python Applications
```bash
./run-python-app.sh
```

### 3. Dừng tất cả services
```bash
./stop-docker.sh
```

## 📖 Hướng dẫn chi tiết

### 🔧 **Bước 1: Kiểm tra Docker**
```bash
# Kiểm tra Docker có cài đặt không
docker --version
docker compose version
```

### 🚀 **Bước 2: Khởi động Infrastructure**
```bash
# Khởi động Kafka, Zookeeper và Kafka UI
./start-docker.sh
```

Sau khi chạy, bạn sẽ có:
- ✅ Kafka Server: `localhost:9092`
- ✅ Kafka UI: http://localhost:8080
- ✅ Zookeeper: `localhost:2181`

### 💻 **Bước 3: Chạy Python Apps**
```bash
# Chạy script tương tác
./run-python-app.sh
```

Hoặc chạy từng app riêng lẻ:
```bash
# Extract - Thu thập dữ liệu Bitcoin
docker compose run --rm python-app python src/extract.py

# Transform Moving Stats
docker compose run --rm python-app python src/transform_moving_stats.py

# Transform Z-Score
docker compose run --rm python-app python src/transform_zscore.py

# Load dữ liệu
docker compose run --rm python-app python src/load.py
```

### 🔍 **Monitoring và Debug**

#### Xem logs:
```bash
# Xem logs tất cả services
docker compose logs -f

# Xem logs Kafka
docker compose logs -f kafka

# Xem logs Python app
docker compose logs -f python-app
```

#### Kiểm tra topics:
```bash
# Liệt kê topics
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Xem messages trong topic
docker compose exec kafka kafka-console-consumer --topic btc-price --bootstrap-server localhost:9092 --from-beginning
```

#### Interactive Shell:
```bash
# Vào container Python để debug
docker compose run --rm python-app bash

# Vào container Kafka
docker compose exec kafka bash
```

## 🎛️ **Kafka UI Dashboard**

Truy cập http://localhost:8080 để:
- 📊 Xem real-time messages
- 🔍 Monitor topics và partitions
- 📈 Xem consumer groups
- ⚙️ Quản lý cấu hình

## 🛑 **Dừng và Cleanup**

### Dừng services:
```bash
./stop-docker.sh
```

### Reset hoàn toàn (xóa dữ liệu):
```bash
docker compose down -v --remove-orphans
```

### Xóa images:
```bash
docker compose down --rmi all
```

## 🔧 **Troubleshooting**

### Lỗi port đã sử dụng:
```bash
# Kiểm tra port nào đang sử dụng
sudo netstat -tulpn | grep :9092
sudo netstat -tulpn | grep :8080

# Kill process sử dụng port
sudo kill -9 <PID>
```

### Lỗi memory:
```bash
# Tăng memory cho Docker
# Docker Desktop: Settings > Resources > Advanced > Memory

# Kiểm tra memory usage
docker stats
```

### Reset hoàn toàn:
```bash
# Dừng tất cả
docker compose down -v --remove-orphans

# Xóa tất cả Docker data
docker system prune -a --volumes
```

## 📝 **Pipeline Workflow**

1. **Extract** → Thu thập dữ liệu Bitcoin từ Binance API
2. **Transform** → Xử lý dữ liệu (moving averages, z-scores)
3. **Load** → Lưu vào database/file system

## 🎯 **Production Tips**

### Chạy background:
```bash
# Chạy extract liên tục
docker compose run -d python-app python src/extract.py

# Chạy tất cả pipeline
docker compose up -d
```

### Monitoring:
```bash
# Theo dõi resource usage
docker compose top

# Kiểm tra health
docker compose ps
```
