# BigData Lab04 - Spark Streaming Pipeline

Dự án này thực hiện một pipeline ETL (Extract-Transform-Load) hoàn chỉnh để phân tích streaming data về giá Bitcoin (BTCUSDT) từ API Binance sử dụng Apache Kafka và Apache Spark.

## 🎯 Tổng quan

Dự án bao gồm 3 giai đoạn chính:

1. **Extract**: Thu thập dữ liệu giá Bitcoin từ Binance API và đẩy vào Kafka
2. **Transform**: Xử lý dữ liệu với 2 phương pháp:
   - Moving Statistics (Thống kê di động)
   - Z-Score Analysis (Phân tích Z-Score)
3. **Load**: Lưu trữ kết quả đã xử lý

## 🛠 Yêu cầu hệ thống

- **Docker** và **Docker Compose**
- **Python 3.8+**
- **Java 8 hoặc 11** (cho Spark)
- **Ít nhất 4GB RAM** cho các container

## 📦 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/nhAnh2510-itus/BigData_Lab04.git
cd BigData_Lab04
```

### 2. Thiết lập môi trường Python

```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cấp quyền thực thi cho scripts

```bash
chmod +x start.sh
chmod +x start-docker.sh
chmod +x stop-docker.sh
chmod +x run-python-app.sh
```

## 📁 Cấu trúc dự án

```
BigData_Lab04/
├── src/                          # Mã nguồn chính
│   ├── extract.py               # Producer Kafka - thu thập dữ liệu
│   ├── transform_moving_stats.py # Transform với moving statistics
│   ├── transform_zscore.py      # Transform với Z-score
│   ├── load.py                  # Consumer Kafka - lưu trữ dữ liệu
│   └── bonus.py                 # Bonus: Phân tích chuyển động giá
├── docs/                        # Tài liệu và báo cáo
├── docker-compose.yml           # Cấu hình Docker services
├── Dockerfile                   # Docker image cho Python app
├── requirements.txt             # Python dependencies
├── start.sh                     # Script chạy ứng dụng Python
├── start-docker.sh             # Script khởi động Docker
├── stop-docker.sh              # Script dừng Docker
├── run-python-app.sh           # Script chạy container Python
└── setup-mongodb.sh            # Script thiết lập MongoDB
```

## 🚀 Hướng dẫn chạy

### Phương pháp 1: Sử dụng Docker (Khuyến nghị)

#### Bước 1: Khởi động infrastructure

```bash
# Khởi động Kafka, Zookeeper và Kafka UI
./start-docker.sh
```

Đợi khoảng 30-60 giây để các services khởi động hoàn toàn.

#### Bước 2: Kiểm tra services

- **Kafka UI**: http://localhost:8080
- **MongoDB**: mongodb://admin:password123@localhost:27017
- **Zookeeper**: localhost:2181
- **Kafka**: localhost:9092

#### Bước 3: Setup MongoDB (chỉ cần chạy 1 lần)

```bash
./setup-mongodb.sh
```

#### Bước 4: Chạy các components

**Cách 1: Sử dụng script tương tác**
```bash
# Terminal 1: Extract
./run-python-app.sh  # Chọn 1

# Terminal 2: Transform Moving Stats  
./run-python-app.sh  # Chọn 2
```

**Cách 2: Chạy trực tiếp**
```bash
# Extract
docker-compose exec python-app python src/extract.py

# Transform Moving Stats
docker-compose exec python-app python src/transform_moving_stats.py

# Transform Z-Score  
docker-compose exec python-app python src/transform_zscore.py

# Load
docker-compose exec python-app python src/load.py

# Bonus
docker-compose exec python-app python src/bonus.py
```

#### Bước 6: Dừng services

```bash
./stop-docker.sh
```

### Phương pháp 2: Chạy local (Cần Kafka đã cài sẵn)

```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Chạy script với menu tương tác
./start.sh
```

### Phương pháp 3: Chạy từng component riêng biệt

#### Extract (Producer)
```bash
python src/extract.py
```

#### Transform - Moving Statistics
```bash
python src/transform_moving_stats.py
```

#### Transform - Z-Score
```bash
python src/transform_zscore.py
```

#### Load (Consumer)
```bash
python src/load.py
```

## 🔧 Giải thích các thành phần

### Extract (src/extract.py)
- Thu thập dữ liệu giá Bitcoin từ Binance API
- Gửi dữ liệu vào Kafka topic `bitcoin-prices`
- Chạy liên tục với interval 5 giây

### Transform Moving Statistics (src/transform_moving_stats.py)
- Đọc dữ liệu từ topic `bitcoin-prices`
- Tính toán moving average và moving standard deviation
- Gửi kết quả vào topic `bitcoin-moving-stats`

### Transform Z-Score (src/transform_zscore.py)
- Đọc dữ liệu từ topic `bitcoin-prices`
- Tính toán Z-score để phát hiện anomaly
- Gửi kết quả vào topic `bitcoin-zscore`

### Load (src/load.py)
- Consumer dữ liệu từ topic `btc-price-zscore`
- Lưu trữ vào MongoDB collections theo từng window
- Collections: `btc-price-zscore-30s`, `btc-price-zscore-1m`, etc.

### Bonus (src/bonus.py)
- Đọc dữ liệu từ topic `btc-price`
- Tìm khoảng thời gian ngắn nhất giá tăng/giảm trong 20 giây
- Gửi kết quả vào topics `btc-price-higher` và `btc-price-lower`

## 📊 Monitoring

### Kafka UI
Truy cập http://localhost:8080 để:
- Xem các topics: `btc-price`, `btc-price-moving`, `btc-price-zscore`, `btc-price-higher`, `btc-price-lower`
- Monitor messages
- Kiểm tra consumer groups
- Xem cluster health

### MongoDB
```bash
# Kết nối MongoDB
docker exec -it mongodb mongosh bigdata_lab04

# Xem collections
show collections

# Xem dữ liệu
db['btc-price-zscore-30s'].find().limit(5)
```

## 📝 Notes

- Dự án chỉ dành cho mục đích giáo dục
- Không khuyến khích giao dịch tiền điện tử thực
- Binance API có rate limit, cần chú ý khi test
- Đảm bảo kết nối internet ổn định cho API calls

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.