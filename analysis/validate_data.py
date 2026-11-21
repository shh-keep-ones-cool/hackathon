"""Run deterministic structure, key, crosswalk, GeoJSON and unit checks."""
import json, sys
import pandas as pd
from common import DATA

def check(condition,msg):
    if not condition: raise AssertionError(msg)
    print('PASS -',msg)

def main():
    p=pd.read_csv(DATA/'pci_provinces.csv',encoding='utf-8-sig')
    check(len(p)==34,'PCI 2025 has 34 rows')
    check(p.province_id.notna().all() and p.province_id.is_unique,'province_id non-null and unique')
    score=[f'pci_s{i}' for i in range(1,10)]
    check(p[score].notna().all().all(),'9 PCI subindices are filled for all 34 provinces')
    check(p[score].apply(lambda s:s.between(0,10).all()).all(),'PCI subindex values are in [0,10]')
    cw=pd.read_csv(DATA/'crosswalk_63_to_34.csv',encoding='utf-8-sig')
    check(len(cw)==63,'crosswalk has 63 old province rows')
    check(cw.old_province_id.nunique()==63,'63 old IDs are unique')
    sh=pd.to_numeric(cw.share,errors='coerce')
    check(sh.notna().all() and sh.between(0,1).all(),'crosswalk shares are numeric in [0,1]')
    check(((cw.assign(share=sh).groupby('old_province_id').share.sum()-1).abs()<1e-9).all(),'share sums to 1 for every old province')
    check(cw.new_province_id.nunique()==34,'crosswalk maps to 34 new provinces')
    for fn, key in [('pci_panel_63.csv','province_id_old'),('outcomes_panel_63.csv','province_id_old')]:
        df=pd.read_csv(DATA/fn,encoding='utf-8-sig')
        check({key,'year'}.issubset(df.columns),f'{fn} has required keys')
        check(not df.duplicated([key,'year']).any(),f'{fn} has no duplicate province-year keys')
    geo=DATA/'vn_provinces.geojson'
    if geo.exists():
        gj=json.loads(geo.read_text(encoding='utf-8'))
        features=gj.get('features',[])
        ids=[ft.get('properties',{}).get('province_id') for ft in features]
        check(len(features)==34,'GeoJSON has 34 features')
        check(all(ids) and len(set(ids))==34,'GeoJSON province_id populated and unique')
    else: print('WARN - GeoJSON chưa được tạo; chạy build_geojson.py')
    print('Validation completed.')
if __name__=='__main__': main()
