
    

    create  table
      "warehouse"."main"."dim_customer__dbt_tmp"
  
    
    as (
      SELECT DISTINCT
    customer_id
FROM "warehouse"."main"."stg_orders"
WHERE customer_id IS NOT NULL
    );
    
  