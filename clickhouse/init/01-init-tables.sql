-- Criação de tabelas RAW no ClickHouse

CREATE DATABASE IF NOT EXISTS raw;
CREATE DATABASE IF NOT EXISTS analytics;

-- Tabelas RAW (serão populadas pelo Airbyte)
CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id Int32,
    first_name String,
    last_name String,
    email String,
    phone String,
    state String,
    city String,
    created_at DateTime,
    _airbyte_ab_id String,
    _airbyte_emitted_at DateTime,
    _airbyte_normalized_at DateTime
) ENGINE = MergeTree()
ORDER BY customer_id;

CREATE TABLE IF NOT EXISTS raw.products (
    product_id Int32,
    product_name String,
    category String,
    price Decimal(10, 2),
    cost Decimal(10, 2),
    created_at DateTime,
    _airbyte_ab_id String,
    _airbyte_emitted_at DateTime,
    _airbyte_normalized_at DateTime
) ENGINE = MergeTree()
ORDER BY product_id;

CREATE TABLE IF NOT EXISTS raw.orders (
    order_id Int32,
    customer_id Int32,
    order_date DateTime,
    status String,
    total_amount Decimal(10, 2),
    _airbyte_ab_id String,
    _airbyte_emitted_at DateTime,
    _airbyte_normalized_at DateTime
) ENGINE = MergeTree()
ORDER BY order_id;

CREATE TABLE IF NOT EXISTS raw.order_items (
    order_item_id Int32,
    order_id Int32,
    product_id Int32,
    quantity Int32,
    unit_price Decimal(10, 2),
    subtotal Decimal(10, 2),
    _airbyte_ab_id String,
    _airbyte_emitted_at DateTime,
    _airbyte_normalized_at DateTime
) ENGINE = MergeTree()
ORDER BY order_item_id;
