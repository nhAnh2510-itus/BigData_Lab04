#!/bin/bash

echo "🛑 BigData Lab04 - Dừng Docker Services"
echo "======================================="

echo "🔍 Kiểm tra containers đang chạy..."
docker compose ps

echo ""
echo "🛑 Dừng tất cả Python ETL services..."
# Dừng các Python services đang chạy
docker stop extract-service transform-moving-service transform-zscore-service load-service 2>/dev/null || true
docker rm extract-service transform-moving-service transform-zscore-service load-service 2>/dev/null || true

echo "🛑 Dừng Docker Compose services..."
# Dừng tất cả containers trong docker-compose
docker compose down

echo ""
echo "🗑️  Tùy chọn dọn dẹp:"
echo "1. 🔄 Giữ dữ liệu (restart nhanh)"
echo "2. 🗑️  Xóa volumes (reset hoàn toàn)"
echo "3. 🧹 Dọn dẹp images không dùng"

read -p "Chọn tùy chọn (1-3, Enter để bỏ qua): " cleanup_choice

case $cleanup_choice in
    2)
        echo "🗑️  Xóa volumes và reset dữ liệu..."
        docker compose down -v
        echo "✅ Đã reset tất cả dữ liệu"
        ;;
    3)
        echo "🧹 Dọn dẹp Docker images không dùng..."
        docker system prune -f
        echo "✅ Đã dọn dẹp Docker system"
        ;;
    *)
        echo "✅ Giữ nguyên dữ liệu"
        ;;
esac

echo ""
echo "✅ Đã dừng tất cả services!"

# Hiển thị trạng thái cuối
echo ""
echo "📊 Trạng thái cuối:"
docker compose ps

echo ""
echo "🚀 Để khởi động lại:"
echo "   ./start-docker.sh"
