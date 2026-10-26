import os
import json
from datetime import datetime
import pandas as pd

CHECKPOINT_FILE = "data/checkpoint.json"
INPUT_FILE = "data/valid/valid_orders.parquet"
OUTPUT_FILE = "data/valid/transformed_orders.parquet"

def get_last_watermark() -> str:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_watermark", "1970-01-01T00:00:00Z")
    return "1970-01-01T00:00:00Z"

def save_watermark(timestamp_str: str):
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"last_watermark": timestamp_str, "updated_at": datetime.now().isoformat()}, f, indent=2)

def run_transformation():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File input '{INPUT_FILE}' tidak ditemukan. Jalankan scripts/validate.py terlebih dahulu.")
        return

    last_watermark = get_last_watermark()
    print(f"ℹ️ Watermark Terakhir: {last_watermark}")

    df = pd.read_parquet(INPUT_FILE)

    df["order_ts"] = pd.to_datetime(df["order_ts"], utc=True)
    last_watermark_dt = pd.to_datetime(last_watermark, utc=True)

    new_records = df[df["order_ts"] > last_watermark_dt].copy()

    if new_records.empty:
        print(" Validasi Watermark: Tidak ada data/record baru untuk diproses.")
        return

    print(f" Mengolah {len(new_records)} record baru...")

    new_records["quantity"] = new_records["quantity"].astype(int)
    new_records["unit_price"] = new_records["unit_price"].astype(float)
    new_records["discount_pct"] = new_records["discount_pct"].astype(float)

    new_records["gross_amount"] = new_records["quantity"] * new_records["unit_price"]
    new_records["net_amount"] = new_records["gross_amount"] * (1 - new_records["discount_pct"])

    new_records["order_ts"] = new_records["order_ts"].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    if os.path.exists(OUTPUT_FILE):
        df_existing = pd.read_parquet(OUTPUT_FILE)
        df_existing["order_ts"] = pd.to_datetime(df_existing["order_ts"], utc=True).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Gabungkan data lama dan baru
        df_combined = pd.concat([df_existing, new_records], ignore_index=True)
        # Deduplikasi berdasarkan order_id, ambil record terbaru
        df_final = df_combined.drop_duplicates(subset=["order_id"], keep="last")
    else:
        df_final = new_records.drop_duplicates(subset=["order_id"], keep="last")

    # Simpan ke Parquet
    df_final.to_parquet(OUTPUT_FILE, index=False)
    print(f"✅ Berhasil menyimpan {len(df_final)} total record ke '{OUTPUT_FILE}'")

    # 5. Simpan Watermark Baru (Hanya setelah penulisan sukses)
    max_ts = new_records["order_ts"].max()
    save_watermark(max_ts)
    print(f"✅ Watermark baru diperbarui ke: {max_ts}")

if __name__ == "__main__":
    run_transformation()