{{ config(
    materialized='table',
    order_by='order_date'
) }}

SELECT
    oi.order_item_id AS order_item_id,
    o.order_id AS order_id,
    o.customer_id AS customer_id,
    oi.product_id AS product_id,
    o.order_date AS order_date,
    o.order_year AS order_year,
    o.order_month AS order_month,
    o.order_quarter AS order_quarter,
    o.status AS status,
    oi.quantity AS quantity,
    oi.unit_price AS unit_price,
    oi.subtotal AS revenue,
    p.cost * oi.quantity AS cost,
    oi.subtotal - (p.cost * oi.quantity) AS profit,
    c.state AS state,
    c.city AS city,
    p.category AS category
FROM {{ ref('stg_order_items') }} oi
INNER JOIN {{ ref('stg_orders') }} o ON oi.order_id = o.order_id
INNER JOIN {{ ref('stg_products') }} p ON oi.product_id = p.product_id
INNER JOIN {{ ref('stg_customers') }} c ON o.customer_id = c.customer_id
