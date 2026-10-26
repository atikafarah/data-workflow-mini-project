import json
import os
from datetime import datetime
import pandas as pd
from kafka import KafkaConsumer, TopicPartition
from pydantic import ValidationError
from validate import OrderContract

def run_consumer():
    # Menyetel enable_auto_commit=False untuk menggunakan manual commit
    consumer = KafkaConsumer(
        "orders",
        bootstrap_servers=["localhost:9092"],
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id="order-processing-group"
    )

    valid_out = "data/valid"
    rejected_out = "data/rejected"
    os.makedirs(valid_out, exist_ok=True)
    os.makedirs(rejected_out, exist_ok=True)

    processed_keys = set()
    valid_records = []
    rejected_records = []

    print("🎧 Consumer mendengarkan topik 'orders'... (Tekan Ctrl+C jika ingin menghentikan)")

    try:
        # Polling pesan menggunakan Consumer
        for message in consumer:
            # 1. Catat topic, partition, dan offset
            print(f"📥 Received | Topic: {message.topic} | Partition: {message.partition} | Offset: {message.offset}")

            # 2. Penanganan JSON Rusak
            try:
                payload = json.loads(message.value.decode("utf-8"))
            except Exception as e:
                print(f"❌ Corrupted JSON payload at offset {message.offset}: {e}")
                rejected_records.append({
                    "raw_message": str(message.value),
                    "error_details": "Invalid JSON format",
                    "rejected_at": datetime.now().isoformat()
                })
                consumer.commit()  # Commit offset agar tidak terjebak di pesan rusak
                continue

            order_id = payload.get("order_id")

            # 3. Sink deduplikasi/upsert berdasarkan order_id
            if order_id in processed_keys:
                print(f"⚠️ Duplicate record detected for order_id: {order_id}. Skipped.")
                consumer.commit()
                continue

            processed_keys.add(order_id)

            # Preprocessing sederhana untuk tipe data float -> int pada quantity
            if "quantity" in payload and payload["quantity"] is not None:
                try:
                    val = float(payload["quantity"])
                    if val.is_integer():
                        payload["quantity"] = int(val)
                except (ValueError, TypeError):
                    pass

            # 4. Validasi dengan Kontrak Pydantic
            try:
                validated_item = OrderContract(**payload)
                valid_records.append(validated_item.model_dump())
            except ValidationError as e:
                rejected_records.append({
                    "order_id": order_id,
                    "raw_payload": payload,
                    "error_details": e.errors(),
                    "rejected_at": datetime.now().isoformat()
                })

            # 5. Commit offset manual setelah proses sink/logika selesai (At-Least-Once guarantee)
            consumer.commit()

    except KeyboardInterrupt:
        print("\n🛑 Consumer dihentikan pengguna.")

    # Simpan hasil sink stream
    if valid_records:
        df_stream = pd.DataFrame(valid_records)
        stream_path = os.path.join(valid_out, "stream_valid_orders.parquet")
        df_stream.to_parquet(stream_path, index=False)
        print(f"✅ {len(valid_records)} valid event records saved to '{stream_path}'")

    if rejected_records:
        rejected_path = os.path.join(rejected_out, "stream_rejected_orders.json")
        with open(rejected_path, "w", encoding="utf-8") as f:
            json.dump(rejected_records, f, indent=2, default=str)
        print(f"❌ {len(rejected_records)} invalid event records saved to '{rejected_path}'")

if __name__ == "__main__":
    run_consumer()