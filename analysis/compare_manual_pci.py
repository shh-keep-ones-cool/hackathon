"""So sánh bảng PCI bạn nhập tay (config/pci_historical_column_map_template.csv) với dữ liệu trích tự động.

Script nhận ra tỉnh của từng dòng bằng cách tìm giá trị đã nhập trong bảng truy vết data/raw/pci/pci_extract_audit.csv (tạo bởi extract_pci_panel_63.py).
Nếu bảng nhập tay có cột province_column chứa tên tỉnh, script kiểm tra thêm tên đó có đúng với số liệu không.
Kết quả: data/raw/pci/manual_vs_extracted_report.csv, mỗi dòng nhập tay một dòng báo cáo.

Chạy:  python analysis/extract_pci_panel_63.py     (tạo bảng truy vết)
       python analysis/compare_manual_pci.py
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_pci_panel_63 import key, load_crosswalk  # noqa: E402  (cùng thư mục analysis/)
KEYWORDS = [(1, ["entry"]), (2, ["land"]), (3, ["transparen"]), (4, ["time"]), (5, ["informal"]),
            (6, ["bias", "policy"]), (7, ["proactiv"]), (8, ["business support", "bss"]),
            (9, ["labor", "labour"]), (10, ["legal", "law"])]
TOL_MATCH, TOL_EXACT = 1e-4, 1e-6


def column_to_subindex(columns):
    out = {}
    for c in columns:
        name = str(c).lower()
        for k, words in KEYWORDS:
            if any(w in name for w in words):
                out[c] = k
                break
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manual", default="config/pci_historical_column_map_template.csv")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()
    root = Path(args.root)

    manual = pd.read_csv(root / args.manual, encoding="utf-8-sig")
    audit = pd.read_csv(root / "data/raw/pci/pci_extract_audit.csv", encoding="utf-8-sig")
    colmap = column_to_subindex(manual.columns)
    name_to_id = load_crosswalk(root)
    has_names = "province_column" in manual.columns and manual["province_column"].notna().any()
    print("Cột nhập tay được nhận diện:", {c: f"pci_old_{k}" for c, k in colmap.items()})

    rows = []
    for i, r in manual.iterrows():
        year = int(r["year"])
        src = audit[audit.year == year]
        entry = {"manual_csv_row": i + 2, "year": year, "province_id_old": "", "n_values": 0, "n_agree": 0,
                 "status": "", "details": ""}
        vals = {c: r[c] for c in colmap if pd.notna(r[c]) and str(r[c]).strip() != ""}
        entry["n_values"] = len(vals)
        if src.empty:
            entry["status"] = "CHUA_CO_NGUON (năm này chưa trích được)"
            rows.append(entry)
            continue
        if not vals:
            entry["status"] = "DONG_TRONG"
            rows.append(entry)
            continue
        votes = Counter()
        for c, v in vals.items():
            k = colmap[c]
            hit = src[(src.sub_index == k) & ((src.value - float(v)).abs() < TOL_MATCH)]
            for p in set(hit.province_id_old):
                votes[p] += 1
        if not votes:
            entry["status"] = "KHONG_KHOP_GI (không giá trị nào có trong workbook)"
            rows.append(entry)
            continue
        (best, n), *rest = votes.most_common()
        tie = bool(rest) and rest[0][1] == n
        entry.update(province_id_old=best, n_agree=n)
        bad = []
        for c, v in vals.items():
            k = colmap[c]
            w = src[(src.province_id_old == best) & (src.sub_index == k)].value
            if w.empty:
                bad.append(f"{c}: {v} nhưng workbook không có chỉ số này")
            elif abs(float(v) - w.iloc[0]) > TOL_EXACT:
                bad.append(f"{c}: nhập {v} ≠ workbook {w.iloc[0]}")
        if has_names and pd.notna(r["province_column"]):
            typed_id = name_to_id.get(key(r["province_column"]))
            if typed_id != best:
                bad.append(f"tên tỉnh nhập '{r['province_column']}' nhưng số liệu thuộc '{best}'")
                entry["name_mismatch"] = True
        entry["details"] = "; ".join(bad)
        if tie or n < len(vals) - 1:
            entry["status"] = "DONG_BI_TRON (các cột không cùng một tỉnh)"
        elif entry.get("name_mismatch"):
            entry["status"] = "SAI_TEN_TINH"
        else:
            entry["status"] = "OK" if not bad else "LECH_SO_LIEU"
        rows.append(entry)

    rep = pd.DataFrame(rows)
    dup = rep[rep.province_id_old != ""].duplicated(["year", "province_id_old"], keep=False)
    rep.loc[dup[dup].index, "status"] += " + TRUNG_TINH"
    out = root / "data/raw/pci/manual_vs_extracted_report.csv"
    rep.to_csv(out, index=False, encoding="utf-8-sig")

    print("\n==== TỔNG KẾT THEO NĂM ====")
    summ = rep.assign(group=rep.status.str.split(" ").str[0]).pivot_table(
        index="year", columns="group", values="manual_csv_row", aggfunc="count", fill_value=0)
    print(summ.to_string())
    ok_years = sorted(audit.year.unique())
    miss = []
    for y in ok_years:
        have = set(rep[(rep.year == y) & (rep.province_id_old != "")].province_id_old)
        allp = set(audit[audit.year == y].province_id_old)
        if allp - have:
            miss.append((y, len(allp - have)))
    print("\nNăm có nguồn nhưng bảng nhập tay còn thiếu tỉnh (năm, số tỉnh thiếu):", miss or "không")
    print("Báo cáo chi tiết:", out)


if __name__ == "__main__":
    main()