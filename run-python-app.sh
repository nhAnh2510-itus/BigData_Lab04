#!/bin/bash

echo "🐍 Chạy Python App trong Docker"
echo "==============================="

# Build Python app image nếu chưa có
echo "🔨 Building Python app image..."
docker compose build python-app

echo ""
echo "📋 Các script Python có sẵn:"
echo "1. extract.py - Thu thập dữ liệu Bitcoin"
echo "2. transform_moving_stats.py - Xử lý moving statistics"
echo "3. transform_zscore.py - Tính toán Z-score"
echo "4. load.py - Load dữ liệu"

echo ""
echo "💡 Chọn script để chạy:"
echo "1) Extract (thu thập dữ liệu Bitcoin)"
echo "2) Transform Moving Stats"
echo "3) Transform Z-Score"
echo "4) Load"
echo "5) Interactive shell"
echo "6) Chạy tất cả theo thứ tự"

read -p "Nhập lựa chọn (1-6): " choice

case $choice in
    1)
        echo "🚀 Chạy Extract..."
        docker compose run --rm python-app python src/extract.py
        ;;
    2)
        echo "🚀 Chạy Transform Moving Stats..."
        docker compose run --rm python-app python src/transform_moving_stats.py
        ;;
    3)
        echo "🚀 Chạy Transform Z-Score..."
        docker compose run --rm python-app python src/transform_zscore.py
        ;;
    4)
        echo "🚀 Chạy Load..."
        docker compose run --rm python-app python src/load.py
        ;;
    5)
        echo "🚀 Mở interactive shell..."
        docker compose run --rm python-app bash
        ;;
    6)
        echo "🚀 Chạy tất cả theo pipeline..."
        echo "Step 1: Extract..."
        docker compose run --rm python-app python src/extract.py &
        EXTRACT_PID=$!
        
        sleep 10
        
        echo "Step 2: Transform Moving Stats..."
        docker compose run --rm python-app python src/transform_moving_stats.py &
        
        echo "Step 3: Transform Z-Score..."
        docker compose run --rm python-app python src/transform_zscore.py &
        
        echo "Step 4: Load..."
        docker compose run --rm python-app python src/load.py &
        
        echo "✅ Tất cả services đã được khởi động!"
        echo "⏹️  Nhấn Ctrl+C để dừng"
        wait
        ;;
    *)
        echo "❌ Lựa chọn không hợp lệ"
        exit 1
        ;;
esac
