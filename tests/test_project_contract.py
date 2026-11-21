from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def test_34_pci_rows_and_scores():
    d=pd.read_csv(ROOT/'data/pci_provinces.csv',encoding='utf-8-sig')
    assert len(d)==34 and d.province_id.nunique()==34
    assert d[[f'pci_s{i}' for i in range(1,10)]].notna().all().all()
def test_crosswalk_63_to_34():
    d=pd.read_csv(ROOT/'data/crosswalk_63_to_34.csv',encoding='utf-8-sig')
    assert len(d)==63 and d.old_province_id.nunique()==63 and d.new_province_id.nunique()==34
    assert (d.groupby('old_province_id').share.sum().sub(1).abs()<1e-9).all()
def test_no_hardcoded_total_score():
    d=pd.read_csv(ROOT/'data/pci_provinces.csv',encoding='utf-8-sig')
    assert d.pci_total.isna().all()
