"""Bootstrap intervals for the dashboard scenario (Stage 5). Writes data/bootstrap_results.csv.
Cluster (province) bootstrap, percentile 95% intervals, B=2000, fixed seed. Point estimates are re-derived here and checked
against data/model_results.csv (Stage 2 specification) before anything is written; the script stops if they differ.
 boot_2025 : OLS of new firms per 1000 residents (2025 file) on the group score (SD of the 34 provinces), raw units; controls none | lnGRDPpc+coastal
 boot_panel: two-way FE (province + year) of ln(new firms per 1000) at t+k on the weighted group score (within-year z over 34), k=1..3
Samples: all (34) and excl_HCMC_HN (32)."""
import pathlib, numpy as np, pandas as pd
R=pathlib.Path(__file__).resolve().parent.parent; D=R/'data'
B=2000; SEED=20261121; TOP2=['ha-noi','tp-ho-chi-minh']
rd=lambda n:pd.read_csv(D/f'{n}.csv',encoding='utf-8-sig')
P=rd('pci_provinces'); O=rd('outcomes_34_rebuilt'); BR=rd('bridge_groups'); PAN=rd('pci_groups_34_panel'); MR=rd('model_results')
ids=list(P.province_id); zs=lambda a:(a-a.mean())/a.std(ddof=1)
cols=sorted({c for s in BR.new_cols for c in s.split('+')}); subz={c:zs(P[c]) for c in cols}
zg={r.group_id:zs(sum(subz[c] for c in r.new_cols.split('+'))/len(r.new_cols.split('+'))) for r in BR.itertuples()}   # same maths as dashboard_core.js
o24=O[O.year==2024].set_index('province_id').loc[ids]; lninc=np.log(o24.grdp/o24['pop']).values; coast=P.coastal.values.astype(float)
y25=(P.firms_new/P['pop']).values
rng=np.random.default_rng(SEED); out=[]
def add(block,outcome,controls,sample,n,g,vals,pt):
    out.append(dict(block=block,outcome=outcome,controls=controls,sample=sample,n=n,row=g,col='-',stat='coef',value=pt))
    for st,v in (('ci_low',np.percentile(vals,2.5)),('ci_high',np.percentile(vals,97.5)),('boot_share_pos',(vals>0).mean()),('boot_B',len(vals))):
        out.append(dict(block=block,outcome=outcome,controls=controls,sample=sample,n=n,row=g,col='-',stat=st,value=v))
def ols_slope(X,y):
    b,*_=np.linalg.lstsq(X,y,rcond=None); return b[1]
# ---- 2025 cross-section
for sample in ('all','excl_HCMC_HN'):
    keep=np.array([i not in TOP2 for i in ids]) if sample!='all' else np.ones(len(ids),bool); n=int(keep.sum())
    for ctl in ('none','lnGRDPpc+coastal'):
        for g in zg:
            x=zg[g].values[keep]; ex=[np.ones(n),x]+([lninc[keep],coast[keep]] if ctl!='none' else []); X=np.column_stack(ex); y=y25[keep]
            pt=ols_slope(X,y); bs=[]
            for _ in range(B):
                ix=rng.integers(0,n,n); Xb=X[ix]
                if np.linalg.matrix_rank(Xb)<X.shape[1]: continue
                bs.append(ols_slope(Xb,y[ix]))
            add('boot_2025','firms_new_per1000',ctl,sample,n,g,np.array(bs),pt)
# ---- panel FE
def twfe(X,Y):                                       # balanced panel arrays [province, year]
    f=lambda A:A-A.mean(1,keepdims=True)-A.mean(0,keepdims=True)+A.mean()
    xd,yd=f(X),f(Y); return (xd*yd).sum()/(xd**2).sum()
for sample in ('all','excl_HCMC_HN'):
    pids=[i for i in ids if sample=='all' or i not in TOP2]
    for k in (1,2,3):
        o=O[['province_id','year','firms_new_per_1000']].assign(year=lambda d:d.year-k); o['y']=np.log(o.firms_new_per_1000)
        for g in zg:
            d=PAN[PAN.province_id.isin(pids)][['province_id','year',g+'_w_z34']].merge(o[['province_id','year','y']],on=['province_id','year']).dropna()
            X=d.pivot(index='province_id',columns='year',values=g+'_w_z34').loc[pids]; Y=d.pivot(index='province_id',columns='year',values='y').loc[pids]
            assert not X.isna().any().any() and not Y.isna().any().any(), 'panel must be balanced'
            X,Y=X.values,Y.values; pt=twfe(X,Y); n=len(pids)
            bs=np.array([twfe(X[ix],Y[ix]) for ix in (rng.integers(0,n,n) for _ in range(B))])
            add('boot_panel',f'ln_firms_new_per1000_t+{k}','weighted',sample,X.size,g,bs,pt)
res=pd.DataFrame(out)
# ---- reproduce Stage 2 before writing
mr={(a,b,c,d,e,f):v for a,b,c,d,e,f,v in zip(MR.block,MR.outcome,MR.controls,MR['sample'],MR.row,MR.stat,MR.value)}; bad=0
for r in res[(res.block=='boot_panel')&(res.stat=='coef')].itertuples():
    ref=mr[('panel_fe',r.outcome,r.controls,getattr(r,'sample'),r.row,'coef')]; bad+=int(abs(ref-r.value)>1e-9)
sd34={c:P[c].std(ddof=1) for c in cols}
for r in res[(res.block=='boot_2025')&(res.stat=='coef')&(res.controls=='none')&res.row.isin(['G1','G2'])].itertuples():
    c=BR.set_index('group_id').new_cols[r.row]; keep=np.array([i not in TOP2 for i in ids]) if getattr(r,'sample')!='all' else np.ones(len(ids),bool)
    X=np.column_stack([np.ones(keep.sum()),P[c].values[keep]]); raw=np.linalg.lstsq(X,y25[keep],rcond=None)[0][1]   # single sub-index group: slope per SD = raw slope x SD(sub-index over 34)
    bad+=int(abs(raw*sd34[c]-r.value)>1e-9)
print("bad",bad)

assert bad==0,f'{bad} estimates differ from the independent recomputation / model_results.csv'
res.to_csv(D/'bootstrap_results.csv',index=False,float_format='%.10g'); print('bootstrap_results.csv',len(res),'rows; Stage 2 reproduction OK')
