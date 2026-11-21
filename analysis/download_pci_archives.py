"""Download VCCI's historical PCI workbooks exposed on its PCI-data archive page."""
from pathlib import Path
import re, requests
from bs4 import BeautifulSoup
from common import ROOT
URL='https://pcivietnam.vn/en/pci-data'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; academic-data-project/1.0)'}

def main():
    out=ROOT/'data/raw/pci'; out.mkdir(parents=True,exist_ok=True)
    html=requests.get(URL,headers=HEADERS,timeout=45); html.raise_for_status()
    soup=BeautifulSoup(html.text,'lxml')
    found={}
    for tr in soup.find_all('tr'):
        text=tr.get_text(' ',strip=True)
        m=re.search(r'Data PCI\s+(20\d{2})',text,re.I)
        if not m: m=re.search(r'Dữ liệu PCI\s+(20\d{2})',text,re.I)
        if not m: continue
        y=int(m.group(1)); a=tr.find('a',href=True)
        if a: found[y]=requests.compat.urljoin(URL,a['href'])
    if not found:
        raise SystemExit('Không đọc được link trong bảng archive; mở trang VCCI và tải thủ công, sau đó đặt file tên PCI_YYYY.xlsx vào data/raw/pci/.')
    for y,url in sorted(found.items()):
        ext='.xls' if url.lower().split('?')[0].endswith('.xls') else '.xlsx'
        target=out/f'PCI_{y}{ext}'
        if target.exists(): print('Skip',target.name); continue
        r=requests.get(url,headers=HEADERS,timeout=90); r.raise_for_status()
        target.write_bytes(r.content)
        print('Downloaded',y,target.name,len(r.content),'bytes')
    print('Tải xong. Không đưa file raw của VCCI lên GitHub công khai nếu chưa rà soát quyền sử dụng.')
if __name__=='__main__': main()
