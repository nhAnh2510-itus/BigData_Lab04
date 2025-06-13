#!/bin/bash

echo "🐳 BigData Lab04 - Docker Setup"
echo "================================"

# Kiểm tra Docker có cài đặt không
if ! command -v docker &> /dev/null; then
    echo "❌ Docker chưa được cài đặt. Hãy cài đặt Docker trước."
    echo "💡 Hướng dẫn cài đặt: https://docs.docker.com/get-docker/"
    exit 1
fi

# Kiểm tra Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose chưa được cài đặt."
    exit 1
fi

echo "✅ Docker version: $(docker --version)"
echo "✅ Docker Compose version: $(docker compose version)"

echo ""
echo "🔨 Building Python app image..."
docker compose build python-app

echo ""
echo "🚀 Khởi động infrastructure (Kafka + MongoDB + Spark)..."

# Khởi động tất cả services cần thiết
docker compose up -d zookeeper kafka kafka-ui mongodb spark-master spark-worker

echo ""
echo "⏳ Đợi services khởi động hoàn tất..."
echo "   - Zookeeper: Khởi động..."
echo "   - Kafka: Khởi động..."
echo "   - MongoDB: Khởi động..."
echo "   - Spark Master: Khởi động..."
echo "   - Spark Worker: Khởi động..."

# Đợi Kafka khởi động
sleep 10

echo ""
echo "🗄️ Kiểm tra MongoDB..."
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null || echo "⚠️  MongoDB đang khởi động..."

echo ""
echo "📋 Tạo Kafka topics..."
docker compose exec kafka kafka-topics --create --topic btc-price --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic btc-price đã tồn tại"
docker compose exec kafka kafka-topics --create --topic btc-price-moving --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic btc-price-moving đã tồn tại"
docker compose exec kafka kafka-topics --create --topic btc-price-zscore --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic btc-price-zscore đã tồn tại"

echo ""
echo "🔍 Kiểm tra topics:"
docker compose exec kafka kafka-topics --list --bootstrap-server kafka:29092

echo ""
echo "✅ Infrastructure đã sẵn sàng!"
echo ""
echo "📖 Web UI có sẵn:"
echo "   🌐 Kafka UI: http://localhost:8083"
echo "   ⚡ Spark Master UI: http://localhost:8081"
echo "   👷 Spark Worker UI: http://localhost:8082"
echo ""
echo "📡 Services:"
echo "   📤 Kafka Server: localhost:9092" 
echo "   🗄️  MongoDB: localhost:27017 (admin/password123)"
echo "   ⚡ Spark Master: localhost:7077"
echo ""
echo "🚀 Để chạy Python app:"
echo "   ./run-python-app.sh"
echo ""
echo "🔧 Các lệnh hữu ích:"
echo "   📊 Xem containers: docker compose ps"
echo "   📜 Xem logs Kafka: docker compose logs -f kafka"
echo "   📜 Xem logs Spark: docker compose logs -f spark-master"
echo "   💬 Monitor messages: docker exec kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic btc-price --from-beginning"
echo "   🗄️  MongoDB shell: docker exec -it mongodb mongosh bigdata_lab04"
echo "   - Dừng services: docker compose down"
echo "   - Restart: docker compose restart"
