import os
import json
import duckdb
import pandas as pd

DB_PATH = "warehouse/warehouse.duckdb"
REJECTED_BATCH_FILE = "data/rejected/rejected_orders.json"
REJECTED_STREAM_FILE = "data/rejected/stream_rejected_orders.json"

def run_analytics():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database '{DB_PATH}' tidak ditemukan. Pastikan data sudah dimuat ke DuckDB!")
        return

    conn = duckdb.connect(DB_PATH)
    print("=" * 60)
    print("📊 LAPORAN HASIL ANALISIS DATA (TAHAP 7)")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Penjualan Bersih Per Hari
    # ---------------------------------------------------------
    print("\n1. 📈 Penjualan Bersih per Hari:")
    query_1 = """
    SELECT 
        CAST(order_ts AS DATE) AS order_date, 
        ROUND(SUM(net_amount), 2) AS net_sales
    FROM fct_orders
    WHERE LOWER(status) IN ('paid', 'shipped')
    GROUP BY 1
    ORDER BY 1;
    """
    df_q1 = conn.execute(query_1).fetchdf()
    print(df_q1.to_string(index=False))

    # ---------------------------------------------------------
    # 2. Kategori Produk dengan Penjualan Tertinggi
    # ---------------------------------------------------------
    print("\n2. 🏆 Kategori Produk dengan Penjualan Tertinggi:")
    query_2 = """
    SELECT 
        product_category, 
        ROUND(SUM(net_amount), 2) AS net_sales
    FROM fct_orders
    WHERE LOWER(status) IN ('paid', 'shipped')
    GROUP BY product_category
    ORDER BY net_sales DESC;
    """
    df_q2 = conn.execute(query_2).fetchdf()
    print(df_q2.to_string(index=False))

    # ---------------------------------------------------------
    # 3. Jumlah Pesanan per Status
    # ---------------------------------------------------------
    print("\n3. 📦 Jumlah Pesanan Berdasarkan Status:")
    query_3 = """
    SELECT 
        status, 
        COUNT(*) AS order_count
    FROM fct_orders
    GROUP BY status
    ORDER BY order_count DESC;
    """
    df_q3 = conn.execute(query_3).fetchdf()
    print(df_q3.to_string(index=False))

    # ---------------------------------------------------------
    # 4. Metode Pembayaran Paling Sering Terpakai (Jawaban Opsional Tambahan)
    # ---------------------------------------------------------
    print("\n4. 💳 Metode Pembayaran Paling Sering Digunakan:")
    query_4 = """
    SELECT 
        payment_method, 
        COUNT(*) AS total_transactions
    FROM fct_orders
    GROUP BY payment_method
    ORDER BY total_transactions DESC;
    """
    df_q4 = conn.execute(query_4).fetchdf()
    print(df_q4.to_string(index=False))

    conn.close()

    # ---------------------------------------------------------
    # 5. Nilai & Analisis Pesanan yang Ditolak (Rejected Records)
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("❌ ANALISIS RECORD YANG DITOLAK (DATA CONTRACT REJECTIONS)")
    print("=" * 60)

    rejected_records = []
    
    # Membaca data rejected dari batch
    if os.path.exists(REJECTED_BATCH_FILE):
        with open(REJECTED_BATCH_FILE, "r", encoding="utf-8") as f:
            rejected_records.extend(json.load(f))

    # Membaca data rejected dari streaming
    if os.path.exists(REJECTED_STREAM_FILE):
        with open(REJECTED_STREAM_FILE, "r", encoding="utf-8") as f:
            rejected_records.extend(json.load(f))

    if not rejected_records:
        print("TIDAK ADA record yang ditolak oleh data contract.")
        return

    reason_summary = {}
    total_rejected_value = 0.0

    for item in rejected_records:
        payload = item.get("raw_payload", {})
        
        # Hitung estimasi gross amount jika quantity & unit_price tersedia
        qty = payload.get("quantity", 0) or 0
        price = payload.get("unit_price", 0) or 0
        try:
            total_rejected_value += (float(qty) * float(price))
        except (ValueError, TypeError):
            pass

        # Ekstrak alasan error
        errors = item.get("error_details", [])
        if isinstance(errors, list):
            for err in errors:
                msg = err.get("msg", "Unknown Error") if isinstance(err, dict) else str(err)
                loc = err.get("loc", ["-"])[-1] if isinstance(err, dict) else ""
                key = f"{loc}: {msg}" if loc else msg
                reason_summary[key] = reason_summary.get(key, 0) + 1
        else:
            reason_summary[str(errors)] = reason_summary.get(str(errors), 0) + 1

    print(f"Total Record Ditolak : {len(rejected_records)} baris")
    print(f"Estimasi Nilai Ditolak: Rp {total_rejected_value:,.2f}")
    print("\nRingkasan Penyebab Utama Penolakan:")
    for reason, count in reason_summary.items():
        print(f" - {reason}: {count} record")

if __name__ == "__main__":
    run_analytics()