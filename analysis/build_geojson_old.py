"""Normalize a 2025 administrative-level-1 GeoJSON to the project's 34 stable IDs.
Download a 34-province GeoJSON (valid from 2025-07-01) separately, then pass --input.
"""
import argparse, json, re, unicodedata
import pandas as pd
import geopandas as gpd
from common import ROOT, DATA, normalize_name

ALIASES={
 'hochiminhcity':'tphochiminh','ho chi minh city':'tphochiminh','hochiminh':'tphochiminh','hcmc':'tphochiminh','tp hochiminh':'tphochiminh',
 'thua thien hue':'hue','hue city':'hue','hue':'hue',
 'dak lak':'daklak','daklak':'daklak','dak nong':'daknong','bac kan':'backan','bac kạn':'backan',
 'ba ria vung tau':'bariavungtau','baria vungtau':'bariavungtau'
}
def key(s):
    v=normalize_name(s)
    return ALIASES.get(v,v)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,help='GeoJSON/shapefile downloaded from OCHA/HDX or another documented source')
    p.add_argument('--name-field',default='',help='Property containing province name; auto-detect if omitted')
    a=p.parse_args()
    src=gpd.read_file(a.input)
    candidates=[a.name_field] if a.name_field else ['name','NAME_1','shapeName','admin1Name','ADM1_EN','province','ten_tinh','Tinh','NAME']
    namecol=next((c for c in candidates if c and c in src.columns),None)
    if not namecol: raise SystemExit(f'Không tìm được field tên tỉnh. Các field hiện có: {list(src.columns)}. Chạy lại với --name-field.')
    prov=pd.read_csv(DATA/'pci_provinces.csv',encoding='utf-8-sig')
    name_to_id={key(r.province_name):r.province_id for r in prov.itertuples()}
    src['province_id']=src[namecol].astype(str).map(key).map(name_to_id)
    missing=src.loc[src['province_id'].isna(),namecol].astype(str).tolist()
    if missing: raise ValueError(f'Tên địa phương chưa map được: {missing}. Thêm alias đã xác minh vào ALIASES.')
    if src['province_id'].duplicated().any(): raise ValueError('GeoJSON có nhiều feature cho cùng tỉnh; cần dissolve theo province_id trước khi xuất.')
    src=src.merge(prov[['province_id','province_name']],on='province_id',how='left',validate='one_to_one')
    if len(src)!=34 or src['province_id'].nunique()!=34: raise ValueError(f'GeoJSON cần đúng 34 feature, hiện có {len(src)}')
    out=DATA/'vn_provinces.geojson'
    src=src.to_crs('EPSG:4326')
    src.to_file(out,driver='GeoJSON',encoding='utf-8')
    print(f'Wrote {out} ({len(src)} features, CRS EPSG:4326)')
if __name__=='__main__': main()
