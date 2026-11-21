
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw/gso")

FILES = [
    "V05.02.xlsx",
    "V05.04.xlsx",
    "V02.03-07.xlsx",
    "V03.12.xlsx",
    "V03.10.xlsx",
]

for filename in FILES:
    path = DATA_DIR / filename

    print("\n" + "=" * 100)
    print(f"FILE: {filename}")
    print("=" * 100)

    if not path.exists():
        print("[MISSING]", path)
        continue

    df = pd.read_excel(path, header=None)

    print("Total rows:", len(df))
    print("Total columns:", len(df.columns))

    print("\nALL ROW LABELS:")
    for i, value in enumerate(df.iloc[:, 0].tolist()):
        if pd.notna(value):
            print(f"Row {i}: {str(value).strip()}")

    print("\nLAST 10 ROWS:")
    print(df.tail(10).to_string(index=True, header=False))

# Kiểm tra các file crosswalk hiện có
print("\n" + "=" * 100)
print("CROSSWALK FILES")
print("=" * 100)

for path in Path("data").rglob("*"):
    if path.is_file() and any(
        keyword in path.name.lower()
        for keyword in ["crosswalk", "concordance", "province"]
    ):
        print(path)
