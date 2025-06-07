#!/bin/bash

echo "🛑 Dừng tất cả Docker containers cho BigData Lab04"
echo "================================================="

# Dừng tất cả containers
docker compose down

# Xóa volumes nếu muốn reset hoàn toàn
read -p "Bạn có muốn xóa volumes (reset dữ liệu)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Xóa volumes..."
    docker compose down -v
    echo "✅ Đã reset dữ liệu"
fi

echo "✅ Đã dừng tất cả services"

# Hiển thị trạng thái
echo ""
echo "📊 Trạng thái containers:"
docker compose ps
