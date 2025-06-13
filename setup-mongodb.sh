#!/bin/bash

echo "🗄️  BigData Lab04 - MongoDB Setup"
echo "================================="

# Kiểm tra MongoDB đã chạy chưa
if ! docker compose ps | grep -q "mongodb.*Up"; then
    echo "❌ MongoDB container chưa chạy. Hãy khởi động Docker services trước:"
    echo "   ./start-docker.sh"
    exit 1
fi

echo "✅ MongoDB container đang chạy"

echo ""
echo "📊 Thiết lập database và collections..."

# Kiểm tra kết nối MongoDB
echo "🔍 Kiểm tra kết nối MongoDB..."
if ! docker compose exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
    echo "❌ Không thể kết nối MongoDB. Đợi thêm vài giây..."
    sleep 5
fi

# Connect to MongoDB và tạo database + collections
echo "🗃️  Tạo database 'bigdata_lab04'..."
echo "📋 Tạo collections cho các time windows..."

docker compose exec mongodb mongosh --eval "
use bigdata_lab04;

// Tạo collections cho moving statistics
db.createCollection('btc-price-moving-30s');
db.createCollection('btc-price-moving-1m');
db.createCollection('btc-price-moving-5m');
db.createCollection('btc-price-moving-15m');
db.createCollection('btc-price-moving-30m');
db.createCollection('btc-price-moving-1h');

// Tạo collections cho z-score analysis
db.createCollection('btc-price-zscore-30s');
db.createCollection('btc-price-zscore-1m');
db.createCollection('btc-price-zscore-5m');
db.createCollection('btc-price-zscore-15m');
db.createCollection('btc-price-zscore-30m');
db.createCollection('btc-price-zscore-1h');

// Tạo collections cho bonus analysis
db.createCollection('btc-price-higher');
db.createCollection('btc-price-lower');

print('✅ Đã tạo collections cho moving statistics');
print('✅ Đã tạo collections cho z-score analysis');
print('✅ Đã tạo collections cho bonus analysis');
"

echo ""
echo "🔍 Tạo indexes để tối ưu performance..."

docker compose exec mongodb mongosh bigdata_lab04 --eval "
// Tạo indexes cho timestamp fields
db['btc-price-moving-30s'].createIndex({window_start: 1, window_end: 1});
db['btc-price-moving-1m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-moving-5m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-moving-15m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-moving-30m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-moving-1h'].createIndex({window_start: 1, window_end: 1});

db['btc-price-zscore-30s'].createIndex({window_start: 1, window_end: 1});
db['btc-price-zscore-1m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-zscore-5m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-zscore-15m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-zscore-30m'].createIndex({window_start: 1, window_end: 1});
db['btc-price-zscore-1h'].createIndex({window_start: 1, window_end: 1});

db['btc-price-higher'].createIndex({timestamp: 1});
db['btc-price-lower'].createIndex({timestamp: 1});

print('✅ Đã tạo indexes cho performance');
"

echo ""
echo "📋 Hiển thị collections đã tạo:"
docker compose exec mongodb mongosh bigdata_lab04 --eval "db.listCollections().forEach(c => print('📁 ' + c.name))" --quiet

echo ""
echo "✅ MongoDB setup hoàn tất!"
echo ""
echo "💡 Hướng dẫn sử dụng:"
echo "   🔍 Kết nối: mongodb://admin:password123@localhost:27017/bigdata_lab04"
echo "   💻 MongoDB Shell: docker exec -it mongodb mongosh bigdata_lab04 -u admin -p password123"
echo "   📊 Xem dữ liệu: db['btc-price-moving-1m'].find().limit(5)"
db['btc-price-zscore-1m'].createIndex({timestamp: 1});
db['btc-price-zscore-5m'].createIndex({timestamp: 1});
db['btc-price-zscore-15m'].createIndex({timestamp: 1});
db['btc-price-zscore-30m'].createIndex({timestamp: 1});
db['btc-price-zscore-1h'].createIndex({timestamp: 1});

print('✅ Database và collections đã được tạo thành công');
print('📋 Collections:');
db.getCollectionNames().forEach(name => print('  - ' + name));
"

echo "🎉 MongoDB setup hoàn tất!"
echo "🌐 MongoDB UI: http://localhost:27017"
echo "💻 Kết nối: mongodb://admin:password123@localhost:27017/bigdata_lab04"
