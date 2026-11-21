"""Fail if any L1..L12 item in docs/LIMITATIONS.md is missing from dashboard.html."""
import re,pathlib,sys
R=pathlib.Path(__file__).resolve().parent.parent
md=(R/'docs/LIMITATIONS.md').read_text(encoding='utf-8'); html=(R/'dashboard.html').read_text(encoding='utf-8')
ids=re.findall(r'^\*\*(L\d+)\.',md,re.M); miss=[i for i in ids if f'id="{i.lower()}"' not in html]
print(len(ids),'limitations in LIMITATIONS.md; missing from page:',miss); sys.exit(1 if miss or len(ids)<12 else 0)
