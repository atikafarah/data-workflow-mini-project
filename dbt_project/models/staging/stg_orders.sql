WITH source AS (
    SELECT * FROM {{ source('raw_data', 'raw_orders') }}
)
SELECT
    order_id,
    customer_id,
    CAST(order_ts AS TIMESTAMP) AS order_ts,
    CAST(order_ts AS DATE) AS order_date,
    product_category,
    CAST(quantity AS INT) AS quantity,
    CAST(unit_price AS FLOAT) AS unit_price,
    CAST(discount_pct AS FLOAT) AS discount_pct,
    CAST(gross_amount AS FLOAT) AS gross_amount,
    CAST(net_amount AS FLOAT) AS net_amount,
    payment_method,
    status
FROM source