{{ config(materialized='view') }}

SELECT
    product_id,
    product_name,
    category,
    price,
    cost,
    price - cost AS profit_margin,
    created_at
FROM {{ source('raw', 'products') }}
