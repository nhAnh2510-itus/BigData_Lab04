#!/bin/bash

# Script thiết lập MongoDB cho BigData Lab04
echo "🗄️ Thiết lập MongoDB cho BigData Lab04..."

# Kiểm tra MongoDB đã chạy chưa
if ! docker ps | grep -q mongodb; then
    echo "❌ MongoDB container chưa chạy. Hãy khởi động Docker services trước:"
    echo "   ./start-docker.sh"
    exit 1
fi

echo "✅ MongoDB đã chạy"

# Tạo database và collections
echo "📊 Tạo database và collections..."

# Connect to MongoDB và tạo collections
docker exec -it mongodb mongosh --eval "
use bigdata_lab04;

// Tạo các collections cho từng window
db.createCollection('btc-price-zscore-30s');
db.createCollection('btc-price-zscore-1m');
db.createCollection('btc-price-zscore-5m');
db.createCollection('btc-price-zscore-15m');
db.createCollection('btc-price-zscore-30m');
db.createCollection('btc-price-zscore-1h');

// Tạo indexes cho performance
db['btc-price-zscore-30s'].createIndex({timestamp: 1});
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
