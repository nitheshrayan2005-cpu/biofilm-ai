
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "datasets" / "minnesota_biofilm"
OUTPUT_DIR = PROJECT_DIR / "datasets" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "biofilm_thickness.csv"

# Excel workbooks
FILES = {
    "FLAT": "FLAT.xlsx",
    "RC1": "RC1.xlsx",
    "RC2": "RC2.xlsx",
    "RC3": "RC3.xlsx",
    "RT1": "RT1.xlsx",
    "RT2": "RT2.xlsx",
    "RT3": "RT3.xlsx",
}

records = []
skipped = []

for channel, filename in FILES.items():
    filepath = DATA_DIR / filename

    if not filepath.exists():
        print(f"Missing workbook: {filepath}")
        continue

    excel = pd.ExcelFile(filepath)

    for sheet in excel.sheet_names:
        # Example sheet names: 1ulmin, 5ulmin
        sheet_name = sheet.lower().replace(" ", "")

        if not sheet_name.endswith("ulmin"):
            print(f"Skipping unexpected sheet: {channel}/{sheet}")
            continue

        flow_text = sheet_name.removesuffix("ulmin")

        try:
            flow_rate = float(flow_text)
        except ValueError:
            print(f"Skipping unrecognized flow rate: {channel}/{sheet}")
            continue

        try:
            df = pd.read_excel(
                filepath,
                sheet_name=sheet,
                header=1
            )
        except Exception as exc:
            print(f"Could not read {channel}/{sheet}: {exc}")
            continue

        # Remove fully empty rows and columns
        df = df.dropna(how="all").dropna(axis=1, how="all")
        df.columns = [str(c).strip() for c in df.columns]

        # We need time and AVEG for this initial dataset
        if not {"time", "AVEG"}.issubset(df.columns):
            skipped.append(f"{channel}/{sheet}: missing time or AVEG")
            continue

        # Keep only target and proposed metadata.
        # Do not use measurement-derived values as predictors.
        selected = df[["time", "AVEG"]].copy()

        selected["flow_rate_ul_min"] = flow_rate
        selected["channel"] = channel
        selected["source_sheet"] = sheet
        selected["source_workbook"] = filename

        selected["time"] = pd.to_numeric(
            selected["time"], errors="coerce"
        )
        selected["AVEG"] = pd.to_numeric(
            selected["AVEG"], errors="coerce"
        )

        selected = selected.dropna(subset=["time", "AVEG"])

        records.extend(selected.to_dict("records"))

if not records:
    raise RuntimeError(
        "No usable rows found. Check workbook paths, sheet names and headers."
    )

combined = pd.DataFrame(records)

# Sort for readability
combined = combined.sort_values(
    ["channel", "flow_rate_ul_min", "time"]
).reset_index(drop=True)

# Save
combined.to_csv(OUTPUT_FILE, index=False)

print("\nDATASET PREPARATION COMPLETE")
print(f"Output: {OUTPUT_FILE}")
print(f"Total rows: {len(combined)}")
print(f"Channels: {combined['channel'].nunique()}")
print(f"Flow rates: {sorted(combined['flow_rate_ul_min'].unique())}")
print(f"Missing values:\n{combined.isna().sum()}")
print("\nRows per channel:")
print(combined.groupby("channel").size())
print("\nRows per channel and flow:")
print(combined.groupby(
    ["channel", "flow_rate_ul_min"]
).size())

if skipped:
    print("\nSkipped sheets:")
    for item in skipped:
        print("-", item)

print("\nFirst 10 rows:")
print(combined.head(10).to_string(index=False))
