
from pathlib import Path
import pandas as pd

DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "datasets"
    / "minnesota_biofilm"
)

print("\nBIOFILM AI - CORRECTED DATA INSPECTION")
print("=" * 65)

if not DATA_DIR.exists():
    raise FileNotFoundError(f"Dataset folder not found: {DATA_DIR}")

for path in sorted(DATA_DIR.glob("*.xlsx")):
    print(f"\nFILE: {path.name}")
    print("-" * 65)

    excel = pd.ExcelFile(path)
    print("Sheets:", excel.sheet_names)

    for sheet in excel.sheet_names:
        # Actual headers are on Excel row 2
        df = pd.read_excel(path, sheet_name=sheet, header=1)

        # Remove completely empty columns
        df = df.dropna(axis=1, how="all")

        print(f"\nSheet: {sheet}")
        print("Shape:", df.shape)
        print("Columns:", df.columns.tolist())

        # Display only the experimental data columns
        print("\nFirst 8 rows:")
        print(df.head(8).to_string(index=False))

        print("\nMissing values:")
        print(df.isna().sum().to_dict())

        # Numeric columns only
        numeric = df.select_dtypes(include="number")
        if not numeric.empty:
            print("\nNumeric summary:")
            print(numeric.describe().to_string())

print("\nINSPECTION COMPLETE")
