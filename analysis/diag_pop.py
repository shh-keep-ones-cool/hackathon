import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from fetch_gso_pxweb import load_crosswalk, norm, ROOT

cw = load_crosswalk()
path = ROOT / "data/raw/gso/V02.03-07.xlsx"
xl = pd.ExcelFile(path)
print("Sheets:", xl.sheet_names)

sheet = pd.read_excel(path, header=None, sheet_name=0)
names = sheet.iloc[:, 0].dropna().astype(str).tolist()
keys = {norm(n) for n in names}

missing = cw[~cw.name_key.isin(keys)]
print("\nTỉnh trong crosswalk nhưng KHÔNG khớp trong file:")
print(missing[["old_province_id", "old_province_name", "name_key"]].to_string(index=False))

print("\nCác dòng trong file không khớp crosswalk (cột đầu):")
for n in names:
    if norm(n) not in set(cw.name_key):
        print(repr(n), "->", norm(n))