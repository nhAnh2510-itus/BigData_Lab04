#!/bin/bash

echo "🐍 BigData Lab04 - Python ETL Pipeline"
echo "======================================="

# Kiểm tra infrastructure có chạy không
echo "🔍 Kiểm tra infrastructure..."
if ! docker compose ps | grep -q "kafka.*Up"; then
    echo "❌ Kafka chưa chạy. Hãy khởi động infrastructure trước:"
    echo "   ./start-docker.sh"
    exit 1
fi

if ! docker compose ps | grep -q "mongodb.*Up"; then
    echo "❌ MongoDB chưa chạy. Hãy khởi động infrastructure trước:"
    echo "   ./start-docker.sh"
    exit 1
fi

echo "✅ Infrastructure đã sẵn sàng"

echo ""
echo "📋 ETL Pipeline Components:"
echo "1. 📥 Extract - Thu thập giá Bitcoin từ Binance API"
echo "2. ⚙️  Transform Moving Stats - Tính moving averages & std"
echo "3. ⚙️  Transform Z-Score - Phát hiện anomaly"
echo "4. 📤 Load - Lưu dữ liệu vào MongoDB"
echo "5. 🎯 Bonus - Phân tích trend ngắn hạn"
echo "6. 🔧 Interactive Shell"
echo "7. 🚀 Full Pipeline (chạy tất cả)"
echo "8. 📊 Monitor Topics"
echo "9. 🗄️  MongoDB Shell"

echo ""
read -p "💡 Chọn component để chạy (1-9): " choice

case $choice in
    1)
        echo "🚀 Chạy Extract - Thu thập dữ liệu Bitcoin..."
        echo "⚡ Đang gửi giá Bitcoin vào Kafka topic 'btc-price'"
        echo "🔄 Nhấn Ctrl+C để dừng"
        docker compose run --rm -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/extract.py
        ;;
    2)
        echo "🚀 Chạy Transform Moving Stats..."
        echo "📊 Xử lý dữ liệu từ 'btc-price' → 'btc-price-moving'"
        echo "🔄 Nhấn Ctrl+C để dừng"
        docker compose run --rm -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/transform_moving_stats.py
        ;;
    3)
        echo "🚀 Chạy Transform Z-Score..."
        echo "🎯 Phát hiện anomaly từ 'btc-price' → 'btc-price-zscore'"
        echo "🔄 Nhấn Ctrl+C để dừng"
        docker compose run --rm -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/transform_zscore.py
        ;;
    4)
        echo "🚀 Chạy Load - Lưu vào MongoDB..."
        echo "💾 Lưu dữ liệu từ Kafka topics vào MongoDB"
        echo "🔄 Nhấn Ctrl+C để dừng"
        docker compose run --rm -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/load.py
        ;;
    5)
        echo "🚀 Chạy Bonus - Phân tích trend..."
        echo "📈 Tìm trend tăng/giảm ngắn hạn"
        echo "🔄 Nhấn Ctrl+C để dừng"
        docker compose run --rm -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/bonus.py
        ;;
    6)
        echo "🚀 Mở Interactive Shell..."
        echo "💻 Môi trường Python với tất cả dependencies"
        docker compose run --rm -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app bash
        ;;
    7)
        echo "🚀 Chạy Full ETL Pipeline..."
        echo "📋 Khởi động tất cả components theo thứ tự"
        echo ""
        
        # Chạy Extract trong background
        echo "1️⃣  Khởi động Extract (Background)..."
        docker compose run --rm -d --name extract-service -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/extract.py
        
        # Đợi data có sẵn
        echo "⏳ Đợi dữ liệu khởi tạo (10s)..."
        sleep 10
        
        # Chạy Transform Moving Stats
        echo "2️⃣  Khởi động Transform Moving Stats (Background)..."
        docker compose run --rm -d --name transform-moving-service -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/transform_moving_stats.py
        
        # Chạy Transform Z-Score  
        echo "3️⃣  Khởi động Transform Z-Score (Background)..."
        docker compose run --rm -d --name transform-zscore-service -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/transform_zscore.py
        
        # Chạy Bonus Analysis
        echo "4️⃣  Khởi động Bonus Windows Analysis (Background)..."
        docker compose run --rm -d --name bonus-service -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/bonus.py
        
        # Đợi transform data có sẵn
        echo "⏳ Đợi transform data (5s)..."
        sleep 5
        
        # Chạy Load
        echo "5️⃣  Khởi động Load (Background)..."
        docker compose run --rm -d --name load-service -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 python-app python src/load.py
        
        echo ""
        echo "✅ Full ETL Pipeline đã khởi động!"
        echo "📊 Theo dõi:"
        echo "   🌐 Kafka UI: http://localhost:8080"
        echo "   ⚡ Spark UI: http://localhost:8081"
        echo "   🗄️  MongoDB: mongodb://admin:password123@localhost:27017"
        echo ""
        echo "🔧 Quản lý:"
        echo "   📜 Xem logs: docker logs <service-name>"
        echo "   🛑 Dừng service: docker stop <service-name>"
        echo "   🛑 Dừng tất cả: ./stop-docker.sh"
        echo ""
        echo "🏃 Services đang chạy:"
        echo "   - extract-service"
        echo "   - transform-moving-service" 
        echo "   - transform-zscore-service"
        echo "   - bonus-service"
        echo "   - load-service"
        ;;
    8)
        echo "📊 Monitor Kafka Topics..."
        echo "Chọn topic để theo dõi:"
        echo "1) btc-price (raw data)"
        echo "2) btc-price-moving (moving stats)"
        echo "3) btc-price-zscore (z-score analysis)"
        echo "4) btc-price-higher (bonus: higher price windows)"
        echo "5) btc-price-lower (bonus: lower price windows)"
        read -p "Chọn topic (1-5): " topic_choice
        
        case $topic_choice in
            1) TOPIC="btc-price" ;;
            2) TOPIC="btc-price-moving" ;;
            3) TOPIC="btc-price-zscore" ;;
            4) TOPIC="btc-price-higher" ;;
            5) TOPIC="btc-price-lower" ;;
            *) echo "❌ Lựa chọn không hợp lệ"; exit 1 ;;
        esac
        
        echo "📡 Monitoring topic: $TOPIC"
        echo "🔄 Nhấn Ctrl+C để dừng"
        docker exec kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic $TOPIC --from-beginning
        ;;
    9)
        echo "🗄️  Mở MongoDB Shell..."
        docker exec -it mongodb mongosh bigdata_lab04 -u admin -p password123
        ;;
    *)
        echo "❌ Lựa chọn không hợp lệ"
        exit 1
        ;;
esac
