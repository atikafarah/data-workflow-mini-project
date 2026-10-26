SELECT
    order_date,
    product_category,
    payment_method,
    COUNT(order_id) AS total_orders,
    SUM(gross_amount) AS total_gross_sales,
    SUM(net_amount) AS total_net_sales
FROM {{ ref('fct_orders') }}
WHERE LOWER(status) IN ('paid', 'shipped') -- Penjualan bersih hanya diakui jika paid/shipped
GROUP BY 1, 2, 3