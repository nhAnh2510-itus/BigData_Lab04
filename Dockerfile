FROM python:3.12-slim

# Cài đặt các dependencies hệ thống và Java cho Spark
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    curl \
    openjdk-17-jdk \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập JAVA_HOME cho Spark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Tạo thư mục làm việc
WORKDIR /app

# Download và cài đặt Spark
ENV SPARK_VERSION=3.5.6
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

# Copy và giải nén Spark từ file có sẵn
COPY spark-3.5.6-bin-hadoop3.tgz /tmp/
RUN tar -xzf /tmp/spark-3.5.6-bin-hadoop3.tgz -C /opt/ \
    && mv /opt/spark-3.5.6-bin-hadoop3 ${SPARK_HOME} \
    && rm /tmp/spark-3.5.6-bin-hadoop3.tgz

# Copy requirements và cài đặt Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY docs/ ./docs/

# Tạo thư mục cho checkpoints
RUN mkdir -p /app/checkpoints

# Tạo user non-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Setup Spark configs cho container
ENV SPARK_CONF_DIR=/app
ENV PYSPARK_PYTHON=/usr/local/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python
ENV PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip:$PYTHONPATH

# Expose port (nếu cần)
EXPOSE 8000

# Default command - shell để chạy interactive
CMD ["/bin/bash"]
