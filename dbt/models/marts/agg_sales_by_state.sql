{{ config(
    materialized='table',
    order_by='state'
) }}

SELECT
    state,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    SUM(quantity) AS total_quantity,
    SUM(revenue) AS total_revenue,
    SUM(cost) AS total_cost,
    SUM(profit) AS total_profit,
    AVG(revenue) AS avg_order_value,
    SUM(profit) / SUM(revenue) * 100 AS profit_margin_pct
FROM {{ ref('fact_sales') }}
GROUP BY state
ORDER BY total_revenue DESC
