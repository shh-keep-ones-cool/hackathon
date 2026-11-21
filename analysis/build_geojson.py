"""Build data/vn_provinces.geojson (34 provinces, EPSG:4326) with province_id matching pci_provinces.csv."""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Alias đã xác minh theo mã OCHA (adm1_pcode) cho các tên hay lệch giữa nguồn
ALIASES = {
    "VN46": ["hue", "thua-thien-hue"],
    "VN79": ["ho-chi-minh-city", "ho-chi-minh", "tp-ho-chi-minh", "tphcm"],
}


def slug(value) -> str:
    s = str(value or "").strip().lower().replace("đ", "d")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def candidates(row, name_field: str) -> list[str]:
    out = []
    for field in (name_field, "adm1_name", "adm1_name1"):
        if field in row and row[field]:
            raw = str(row[field])
            out.append(slug(raw))
            out.append(slug(re.sub(r"\s+city$", "", raw, flags=re.I)))
            out.append(slug(re.sub(r"^TP\.?\s*", "", raw, flags=re.I)))
    out += ALIASES.get(str(row.get("adm1_pcode")), [])
    seen, uniq = set(), []
    for c in out:
        if c and c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--name-field", default="adm1_name1")
    ap.add_argument("--output", default=str(DATA / "vn_provinces.geojson"))
    ap.add_argument("--simplify", type=float, default=0.004,
                    help="Dung sai đơn giản hóa (độ). 0 = tắt.")
    args = ap.parse_args()

    prov = pd.read_csv(DATA / "pci_provinces.csv", encoding="utf-8-sig", dtype={"province_id": str})
    ids = set(prov["province_id"])
    if len(ids) != 34:
        raise ValueError(f"pci_provinces.csv cần 34 province_id duy nhất; hiện có {len(ids)}")

    gdf = gpd.read_file(args.input)
    if len(gdf) != 34:
        raise ValueError(f"GeoJSON có {len(gdf)} feature, cần đúng 34 (ranh giới sau 01/07/2025).")
    if args.name_field not in gdf.columns:
        raise ValueError(f"Không có field '{args.name_field}'. Các field: {gdf.columns.tolist()}")

    gdf = gdf.to_crs(4326)

    matched, unmatched = [], []
    for _, row in gdf.iterrows():
        hit = next((c for c in candidates(row, args.name_field) if c in ids), None)
        if hit:
            matched.append(hit)
        else:
            matched.append(None)
            unmatched.append((row[args.name_field], candidates(row, args.name_field)))
    gdf["province_id"] = matched

    if unmatched:
        print("Feature KHÔNG khớp province_id nào trong CSV:")
        for name, cands in unmatched:
            print("  ", name, "-> thử:", cands)
        print("province_id trong CSV chưa được dùng:", sorted(ids - set(m for m in matched if m)))
        raise SystemExit("Thêm alias vào ALIASES (theo adm1_pcode) rồi chạy lại.")

    if gdf["province_id"].duplicated().any() or set(gdf["province_id"]) != ids:
        raise ValueError("province_id trong GeoJSON không khớp 1-1 với CSV.")

    name_col = args.name_field
    out = gdf[["province_id", name_col, "adm1_pcode", "geometry"]].rename(
        columns={name_col: "province_name", "adm1_pcode": "pcode"})

    if args.simplify > 0:
        out["geometry"] = out.geometry.simplify(args.simplify, preserve_topology=True)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    try:
        out.to_file(args.output, driver="GeoJSON", COORDINATE_PRECISION=4)
    except Exception:
        out.to_file(args.output, driver="GeoJSON")

    size_mb = Path(args.output).stat().st_size / 1e6
    print(f"[OK] {args.output}: {len(out)} features, EPSG:4326, {size_mb:.2f} MB")


if __name__ == "__main__":
    main()