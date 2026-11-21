"""Import year-specific VCCI PCI workbooks using a reviewed column-map CSV.
Because historical XLS/XLSX layouts and index availability change by year, this script
requires an explicit mapping instead of guessing columns or treating frameworks as identical.
"""
from pathlib import Path
import argparse
import pandas as pd
from common import ROOT, DATA, normalize_name

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--map',default='config/pci_historical_column_map_template.csv')
    args=p.parse_args()
    mp=pd.read_csv(ROOT/args.map,encoding='utf-8-sig').fillna('')
    cw=pd.read_csv(DATA/'crosswalk_63_to_34.csv',encoding='utf-8-sig')
    name_to_id={normalize_name(r.old_province_name):r.old_province_id for r in cw.itertuples()}
    outputs=[]
    for row in mp.itertuples(index=False):
        year=int(row.year); source=str(row.source_file).strip(); sheet=str(row.sheet_name).strip(); pcol=str(row.province_column).strip()
        if not source or not sheet or not pcol:
            print(f'SKIP {year}: cần điền source_file, sheet_name, province_column trong mapping')
            continue
        path=ROOT/source
        if not path.exists(): print(f'SKIP {year}: không tìm thấy {path}'); continue
        df=pd.read_excel(path,sheet_name=sheet)
        if pcol not in df.columns: raise KeyError(f'{year}: không có cột tỉnh {pcol!r}; headers={list(df.columns)}')
        df['province_id_old']=df[pcol].map(normalize_name).map(name_to_id)
        df=df.dropna(subset=['province_id_old']).copy()
        item={'province_id_old':'','year':year,'framework_version':str(row.framework_version or f'PCI_legacy_{year}'),'n_surveyed_firms':''}
        ncol=str(row.surveyed_firms_column).strip()
        if ncol and ncol in df.columns: df['n_surveyed_firms']=pd.to_numeric(df[ncol],errors='coerce')
        for i in range(1,11):
            col=str(getattr(row,f'source_col_pci_old_{i}')).strip()
            df[f'pci_old_{i}']=pd.to_numeric(df[col],errors='coerce') if col and col in df.columns else pd.NA
        keep=['province_id_old']+[f'pci_old_{i}' for i in range(1,11)]
        if 'n_surveyed_firms' in df: keep.append('n_surveyed_firms')
        out=df[keep].drop_duplicates('province_id_old').copy()
        out['year']=year; out['framework_version']=item['framework_version']
        if 'n_surveyed_firms' not in out: out['n_surveyed_firms']=pd.NA
        outputs.append(out[['province_id_old','year','framework_version','n_surveyed_firms']+[f'pci_old_{i}' for i in range(1,11)]])
        print(f'Imported {year}: {len(out)} province records')
    if outputs:
        result=pd.concat(outputs,ignore_index=True)
        result.to_csv(DATA/'pci_panel_63.csv',index=False,encoding='utf-8-sig')
        print('Wrote data/pci_panel_63.csv')
    else:
        print('Không có năm nào được nhập. Chỉ cập nhật file khi column-map đã được kiểm tra.')
if __name__=='__main__': main()
