SELECT
    order_id,
    customer_id,
    product_category,
    order_ts,
    order_date,
    quantity,
    unit_price,
    discount_pct,
    gross_amount,
    net_amount,
    payment_method,
    status
FROM {{ ref('stg_orders') }}