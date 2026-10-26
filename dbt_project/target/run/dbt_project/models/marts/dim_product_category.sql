
    

    create  table
      "warehouse"."main"."dim_product_category__dbt_tmp"
  
    
    as (
      SELECT DISTINCT
    product_category
FROM "warehouse"."main"."stg_orders"
WHERE product_category IS NOT NULL
    );
    
  