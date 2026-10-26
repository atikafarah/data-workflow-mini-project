
    

    create  table
      "warehouse"."main"."fct_orders__dbt_tmp"
  
    
    as (
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
FROM "warehouse"."main"."stg_orders"
    );
    
  