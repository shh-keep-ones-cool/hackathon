"""Extract legacy PCI sub-indices (Sub-Index 1..10) from VCCI workbooks into data/pci_panel_63.csv.

Replaces copying cells by hand. Safe by design:
  * Dry-run by default; nothing is written unless you pass --write.
  * Finds each sub-index by its "Sub-Index k" header; it never guesses by position.
  * Checks that the sheet/header text matches the expected sub-index (entry, land, ...).
  * Needs exactly 63 provinces per sub-index, otherwise that sub-index is skipped and reported.
  * Cross-checks the Summary sheet against the per-sub-index sheet when both exist.
  * Always writes data/raw/pci/pci_extract_audit.csv: every value with its sheet and Excel cell, for spot checks.
  * Only fills pci_old_1..pci_old_10. Other columns (framework_version, n_surveyed_firms) are untouched.

Usage (project root):
    python analysis/extract_pci_panel_63.py            # dry run: print report only
    python analysis/extract_pci_panel_63.py --write    # back up pci_panel_63.csv, then fill it
"""
from __future__ import annotations

import argparse
import re
import shutil
import unicodedata
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message=".*xlrd engine.*")      # chỉ tắt cảnh báo lặp, không ảnh hưởng dữ liệu
warnings.filterwarnings("ignore", message=".*Unknown extension.*")

ROOT = Path(__file__).resolve().parents[1]

HDR = re.compile(r"sub-?\s*index\s*(\d+)", re.I)
EXPECT = {1: ["entry"], 2: ["land"], 3: ["transparen"], 4: ["time"], 5: ["informal"], 6: ["bias"],
          7: ["proactiv"], 8: ["bss", "support", "suport"],   # workbook 2012-2013 viết sai chính tả "suport"
          9: ["labor", "labour"], 10: ["legal", "law"]}
ALIAS = {"hcmc": "hochiminh", "hcm": "hochiminh", "tphcm": "hochiminh", "tphochiminh": "hochiminh",
         "thanhphohochiminh": "hochiminh", "brvt": "bariavungtau", "tthue": "thuathienhue",
         "hue": "thuathienhue"}


def key(value) -> str:
    s = str(value or "").strip().lower().replace("đ", "d").replace("ð", "d")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"^(tinh|thanh pho|tp\.?)\s+", "", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return ALIAS.get(s, s)


def col_letter(c: int) -> str:
    out = ""
    c += 1
    while c:
        c, r = divmod(c - 1, 26)
        out = chr(65 + r) + out
    return out


def load_crosswalk(root: Path) -> dict[str, str]:
    cw = pd.read_csv(root / "data/crosswalk_63_to_34.csv", dtype=str, encoding="utf-8-sig")
    m = {key(n): i for n, i in zip(cw.old_province_name, cw.old_province_id)}
    if len(m) != 63:
        raise ValueError(f"Crosswalk cho {len(m)} khóa tên duy nhất, cần 63.")
    return m


def find_headers(df: pd.DataFrame, sheet: str):
    """Yield (k, header_row, value_col, header_text) for every 'Sub-Index k' header in the first 4 rows."""
    for r in range(min(4, len(df))):
        for c in range(df.shape[1]):
            m = HDR.search(str(df.iat[r, c]))
            if m and 1 <= int(m.group(1)) <= 10:
                yield int(m.group(1)), r, c, str(df.iat[r, c])


def read_block(df, hdr_row, vcol, names):
    """Return ({province_key: value}, notes) reading rows below the header."""
    for pcol in (vcol - 1, 0):
        if pcol < 0:
            continue
        keys = df.iloc[hdr_row + 1:, pcol].map(key)
        if keys.isin(names).sum() >= 50:
            break
    else:
        return None, ["không tìm thấy cột tên tỉnh"]
    out, notes = {}, []
    vals = pd.to_numeric(df.iloc[hdr_row + 1:, vcol], errors="coerce")
    for idx, k, v in zip(keys.index, keys, vals):
        if k not in names or pd.isna(v):
            continue
        if k in out:
            if abs(out[k][0] - v) > 1e-9:
                notes.append(f"dòng lặp {k}: giữ {out[k][0]:.6f}, bỏ {v:.6f}")
            continue
        out[k] = (float(v), int(idx) + 1)  # (giá trị, số dòng Excel)
    return out, notes


def extract_year(path: Path, names: dict[str, str]):
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    found: dict[int, list] = {}
    log: list[str] = []
    for sheet, df in sheets.items():
        for k, r, c, text in find_headers(df, sheet):
            blob = f"{sheet} {text}".lower()
            if not any(w in blob for w in EXPECT[k]):
                log.append(f"BỎ Sub-Index {k} ở sheet '{sheet}': tên '{text}' không khớp chỉ số mong đợi")
                continue
            block, notes = read_block(df, r, c, names)
            if block is None:
                log.append(f"BỎ Sub-Index {k} ở sheet '{sheet}': {notes[0]}")
                continue
            log += [f"Sub-Index {k} [{sheet}]: {n}" for n in notes]
            found.setdefault(k, []).append((sheet, block, c))
    data = {}
    for k, cands in found.items():
        cands.sort(key=lambda x: x[0].lower() == "summary")  # per-sub-index sheet first
        sheet, block, vcol = cands[0]
        if len(block) != 63:
            log.append(f"BỎ Sub-Index {k}: {len(block)} tỉnh khớp crosswalk (cần 63) ở sheet '{sheet}'")
            continue
        for other_sheet, other, _ in cands[1:]:
            diff = sum(abs(block[p][0] - other[p][0]) > 1e-6 for p in block if p in other)
            if diff:
                log.append(f"CẢNH BÁO Sub-Index {k}: '{sheet}' và '{other_sheet}' khác nhau ở {diff} tỉnh")
        data[k] = {"sheet": sheet, "col": col_letter(vcol), "block": block}
    return data, log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    names = load_crosswalk(root)
    panel_path = root / "data/pci_panel_63.csv"
    panel = pd.read_csv(panel_path, dtype={"province_id_old": str}, encoding="utf-8-sig")
    for k in range(1, 11):
        col = f"pci_old_{k}"
        if col not in panel.columns:
            panel[col] = np.nan
        panel[col] = pd.to_numeric(panel[col], errors="coerce").astype(float)

    files = sorted((root / "data/raw/pci").glob("PCI_20??.xls*"))
    summary, filled, overwritten, audit = [], 0, 0, []
    for f in files:
        year = int(re.search(r"(20\d{2})", f.stem).group(1))
        try:
            data, log = extract_year(f, names)
        except Exception as exc:  # unreadable workbook
            print(f"\n{year}: LỖI đọc {f.name}: {exc}")
            summary.append((year, "ERROR", ""))
            continue
        got = sorted(data)
        missing = [k for k in range(1, 11) if k not in data]
        print(f"\n{year} ({f.name}): có Sub-Index {got}; thiếu {missing}")
        for line in log:
            print("   -", line)
        summary.append((year, ",".join(map(str, got)), ",".join(map(str, missing))))
        for k, info in data.items():
            col = f"pci_old_{k}"
            for pkey, (value, xl_row) in info["block"].items():
                audit.append({"year": year, "source_file": f.name, "province_id_old": names[pkey], "sub_index": k,
                              "pci_old_col": col, "value": value, "sheet": info["sheet"],
                              "excel_cell": f"{info['col']}{xl_row}"})
                mask = (panel.province_id_old == names[pkey]) & (panel.year == year)
                if mask.sum() != 1:
                    print(f"   - không có đúng 1 dòng panel cho {names[pkey]} {year}")
                    continue
                old = panel.loc[mask, col].iloc[0]
                if pd.notna(old) and abs(old - value) > 1e-9:
                    overwritten += 1
                panel.loc[mask, col] = value
                filled += 1

    print("\n==== TỔNG KẾT ====")
    print(pd.DataFrame(summary, columns=["year", "sub_index_found", "sub_index_missing"]).to_string(index=False))
    print(f"Ô được điền: {filled} | ô đã có giá trị khác bị ghi đè: {overwritten}")
    audit_path = root / "data/raw/pci/pci_extract_audit.csv"
    pd.DataFrame(audit).to_csv(audit_path, index=False, encoding="utf-8-sig")
    print(f"Bảng truy vết (mỗi giá trị → sheet và ô Excel gốc): {audit_path}")
    if not args.write:
        print("\nDry run: chưa ghi vào pci_panel_63.csv. Thêm --write để ghi.")
        return
    backup = panel_path.with_name(f"pci_panel_63.bak_{datetime.now():%Y%m%d_%H%M%S}.csv")
    shutil.copy2(panel_path, backup)
    panel.to_csv(panel_path, index=False, encoding="utf-8-sig")
    print(f"\nĐã sao lưu: {backup.name}\nĐã ghi: {panel_path}")


if __name__ == "__main__":
    main()