FROM python:3.11-slim

WORKDIR /usr/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dbt, ClickHouse adapter, and Flask for webhook
# Pin protobuf<5.0.0 for dbt-core 1.7.0 compatibility
RUN pip install --no-cache-dir \
    "protobuf>=4.0.0,<5.0.0" \
    dbt-core==1.7.0 \
    dbt-clickhouse==1.7.0 \
    flask \
    requests

# Copy project files
COPY . .

# Set environment variables
ENV DBT_PROFILES_DIR=/usr/app

# Expose webhook port
EXPOSE 5000

# Default command
CMD ["dbt", "--version"]
