import time
import json
import pandas as pd
from kafka import KafkaProducer

def json_serializer(data):
    return json.dumps(data, default=str).encode("utf-8")

def run_producer():
    producer = KafkaProducer(
        bootstrap_servers=["localhost:9092"],
        value_serializer=json_serializer,
        key_serializer=lambda k: str(k).encode("utf-8") if k else None
    )

    topic_name = "orders"
    csv_file = "data/orders.csv"

    # Membaca data sampel dari CSV
    df = pd.read_csv(csv_file)
    records = df.head(20).to_dict(orient="records")

    print(f"🚀 Mengirim {len(records)} event ke Kafka topic '{topic_name}'...")

    for record in records:
        order_id = record.get("order_id")
        # Producer menetapkan key pesan ke order_id untuk kebutuhan partisi
        producer.send(topic_name, key=order_id, value=record)
        print(f"Sent order_id: {order_id}")
        time.sleep(0.1)

    # --- SIMULASI DUPLIKASI PESAN ---
    duplicate_record = records[0]
    print(f"⚠️ Simulasi duplikasi: Mengirim ulang order_id: {duplicate_record['order_id']}")
    producer.send(topic_name, key=duplicate_record["order_id"], value=duplicate_record)

    producer.flush()
    producer.close()
    print("✅ Producer selesai mengirim pesan.")

if __name__ == "__main__":
    run_producer()