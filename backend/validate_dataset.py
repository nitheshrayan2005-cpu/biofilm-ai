
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = (
    PROJECT_DIR
    / "datasets"
    / "processed"
    / "biofilm_thickness.csv"
)

df = pd.read_csv(DATA_FILE)

print("\n========== DATA VALIDATION ==========")

print("\n1. Dataset shape:")
print(df.shape)

print("\n2. Target summary:")
print(df["AVEG"].describe())

print("\n3. Negative thickness values:")
print((df["AVEG"] < 0).sum())

print("\n4. Zero thickness values:")
print((df["AVEG"] == 0).sum())

print("\n5. Zero values by channel and flow:")
zero_summary = (
    df.assign(is_zero=df["AVEG"] == 0)
    .groupby(["channel", "flow_rate_ul_min"])
    .agg(
        total_rows=("AVEG", "size"),
        zero_rows=("is_zero", "sum"),
        min_thickness=("AVEG", "min"),
        max_thickness=("AVEG", "max"),
    )
)
print(zero_summary.to_string())

print("\n6. Measurements per experiment:")
experiment_summary = (
    df.groupby(["channel", "flow_rate_ul_min"])
    .agg(
        rows=("AVEG", "size"),
        unique_times=("time", "nunique"),
        min_time=("time", "min"),
        max_time=("time", "max"),
    )
)
print(experiment_summary.to_string())

print("\n7. Duplicate time records per experiment:")
duplicates = df.duplicated(
    subset=["channel", "flow_rate_ul_min", "time"],
    keep=False
)
print("Rows involved:", int(duplicates.sum()))

if duplicates.any():
    print(df.loc[
        duplicates,
        ["channel", "flow_rate_ul_min", "time", "AVEG"]
    ].to_string(index=False))

print("\n8. Dataset columns:")
print(df.columns.tolist())

print("\nVALIDATION COMPLETE")
