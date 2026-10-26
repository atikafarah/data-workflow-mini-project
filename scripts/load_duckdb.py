import os
import duckdb

# Pastikan folder warehouse tersedia
os.makedirs("warehouse", exist_ok=True)

db_path = "warehouse/warehouse.duckdb"
parquet_valid = "data/valid/transformed_orders.parquet"

conn = duckdb.connect(db_path)

# Muat data valid ke tabel raw_orders (staging)
conn.execute(f"""
    CREATE OR REPLACE TABLE raw_orders AS 
    SELECT * FROM read_parquet('{parquet_valid}');
""")

print("✅ Data valid berhasil dimuat ke DuckDB tabel 'raw_orders'.")

# Verifikasi total baris
count = conn.execute("SELECT COUNT(*) FROM raw_orders;").fetchone()[0]
print(f" Total record di raw_orders: {count}")

conn.close()