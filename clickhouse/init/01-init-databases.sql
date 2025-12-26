-- Create database analytics if not exists
CREATE DATABASE IF NOT EXISTS analytics;

-- Use database analytics
USE analytics;

-- Table raw for customers
CREATE TABLE IF NOT EXISTS raw_customers (
    customer_id Int32,
    name String,
    email String,
    state String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY customer_id;

-- Table raw for products
CREATE TABLE IF NOT EXISTS raw_products (
    product_id Int32,
    name String,
    category String,
    price Float64,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY product_id;

-- Tabela raw para orders   
CREATE TABLE IF NOT EXISTS raw_orders (
    order_id Int32,
    customer_id Int32,
    order_date DateTime,
    total_amount Float64,
    status String
) ENGINE = MergeTree()
ORDER BY order_id;

-- Table raw for order_items
CREATE TABLE IF NOT EXISTS raw_order_items (
    order_item_id Int32,
    order_id Int32,
    product_id Int32,
    quantity Int32,
    unit_price Float64,
    total_price Float64
) ENGINE = MergeTree()
ORDER BY order_item_id;

-- Tables for transformed data (staging)
CREATE TABLE IF NOT EXISTS stg_customers (
    customer_id Int32,
    name String,
    email String,
    state String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY customer_id;

CREATE TABLE IF NOT EXISTS stg_products (
    product_id Int32,
    name String,
    category String,
    price Float64,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY product_id;

CREATE TABLE IF NOT EXISTS stg_orders (
    order_id Int32,
    customer_id Int32,
    order_date DateTime,
    total_amount Float64,
    status String
) ENGINE = MergeTree()
ORDER BY order_id;

CREATE TABLE IF NOT EXISTS stg_order_items (
    order_item_id Int32,
    order_id Int32,
    product_id Int32,
    quantity Int32,
    unit_price Float64,
    total_price Float64
) ENGINE = MergeTree()
ORDER BY order_item_id;

-- Tables for analytical data (marts)
CREATE TABLE IF NOT EXISTS fact_sales (
    order_id Int32,
    customer_id Int32,
    product_id Int32,
    order_date DateTime,
    quantity Int32,
    unit_price Float64,
    total_price Float64,
    customer_name String,
    product_name String,
    category String,
    state String
) ENGINE = MergeTree()
ORDER BY (order_id, customer_id, product_id);

CREATE TABLE IF NOT EXISTS agg_sales_by_state (
    state String,
    total_sales Float64,
    total_orders Int32,
    total_items Int32,
    avg_order_value Float64,
    date DateTime
) ENGINE = MergeTree()
ORDER BY (state, date);

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id Int32,
    name String,
    email String,
    state String,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY customer_id;

CREATE TABLE IF NOT EXISTS dim_products (
    product_id Int32,
    name String,
    category String,
    price Float64,
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY product_id;
