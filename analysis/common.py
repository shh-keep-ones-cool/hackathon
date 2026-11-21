from __future__ import annotations
import re, unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def normalize_name(value: object) -> str:
    s = str(value or '').strip().lower().replace('đ','d')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'^(tinh|thanh pho|tp\.?|province of|province|city of)\s+', '', s)
    s = re.sub(r'[^a-z0-9]+', '', s)
    aliases = {
        'hochiminh':'tphochiminh','thanhphohochiminh':'tphochiminh','hcm':'tphochiminh','tphcm':'tphochiminh','tphochiminh':'tphochiminh','hcmc':'tphochiminh','hochiminhcity':'tphochiminh',
        'thua thien hue':'hue','thuathienhue':'hue','huecity':'hue',
        'baria-vungtau':'bariavungtau','bariavungtau':'bariavungtau',
        'daklak':'daklak','daknong':'daknong','bac kan':'backan','backan':'backan',
        'baoloc':'baoloc'
    }
    return aliases.get(s, s)

def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={'province_id':'string','province_id_old':'string','old_province_id':'string','new_province_id':'string'}, encoding='utf-8-sig')
