{{ config(materialized='view') }}

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    state,
    city,
    created_at
FROM {{ source('raw', 'customers') }}
