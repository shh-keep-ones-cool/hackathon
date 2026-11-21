"""Merge a manually exported, source-documented GSO 34-province 2025 CSV into PCI 2025.
Input format is data/raw/gso/gso_34_2025_template.csv; keep all units and price bases explicit.
"""
import pandas as pd
from common import ROOT, DATA, normalize_name

def main():
    src=DATA/'raw/gso/gso_34_2025.csv'
    if not src.exists(): raise SystemExit('Chưa có data/raw/gso/gso_34_2025.csv. Copy template, điền số từ NSO và giữ source_url/source_table.')
    g=pd.read_csv(src,encoding='utf-8-sig')
    base=pd.read_csv(DATA/'pci_provinces.csv',encoding='utf-8-sig')
    g['name_key']=g['province_name'].map(normalize_name); base['name_key']=base['province_name'].map(normalize_name)
    rename={'pop_thousand':'pop','grdp_billion_vnd':'grdp'}
    g=g.rename(columns=rename)
    cols=['name_key']+[c for c in ['pop','grdp','grdp_price_basis','firms_new','firms_active','fdi_pc','public_invest_pc','budget_revenue_pc','pm25_mean'] if c in g.columns]
    out=base.drop(columns=[c for c in cols if c!='name_key' and c in base.columns],errors='ignore').merge(g[cols],on='name_key',how='left',validate='one_to_one').drop(columns='name_key')
    if len(out)!=34 or out['province_id'].nunique()!=34: raise ValueError('Kết quả không còn đúng 34 tỉnh duy nhất')
    out.to_csv(DATA/'pci_provinces.csv',index=False,encoding='utf-8-sig')
    print('Đã merge GSO; số liệu thiếu tiếp tục để NA, không nội suy.')
if __name__=='__main__': main()
