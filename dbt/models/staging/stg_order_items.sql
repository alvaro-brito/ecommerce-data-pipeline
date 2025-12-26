{{ config(materialized='view') }}

SELECT
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    subtotal
FROM {{ source('raw', 'order_items') }}
