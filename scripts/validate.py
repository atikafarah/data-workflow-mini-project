import json
import os
from datetime import datetime
from typing import Literal, List, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator

class OrderContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    order_ts: datetime
    product_category: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    discount_pct: float = Field(ge=0, le=1)
    payment_method: str = Field(min_length=1)
    status: Literal["paid", "shipped", "cancelled", "refunded"]

    @field_validator("quantity", mode="before")
    @classmethod
    def convert_quantity_to_int(cls, v: Any) -> Any:
        # Menangani float dari Pandas/Numpy agar aman dikonversi ke int
        if isinstance(v, (float, int)):
            if float(v).is_integer():
                return int(v)
        return v

def validate_raw_data(raw_folder: str, valid_out: str, rejected_out: str):
    os.makedirs(valid_out, exist_ok=True)
    os.makedirs(rejected_out, exist_ok=True)

    valid_records: List[Dict[str, Any]] = []
    rejected_records: List[Dict[str, Any]] = []

    for file_name in os.listdir(raw_folder):
        if file_name.endswith(".parquet"):
            file_path = os.path.join(raw_folder, file_name)
            df_raw = pd.read_parquet(file_path)

            for index, row in df_raw.iterrows():
                payload = row.to_dict()

                # Konversi tambahan untuk memastikan float utuh menjadi int
                if "quantity" in payload and pd.notna(payload["quantity"]):
                    try:
                        val = float(payload["quantity"])
                        if val.is_integer():
                            payload["quantity"] = int(val)
                    except (ValueError, TypeError):
                        pass

                try:
                    # Validasi record
                    validated_item = OrderContract(**payload)
                    # Gunakan model_dump() standar (dikombinasikan dengan str/isoformat jika perlu)
                    data_dict = validated_item.model_dump()
                    valid_records.append(data_dict)
                except ValidationError as e:
                    # Isolasi record cacat
                    rejected_records.append({
                        "order_id": payload.get("order_id", None),
                        "raw_payload": payload,
                        "error_details": e.errors(),
                        "rejected_at": datetime.now().isoformat()
                    })

    # Simpan hasil
    if valid_records:
        df_valid = pd.DataFrame(valid_records)
        df_valid.to_parquet(os.path.join(valid_out, "valid_orders.parquet"), index=False)
        print(f"✅ Validation Success: {len(valid_records)} records saved to '{valid_out}/valid_orders.parquet'")

    if rejected_records:
        rejected_file_path = os.path.join(rejected_out, "rejected_orders.json")
        with open(rejected_file_path, "w", encoding="utf-8") as f:
            json.dump(rejected_records, f, indent=2, default=str)
        print(f"❌ Validation Errors: {len(rejected_records)} records isolated in '{rejected_out}/rejected_orders.json'")

if __name__ == "__main__":
    RAW_DIR = "data/raw"
    VALID_DIR = "data/valid"
    REJECTED_DIR = "data/rejected"

    validate_raw_data(RAW_DIR, VALID_DIR, REJECTED_DIR)