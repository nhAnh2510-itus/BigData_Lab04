#!/bin/bash

# Script khởi động BigData Lab04
echo "🚀 Khởi động BigData Lab04..."

# Kích hoạt môi trường ảo
source venv/bin/activate

echo "✅ Môi trường ảo đã được kích hoạt"
echo "📦 Python version: $(python --version)"

# Hiển thị các tùy chọn
echo ""
echo "🔧 Chọn chương trình để chạy:"
echo "1. Extract - Thu thập dữ liệu Bitcoin (extract.py)"
echo "2. Transform Moving Stats - Tính toán thống kê di động (transform_moving_stats.py)"
echo "3. Transform Z-Score - Tính toán Z-Score (transform_zscore.py)"
echo "4. Load - Tải dữ liệu vào MongoDB (load.py)"
echo "5. Bonus - Phân tích chuyển động giá (bonus.py)"
echo ""

read -p "Nhập số (1-5): " choice

case $choice in
    1)
        echo "🟢 Chạy Extract script..."
        python src/extract.py
        ;;
    2)
        echo "🟡 Chạy Transform Moving Stats script..."
        python src/transform_moving_stats.py
        ;;
    3)
        echo "🟠 Chạy Transform Z-Score script..."
        python src/transform_zscore.py
        ;;
    4)
        echo "🔵 Chạy Load script..."
        python src/load.py
        ;;
    5)
        echo "🎯 Chạy Bonus script..."
        python src/bonus.py
        ;;
    *)
        echo "❌ Lựa chọn không hợp lệ!"
        ;;
esac
