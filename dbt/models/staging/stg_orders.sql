{{ config(materialized='view') }}

SELECT
    order_id,
    customer_id,
    order_date,
    status,
    total_amount,
    toYear(order_date) AS order_year,
    toMonth(order_date) AS order_month,
    toQuarter(order_date) AS order_quarter
FROM {{ source('raw', 'orders') }}
