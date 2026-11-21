"""Fetch NSO PxWeb tables and build the 63-province outcomes panel.

Verified table codes supplied by the project owner:
- V05.02: new enterprise registrations by province
- V05.04: active enterprises at 31 Dec by province
- V02.03-07: average population by province, sex and urban/rural

The script discovers dimension codes from the live metadata; it does not hard-code
province/year item codes. V03.12 and V03.10 are imported from the supplied NSO
Excel exports because those workbooks are already available locally.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw" / "gso"
CROSSWALK = DATA / "crosswalk_63_to_34.csv"
OUTCOMES = DATA / "outcomes_panel_63.csv"

BASE = "https://pxweb.nso.gov.vn/api/v1/vi"
TABLES = {
    "firms_new": f"{BASE}/Doanh%20nghi%E1%BB%87p/V05.02.px",
    "firms_active": f"{BASE}/Doanh%20nghi%E1%BB%87p/V05.04.px",
    "pop": f"{BASE}/D%C3%A2n%20s%E1%BB%91%20v%C3%A0%20lao%20%C4%91%E1%BB%99ng/V02.03-07.px",
}
TABLE_PAGE = {
    "firms_new": "https://pxweb.nso.gov.vn/pxweb/vi/Doanh%20nghi%E1%BB%87p/Doanh%20nghi%E1%BB%87p/V05.02.px/",
    "firms_active": "https://pxweb.nso.gov.vn/pxweb/vi/Doanh%20nghi%E1%BB%87p/Doanh%20nghi%E1%BB%87p/V05.04.px/",
    "pop": "https://pxweb.nso.gov.vn/pxweb/vi/D%C3%A2n%20s%E1%BB%91%20v%C3%A0%20lao%20%C4%91%E1%BB%99ng/D%C3%A2n%20s%E1%BB%91%20v%C3%A0%20lao%20%C4%91%E1%BB%99ng/V02.03-07.px/",
    "grdp_pc": "https://pxweb.nso.gov.vn/pxweb/vi/T%C3%A0i%20kho%E1%BA%A3n%20qu%E1%BB%91c%20gia/T%C3%A0i%20kho%E1%BA%A3n%20qu%E1%BB%91c%20gia/V03.12.px/",
    "grdp_growth_index": "https://pxweb.nso.gov.vn/pxweb/vi/T%C3%A0i%20kho%E1%BA%A3n%20qu%E1%BB%91c%20gia/T%C3%A0i%20kho%E1%BA%A3n%20qu%E1%BB%91c%20gia/V03.10.px/",
}


def norm(value: Any) -> str:
    s = str(value or "").strip().lower().replace("đ", "d").replace("ð", "d")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"^(tinh|thanh pho|tp\.?|province of|province|city of)\s+", "", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    aliases = {
        "hochiminh": "tphochiminh", "thanhphohochiminh": "tphochiminh",
        "tphcm": "tphochiminh", "tphochiminh": "tphochiminh", "hcmc": "tphochiminh",
        "hochiminhcity": "tphochiminh", "thua thien hue": "thuathienhue", "hue": "thuathienhue",
        "baria-vungtau": "bariavungtau", "bariavungtau": "bariavungtau",
        "backan": "backan", "baccan": "backan",
    }
    return aliases.get(s, s)


def get_var_values(var: dict) -> list[tuple[str, str]]:
    """Return [(item_code, item_label)] for classic PxWeb metadata."""
    codes = var.get("values", [])
    labels = var.get("valueTexts", codes)
    if isinstance(codes, dict):
        return [(str(k), str(v)) for k, v in codes.items()]
    return [(str(c), str(labels[i] if i < len(labels) else c)) for i, c in enumerate(codes)]


def load_crosswalk() -> pd.DataFrame:
    if not CROSSWALK.exists():
        raise FileNotFoundError(f"Không tìm thấy {CROSSWALK}")
    cw = pd.read_csv(CROSSWALK, dtype=str, encoding="utf-8-sig")
    required = {"old_province_id", "old_province_name"}
    if not required.issubset(cw.columns):
        raise ValueError(f"Crosswalk thiếu cột: {required - set(cw.columns)}")
    if cw.old_province_id.nunique() != 63 or len(cw) != 63:
        raise ValueError(f"Crosswalk cần đúng 63 tỉnh cũ; hiện có {len(cw)} dòng, {cw.old_province_id.nunique()} mã.")
    cw["name_key"] = cw.old_province_name.map(norm)
    return cw


def get_metadata(session: requests.Session, endpoint: str) -> list[dict]:
    """
    Fetch PxWeb metadata.

    Supports:
    - Classic PxWeb response: list of variables
    - Current NSO response: dict containing title and variables
    """
    response = session.get(endpoint, timeout=60)
    response.raise_for_status()

    payload = response.json()

    # Format 1: classic PxWeb metadata
    if isinstance(payload, list):
        return payload

    # Format 2: NSO PxWeb metadata
    if isinstance(payload, dict):
        variables = payload.get("variables")

        if isinstance(variables, list):
            print(
                f"[OK] Metadata loaded: "
                f"{payload.get('title', endpoint)} "
                f"({len(variables)} variables)"
            )
            return variables

        raise ValueError(
            f"Metadata PxWeb trả về JSON object "
            f"nhưng không có danh sách 'variables'. "
            f"Endpoint: {endpoint}. "
            f"Keys nhận được: {list(payload.keys())}"
        )

    raise ValueError(
        f"Metadata PxWeb có định dạng không hỗ trợ: "
        f"{type(payload).__name__}. Endpoint: {endpoint}"
    )


def identify_dimensions(metadata: list[dict], crosswalk: pd.DataFrame, table_key: str):
    expected = set(crosswalk.name_key)
    province_candidates = []
    year_candidates = []
    for var in metadata:
        pairs = get_var_values(var)
        matched = [norm(label) for _, label in pairs if norm(label) in expected]
        if len(set(matched)) >= 50:
            province_candidates.append((var, pairs, len(set(matched))))
        year_pairs = [(code, label, re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", label)) for code, label in pairs]
        years = [(code, int(m.group(1))) for code, _, m in year_pairs if m]
        var_label = norm(var.get("text", "") + " " + var.get("code", ""))
        if len(years) >= 2 and ("nam" in var_label or "year" in var_label or len(years) >= 5):
            year_candidates.append((var, pairs, years))
    if len(province_candidates) != 1:
        detail = [(x[0].get("text"), x[2]) for x in province_candidates]
        raise ValueError(f"Không xác định duy nhất chiều tỉnh trong {table_key}. Ứng viên: {detail}")
    if len(year_candidates) != 1:
        detail = [(x[0].get("text"), len(x[2])) for x in year_candidates]
        raise ValueError(f"Không xác định duy nhất chiều năm trong {table_key}. Ứng viên: {detail}")
    pvar, ppairs, _ = province_candidates[0]
    yvar, ypairs, year_values = year_candidates[0]
    extra = [v for v in metadata if v.get("code") not in {pvar.get("code"), yvar.get("code")}]
    return (pvar, ppairs), (yvar, ypairs, year_values), extra


def select_population_total(extra_vars: list[dict], table_key: str) -> list[tuple[dict, list[tuple[str, str]]]]:
    selected = []
    for var in extra_vars:
        pairs = get_var_values(var)
        exact = [(c, t) for c, t in pairs if norm(t) in {"tongso", "total", "all"}]
        if len(exact) == 1:
            selected.append((var, [exact[0]]))
        elif len(pairs) == 1:
            selected.append((var, pairs))
        else:
            labels = [t for _, t in pairs[:20]]
            raise ValueError(
                f"Bảng {table_key} có chiều phụ '{var.get('text')}' không thể tự chọn an toàn. "
                f"Các giá trị đầu: {labels}. Hãy xác nhận dòng 'Tổng số' trong metadata."
            )
    return selected


def years_from_meta(year_info) -> dict[int, str]:
    _, pairs, _ = year_info
    found = {}
    for code, label in pairs:
        m = re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", label)
        if m:
            found[int(m.group(1))] = code
    return found


def query_jsonstat2(session: requests.Session, endpoint: str, metadata: list[dict], crosswalk: pd.DataFrame,
                    table_key: str, years: list[int]) -> pd.DataFrame:
    (pvar, ppairs), year_info, extra_vars = identify_dimensions(metadata, crosswalk, table_key)
    yvar, _, _ = year_info

    expected = dict(zip(crosswalk.name_key, crosswalk.old_province_id))
    province_codes = []
    missing_names = []
    for code, label in ppairs:
        key = norm(label)
        if key in expected:
            province_codes.append(code)
    got = {norm(label) for code, label in ppairs if code in province_codes}
    missing_names = sorted(set(expected) - got)
    if missing_names:
        raise ValueError(f"{table_key}: thiếu {len(missing_names)} tỉnh cũ trong metadata: {missing_names[:12]}")

    years_map = years_from_meta(year_info)
    absent_years = [year for year in years if year not in years_map]
    if absent_years:
        raise ValueError(f"{table_key}: không có năm yêu cầu {absent_years}. Năm có sẵn: {sorted(years_map)}")

    query = [
        {"code": pvar["code"], "selection": {"filter": "item", "values": province_codes}},
        {"code": yvar["code"], "selection": {"filter": "item", "values": [years_map[y] for y in years]}},
    ]
    for var, pairs in select_population_total(extra_vars, table_key):
        query.append({"code": var["code"], "selection": {"filter": "item", "values": [c for c, _ in pairs]}})
 
    body = {"query": query, "response": {"format": "json-stat2"}}

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Thử endpoint có và không có dấu slash cuối
    candidates = [
        endpoint,
        endpoint.rstrip("/") + "/"
    ]

    response = None

    for candidate in candidates:
        print(f"\n[TEST POST] {candidate}")

        r = session.post(
            candidate,
            json=body,
            headers=headers,
            timeout=120
        )

        print("[STATUS]", r.status_code)
        print("[CONTENT-TYPE]", r.headers.get("Content-Type"))
        print("[RESPONSE]", r.text[:500])

        if r.ok:
            response = r
            print("[OK] POST request successful")
            break

    if response is None:
        print("\n========== PXWEB API ERROR ==========")
        print("HTTP Status:", r.status_code)
        print("Endpoint:", r.url)
        print("Response:", r.text[:5000])

        print("\n========== QUERY SENT ==========")
        print(json.dumps(body, ensure_ascii=False, indent=2))

        raise RuntimeError(
            f"PxWeb query failed: HTTP {r.status_code}"
        )

    result = response.json()
    (RAW / f"{table_key}_response.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    dims = result.get("id", [])
    sizes = result.get("size", [])
    dim_meta = result.get("dimension", {})
    categories = []
    for dim in dims:
        cat = dim_meta[dim]["category"]
        index = cat.get("index", {})
        if isinstance(index, list):
            code_order = index
        else:
            code_order = [k for k, _ in sorted(index.items(), key=lambda kv: kv[1])]
        labels = cat.get("label", {})
        categories.append([(code, labels.get(code, code)) for code in code_order])

    records = []
    values = result.get("value", [])
    for idx_tuple in itertools.product(*[range(n) for n in sizes]):
        linear = 0
        for i, ix in enumerate(idx_tuple):
            multiplier = int(np.prod(sizes[i + 1:])) if i + 1 < len(sizes) else 1
            linear += ix * multiplier
        val = values[linear] if linear < len(values) else None
        selected = {dims[i]: categories[i][idx_tuple[i]] for i in range(len(dims))}
        p_code, p_label = selected[pvar["code"]]
        _, province_label = p_code, p_label
        y_code, y_label = selected[yvar["code"]]
        year_match = re.search(r"(19\d{2}|20\d{2})", str(y_label))
        if not year_match:
            continue
        pid = expected.get(norm(province_label))
        if pid is None:
            continue
        records.append({"province_id_old": pid, "year": int(year_match.group(1)), table_key: val})
    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        raise ValueError(f"PxWeb trả về dữ liệu rỗng cho {table_key}; kiểm tra lại dimension query.")
    if frame.duplicated(["province_id_old", "year"]).any():
        raise ValueError(f"{table_key}: dữ liệu bị trùng tỉnh-năm, thường do chiều phụ chưa được lọc đúng.")
    return frame


def import_wide_nso_excel(path: Path, value_col: str, crosswalk: pd.DataFrame) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy workbook: {path}")
    sheet = pd.read_excel(path, header=None, sheet_name=0)
    header_idx = None
    for i in range(min(8, len(sheet))):
        years = [re.search(r"(19\d{2}|20\d{2})", str(x)) for x in sheet.iloc[i, 1:].tolist()]
        if sum(bool(m) for m in years) >= 4:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"Không tìm thấy hàng năm trong {path.name}")
    header = sheet.iloc[header_idx].tolist()
    year_cols = {}
    for col_idx, cell in enumerate(header[1:], start=1):
        m = re.search(r"(19\d{2}|20\d{2})", str(cell))
        if m:
            year_cols[col_idx] = int(m.group(1))
    id_by_name = dict(zip(crosswalk.name_key, crosswalk.old_province_id))
    long_rows = []
    for _, row in sheet.iloc[header_idx + 1:].iterrows():
        name = row.iloc[0]
        if pd.isna(name):
            continue
        pid = id_by_name.get(norm(name))
        if not pid:
            continue  # skips six regional subtotal rows

        for col_idx, year in year_cols.items():
            value = row.iloc[col_idx]

            # Bỏ qua giá trị thiếu của NSO: NaN, "..", "-", ...
            if pd.isna(value):
                continue

            value_str = str(value).strip()
            if value_str in ["..", ".", "-", "—", "", "NA", "N/A"]:
                continue

            try:
                numeric_value = float(value_str.replace(",", ""))
            except (ValueError, TypeError):
                print(
                    f"[WARNING] Bỏ qua giá trị không phải số: "
                    f"{path.name} | {name} | {year} | {value}"
                )
                continue

            long_rows.append({
                "province_id_old": pid,
                "year": year,
                value_col: numeric_value,
            })

    frame = pd.DataFrame(long_rows)
    if frame.empty or frame.province_id_old.nunique() != 63:
        raise ValueError(
            f"{path.name}: kỳ vọng 63 tỉnh; nhận được "
            f"{frame.province_id_old.nunique() if not frame.empty else 0}."
        )
    if frame.duplicated(["province_id_old", "year"]).any():
        raise ValueError(f"{path.name}: trùng khóa tỉnh-năm.")
    return frame

def inspect_all(session: requests.Session, cw: pd.DataFrame) -> dict[str, Any]:
    summary = {}
    RAW.mkdir(parents=True, exist_ok=True)
    for key, endpoint in TABLES.items():
        print(f"\n[METADATA] {key}: {endpoint}")
        meta = get_metadata(session, endpoint)
        (RAW / f"{key}_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        pinfo, yinfo, extra = identify_dimensions(meta, cw, key)
        ymap = years_from_meta(yinfo)
        print("  province dimension:", pinfo[0].get("code"), "matched", len([1 for _, label in pinfo[1] if norm(label) in set(cw.name_key)]), "/63")
        print("  year dimension:", yinfo[0].get("code"), "years:", sorted(ymap))
        for var in extra:
            print("  extra dimension:", var.get("code"), "=>", [label for _, label in get_var_values(var)])
        summary[key] = {"years": sorted(ymap), "endpoint": endpoint}
    years = sorted(set.intersection(*[set(v["years"]) for v in summary.values()]))
    print("\nIntersection years across API tables:", years)
    return {"tables": summary, "common_years": years}



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import NSO Excel workbooks → outcomes_panel_63.csv"
    )
    parser.add_argument("--download", action="store_true",
                        help="Import dữ liệu từ 5 file Excel NSO có sẵn.")
    parser.add_argument("--start-year", type=int, default=2018)
    parser.add_argument("--end-year", type=int, default=2024)

    parser.add_argument("--firms-new-file", default="data/raw/gso/V05.02.xlsx")
    parser.add_argument("--firms-active-file", default="data/raw/gso/V05.04.xlsx")
    parser.add_argument("--pop-file", default="data/raw/gso/V02.03-07.xlsx")
    parser.add_argument("--grdp-pc-file", default="data/raw/gso/V03.12.xlsx")
    parser.add_argument("--grdp-growth-file", default="data/raw/gso/V03.10.xlsx")

    args = parser.parse_args()

    if not args.download:
        parser.error("Hãy chạy với tham số --download để import dữ liệu Excel.")

    RAW.mkdir(parents=True, exist_ok=True)

    # 1. Load crosswalk 63 tỉnh
    cw = load_crosswalk()
    print(f"[OK] Crosswalk: {len(cw)} tỉnh")

    # 2. Import 5 NSO Excel workbooks
    files = {
        "firms_new": args.firms_new_file,
        "firms_active": args.firms_active_file,
        "pop": args.pop_file,
        "grdp_pc": args.grdp_pc_file,
        "grdp_growth_index": args.grdp_growth_file,
    }

    downloads = {}

    for key, filename in files.items():
        path = ROOT / filename
        print(f"\n[IMPORT] {key}: {path.name}")

        frame = import_wide_nso_excel(path, key, cw)

        # Giới hạn khoảng năm cần đưa vào panel
        frame = frame[
            frame["year"].between(args.start_year, args.end_year)
        ].copy()

        if frame.empty:
            raise ValueError(
                f"{path.name}: không có dữ liệu trong khoảng "
                f"{args.start_year}-{args.end_year}"
            )

        if frame.duplicated(["province_id_old", "year"]).any():
            raise ValueError(f"{path.name}: trùng khóa tỉnh-năm.")

        downloads[key] = frame

        frame.to_csv(
            RAW / f"{key}_63_long.csv",
            index=False,
            encoding="utf-8-sig"
        )

        print(
            f"  Rows: {len(frame)} | "
            f"Provinces: {frame['province_id_old'].nunique()} | "
            f"Years: {sorted(frame['year'].unique().tolist())}"
        )

    # 3. Merge 5 datasets theo province_id_old và year
    merged = downloads["firms_new"]

    for key in [
        "firms_active",
        "pop",
        "grdp_pc",
        "grdp_growth_index",
    ]:
        merged = merged.merge(
            downloads[key],
            on=["province_id_old", "year"],
            how="outer",
            validate="one_to_one"
        )

    merged["grdp_pc_price_basis"] = "as_reported_by_nso"
    merged["source_note"] = (
        "NSO Excel workbooks: V05.02, V05.04, "
        "V02.03-07, V03.12, V03.10"
    )
    merged["source_access_date"] = date.today().isoformat()

    merged = merged.sort_values(
        ["province_id_old", "year"]
    ).reset_index(drop=True)

    if merged.duplicated(["province_id_old", "year"]).any():
        raise ValueError("Bảng hợp nhất bị trùng khóa tỉnh-năm.")

    # 4. Save raw merged dataset
    merged.to_csv(
        RAW / "nso_outcomes_63_long.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # 5. Update existing outcomes panel, preserving its existing rows
    if OUTCOMES.exists():
        existing = pd.read_csv(
            OUTCOMES,
            dtype={"province_id_old": "string"},
            encoding="utf-8-sig"
        )

        merged["province_id_old"] = merged["province_id_old"].astype("string")
        existing["province_id_old"] = existing["province_id_old"].astype("string")

        key_cols = ["province_id_old", "year"]
        update_cols = [
            "firms_new",
            "firms_active",
            "pop",
            "grdp_pc",
            "grdp_growth_index",
            "grdp_pc_price_basis",
            "source_note",
            "source_access_date",
        ]

        # Chỉ bổ sung các cột chưa có trong panel hiện tại
        for col in update_cols:
            if col not in existing.columns:
                existing[col] = np.nan

        # Tạo bảng dữ liệu mới để cập nhật theo khóa
        update_data = merged[key_cols + update_cols].copy()

        existing = existing.merge(
            update_data,
            on=key_cols,
            how="left",
            suffixes=("", "_new"),
            validate="one_to_one"
        )

        # Giá trị mới được ưu tiên; nếu thiếu thì giữ giá trị cũ
        for col in update_cols:
            new_col = f"{col}_new"
            existing[col] = existing[new_col].combine_first(existing[col])
            existing.drop(columns=[new_col], inplace=True)

        existing.to_csv(
            OUTCOMES,
            index=False,
            encoding="utf-8-sig"
        )

        print(f"\n[OK] Đã cập nhật panel: {OUTCOMES}")
        print(f"  Total rows: {len(existing)}")

    else:
        output_path = DATA / "outcomes_panel_63_nso.csv"
        merged.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig"
        )
        print(f"\n[OK] Đã tạo panel mới: {output_path}")

    # 6. Generate coverage report
    coverage = merged.groupby("year").agg(
        provinces=("province_id_old", "nunique"),
        firms_new_nonmissing=("firms_new", "count"),
        firms_active_nonmissing=("firms_active", "count"),
        pop_nonmissing=("pop", "count"),
        grdp_pc_nonmissing=("grdp_pc", "count"),
        grdp_growth_nonmissing=("grdp_growth_index", "count"),
    ).reset_index()

    coverage.to_csv(
        RAW / "stage3_coverage_report.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\n========== COVERAGE REPORT ==========")
    print(coverage.to_string(index=False))

    print("\n[COMPLETED] Stage 3 Excel import finished.")
    print("Source folder:", RAW)
    print("No API requests were made.")

if __name__ == "__main__":
    main()