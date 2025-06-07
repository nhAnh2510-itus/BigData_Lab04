FROM python:3.12-slim

# Cài đặt các dependencies hệ thống và Java cho Spark
RUN apt-get update && apt-get install -y \
    gcc \
    openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập JAVA_HOME cho Spark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Tạo thư mục làm việc
WORKDIR /app

# Copy requirements và cài đặt Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY docs/ ./docs/

# Tạo user non-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (nếu cần)
EXPOSE 8000

# Default command - shell để chạy interactive
CMD ["/bin/bash"]
CMD ["python", "-c", "print('BigData Lab04 Container Ready! Use docker-compose exec python-app python src/extract.py')"]
