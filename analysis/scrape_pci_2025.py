"""Scrape the published 34-province PCI 2025 table from VCCI's PCI 2.0 report page.
The official XLSX link is also downloaded to data/raw/pci for a local audit trail.
"""
from pathlib import Path
import argparse, re, sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
from common import ROOT, DATA, normalize_name

URL = 'https://pcivietnam.vn/report-2025'
XLSX_URL = 'https://pcivietnam.vn/data_pci_file/general_file/1778745497-06.%20Du%20lieu%20PCI%202025.xlsx'
HEADERS = {'User-Agent':'Mozilla/5.0 (compatible; academic-data-project/1.0)'}

def scrape_tables(html: str):
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('table')
    if not tables:
        raise RuntimeError('Không tìm thấy HTML table. VCCI có thể đã đổi cấu trúc trang; hãy dùng XLSX tải thủ công.')
    candidates=[]
    for table in tables:
        rows=[]
        for tr in table.find_all('tr'):
            cells=[c.get_text(' ',strip=True) for c in tr.find_all(['th','td'])]
            if cells: rows.append(cells)
        if not rows: continue
        # Select the 10-column table with province name + 9 index score columns.
        if any('Gia nhập' in ' '.join(r) or 'Gia nhap' in ' '.join(r) for r in rows[:3]) or max(map(len,rows)) >= 10:
            candidates.append(rows)
    for rows in candidates:
        data=[]
        for row in rows:
            if len(row) < 10: continue
            vals=row[:10]
            if re.search(r'\d', vals[1]):
                try:
                    numbers=[float(x.replace(',','.')) for x in vals[1:10]]
                    data.append([vals[0],*numbers])
                except ValueError:
                    continue
        if len(data)==34:
            return pd.DataFrame(data,columns=['province_name']+[f'pci_s{i}' for i in range(1,10)])
    # pd.read_html fallback is useful when table header markup is unusual.
    try:
        for df in pd.read_html(html):
            if df.shape[1] >= 10:
                tmp=df.iloc[:, :10].copy(); tmp.columns=['province_name']+[f'pci_s{i}' for i in range(1,10)]
                tmp['province_name']=tmp['province_name'].astype(str)
                for c in tmp.columns[1:]: tmp[c]=pd.to_numeric(tmp[c],errors='coerce')
                tmp=tmp.dropna(subset=['pci_s1'])
                if len(tmp)==34: return tmp
    except Exception:
        pass
    raise RuntimeError('Không đọc được đủ 34 dòng PCI. Kiểm tra trang nguồn hoặc dùng file XLSX đã tải.')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--skip-xlsx',action='store_true',help='Bỏ qua tải XLSX, chỉ cào bảng HTML')
    args=p.parse_args()
    r=requests.get(URL,headers=HEADERS,timeout=45); r.raise_for_status()
    raw=DATA/'raw/pci'; raw.mkdir(parents=True,exist_ok=True)
    (raw/'pci_2025_source.html').write_bytes(r.content)
    if not args.skip_xlsx:
        try:
            x=requests.get(XLSX_URL,headers=HEADERS,timeout=90); x.raise_for_status()
            if not x.content.startswith(b'PK'):
                raise RuntimeError('URL không trả về XLSX hợp lệ')
            (raw/'pci_2025_official.xlsx').write_bytes(x.content)
            print('Đã lưu XLSX nguồn tại data/raw/pci/pci_2025_official.xlsx')
        except Exception as e:
            print(f'Cảnh báo: không tải được XLSX ({e}); dùng bảng công bố trên website.',file=sys.stderr)
    scraped=scrape_tables(r.text)
    base=pd.read_csv(DATA/'pci_provinces.csv',encoding='utf-8-sig')
    scraped['name_key']=scraped['province_name'].map(normalize_name)
    base['name_key']=base['province_name'].map(normalize_name)
    merged=base.drop(columns=[c for c in scraped.columns if c in base.columns and c!='name_key'],errors='ignore').merge(scraped.drop(columns='province_name'),on='name_key',how='left',validate='one_to_one')
    if merged[[f'pci_s{i}' for i in range(1,10)]].isna().any().any():
        missing=merged.loc[merged['pci_s1'].isna(),'province_name'].tolist()
        raise RuntimeError(f'Thiếu tỉnh khi nối tên: {missing}. Không ghi đè CSV.')
    merged=merged.drop(columns='name_key')
    merged.to_csv(DATA/'pci_provinces.csv',index=False,encoding='utf-8-sig')
    print(f'Đã cập nhật {len(merged)} tỉnh vào data/pci_provinces.csv. pci_total và các biến GSO giữ NA nếu nguồn chưa cung cấp.')

if __name__=='__main__': main()
