import time
import os
import pandas as pd
import polars as pl

CSV_FILE = "data/orders.csv"

def run_benchmark(iterations: int = 5):
    print("BENCHMARK PERFORMANCE: PANDAS vs POLARS")

    # 1. Pandas Benchmark
    pandas_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        df_pd = pd.read_csv(CSV_FILE)
        df_pd["gross_amount"] = df_pd["quantity"] * df_pd["unit_price"]
        df_pd["net_amount"] = df_pd["gross_amount"] * (1 - df_pd["discount_pct"])
        summary_pd = df_pd.groupby("product_category", dropna=False)["net_amount"].sum()
        pandas_times.append(time.perf_counter() - start)

    avg_pandas = sum(pandas_times) / iterations
    print(f"⏱️  Pandas Average Time ({iterations} runs): {avg_pandas:.4f} seconds")

    # 2. Polars Eager Benchmark
    polars_eager_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        df_pl = pl.read_csv(CSV_FILE)
        df_pl = df_pl.with_columns(
            (pl.col("quantity") * pl.col("unit_price")).alias("gross_amount"),
            (pl.col("quantity") * pl.col("unit_price") * (1 - pl.col("discount_pct"))).alias("net_amount"),
        )
        summary_pl = df_pl.group_by("product_category").agg(pl.col("net_amount").sum())
        polars_eager_times.append(time.perf_counter() - start)

    avg_polars_eager = sum(polars_eager_times) / iterations
    print(f"⏱️  Polars Eager Average Time ({iterations} runs): {avg_polars_eager:.4f} seconds")

    # 3. Polars Lazy Benchmark
    polars_lazy_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        query = (
            pl.scan_csv(CSV_FILE)
            .with_columns(
                (pl.col("quantity") * pl.col("unit_price")).alias("gross_amount"),
                (pl.col("quantity") * pl.col("unit_price") * (1 - pl.col("discount_pct"))).alias("net_amount"),
            )
            .group_by("product_category")
            .agg(pl.col("net_amount").sum())
        )
        summary_lazy = query.collect()
        polars_lazy_times.append(time.perf_counter() - start)

    avg_polars_lazy = sum(polars_lazy_times) / iterations
    print(f"⏱️  Polars Lazy Average Time ({iterations} runs): {avg_polars_lazy:.4f} seconds")

def run_skew_experiment():
    print("DATA SKEW EXPERIMENT")

    df_orig = pl.read_csv(CSV_FILE)
    
    # 1. Buat Dataset Skewed (Mereplikasi 1000x record dengan customer_id dominan)
    dominant_customer_id = df_orig["customer_id"][0]
    df_dominant = df_orig.filter(pl.col("customer_id") == dominant_customer_id)
    
    # Replikasi data untuk menciptakan beban tidak merata (skewness)
    skewed_records = pl.concat([df_orig] + [df_dominant] * 1000)
    
    print(f"Original Dataset Size: {len(df_orig)} rows")
    print(f"Skewed Dataset Size  : {len(skewed_records)} rows")
    print(f"Dominant Customer ID : {dominant_customer_id}")

    # 2. Ukur waktu group_by pada dataset normal vs skewed
    start = time.perf_counter()
    res_orig = df_orig.group_by("customer_id").agg(pl.col("quantity").sum())
    time_orig = time.perf_counter() - start

    start = time.perf_counter()
    res_skewed = skewed_records.group_by("customer_id").agg(pl.col("quantity").sum())
    time_skewed = time.perf_counter() - start

    print(f"\n⏱️  Normal Group By Time : {time_orig:.4f} seconds")
    print(f"⏱️  Skewed Group By Time : {time_skewed:.4f} seconds")

if __name__ == "__main__":
    run_benchmark()
    run_skew_experiment()