#!/bin/bash

echo "🐳 BigData Lab04 - Docker Setup"
echo "================================"

# Kiểm tra Docker có cài đặt không
if ! command -v docker &> /dev/null; then
    echo "❌ Docker chưa được cài đặt. Hãy cài đặt Docker trước."
    echo "💡 Hướng dẫn cài đặt: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker version: $(docker --version)"
echo "✅ Docker Compose version: $(docker compose version)"

echo ""
echo "🚀 Khởi động infrastructure (Kafka + MongoDB)..."

# Khởi động Zookeeper, Kafka, Kafka UI và MongoDB
docker compose up -d zookeeper kafka kafka-ui mongodb

echo ""
echo "⏳ Đợi services khởi động hoàn tất..."
sleep 30

echo ""
echo "🗄️ Kiểm tra MongoDB..."
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet

echo ""
echo "📋 Tạo topic btc-price..."
docker compose exec kafka kafka-topics --create --topic btc-price --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic đã tồn tại"

echo ""
echo "🔍 Kiểm tra topics:"
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

echo ""
echo "✅ Infrastructure đã sẵn sàng!"
echo ""
echo "📖 Hướng dẫn sử dụng:"
echo "1. Kafka UI: http://localhost:8080"
echo "2. Kafka Server: localhost:9092" 
echo "3. MongoDB: localhost:27017"
echo "4. Chạy Python app: ./run-python-app.sh"
echo ""
echo "🔧 Các lệnh hữu ích:"
echo "   - Xem messages: docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic btc-price --from-beginning"
echo "   - MongoDB shell: docker exec -it mongodb mongosh bigdata_lab04"
echo "   - Xem logs Kafka: docker compose logs -f kafka"
echo "   - Xem logs MongoDB: docker compose logs -f mongodb"
echo "   - Dừng services: docker compose down"
echo "   - Restart: docker compose restart"
