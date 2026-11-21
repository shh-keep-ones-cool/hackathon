"""Build dashboard.html: embeds data/*.csv verbatim (so every number is traceable), a display-simplified GeoJSON, and analysis/dashboard_core.js."""
import json, hashlib, pathlib, pandas as pd, math
R=pathlib.Path(__file__).resolve().parent.parent; D=R/'data'; A=R/'analysis'
FILES=['pci_provinces','outcomes_34_rebuilt','bridge_groups','pci_subindex_meta','pci_groups_34_panel','model_results','pci_bpi_2025','bootstrap_results']
def rdp(pts,eps):                                   # Ramer-Douglas-Peucker, iterative
    keep=[False]*len(pts); keep[0]=keep[-1]=True; stack=[(0,len(pts)-1)]
    while stack:
        a,b=stack.pop(); (x1,y1),(x2,y2)=pts[a],pts[b]; dx,dy=x2-x1,y2-y1; L=math.hypot(dx,dy) or 1e-12; dm,im=0,None
        for i in range(a+1,b):
            d=abs(dy*pts[i][0]-dx*pts[i][1]+x2*y1-y2*x1)/L
            if d>dm: dm,im=d,i
        if dm>eps: keep[im]=True; stack+= [(a,im),(im,b)]
    return [p for p,k in zip(pts,keep) if k]
def rdp_ring(r,eps):                                # closed rings (first == last) have a zero-length baseline, so split at the midpoint first
    pts=[tuple(p) for p in r]
    if pts[0]!=pts[-1]: return rdp(pts,eps)
    h=len(pts)//2; return rdp(pts[:h+1],eps)[:-1]+rdp(pts[h:],eps)
def area(r): return abs(sum(r[i][0]*r[(i+1)%len(r)][1]-r[(i+1)%len(r)][0]*r[i][1] for i in range(len(r))))/2
EPS=0.012; MINAREA=0.0004                           # degrees; display only
g=json.load(open(D/'vn_provinces.geojson',encoding='utf-8')); feats=[]; n0=n1=0
for f in g['features']:
    c=f['geometry']['coordinates']; polys=c if f['geometry']['type']=='MultiPolygon' else [c]; out=[]
    for poly in polys:
        rings=[]
        for k,r in enumerate(poly):
            n0+=len(r)
            if area(r)<MINAREA and not (k==0 and len(polys)==1): continue
            s=rdp_ring(r,EPS)
            if len(s)>=4: rings.append([[round(x,3),round(y,3)] for x,y in s]); n1+=len(s)
        if rings: out.append(rings)
    feats.append({'properties':{'province_id':f['properties']['province_id']},'geometry':{'coordinates':out}})
print(f'geometry points {n0} -> {n1} (tolerance {EPS} deg, rings < {MINAREA} deg2 dropped)')
rd=lambda n:pd.read_csv(D/f'{n}.csv',encoding='utf-8-sig')
bpi=rd('pci_bpi_2025'); o63=rd('outcomes_panel_63'); cw=rd('crosswalk_63_to_34')
meta=dict(bpi_source=bpi.source.iloc[0],bpi_date=str(bpi.source_date.iloc[0]),nso_note=o63.source_note.dropna().iloc[0],nso_date=str(o63.source_access_date.dropna().max()),
          crosswalk_note=cw.note.iloc[0].split(';')[0],trend='2015\u20132017 \u2192 2022\u20132024',
          files=[[f'data/{n}.csv',hashlib.sha256((D/f'{n}.csv').read_bytes()).hexdigest()[:8]] for n in FILES])
blocks='\n'.join(f'<script type="text/csv" id="csv-{n}">{(D/f"{n}.csv").read_text(encoding="utf-8-sig")}</script>' for n in FILES)
html=(A/'dashboard_template.html').read_text(encoding='utf-8').replace('{{CSV_BLOCKS}}',blocks).replace('{{GEO}}',json.dumps({'features':feats},separators=(',',':'))).replace('{{META}}',json.dumps(meta,ensure_ascii=False)).replace('{{CORE}}',(A/'dashboard_core.js').read_text(encoding='utf-8'))
(R/'dashboard.html').write_text(html,encoding='utf-8'); print('dashboard.html',round(len(html)/1024),'KB'); print(meta)
