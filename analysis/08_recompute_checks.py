import os,pathlib; os.chdir(pathlib.Path(__file__).resolve().parent.parent/"data")   # run from anywhere
import numpy as np, pandas as pd
from scipy import stats
P=pd.read_csv('pci_provinces.csv'); O=pd.read_csv('outcomes_34_rebuilt.csv'); BR=pd.read_csv('bridge_groups.csv'); PAN=pd.read_csv('pci_groups_34_panel.csv'); MR=pd.read_csv('model_results.csv')
ids=list(P.province_id); zs=lambda a:(a-a.mean())/a.std(ddof=1)
print("="*70,"\nNUMBER 1: HCMC shortfall (default headline)")
cols=['pci_s5','pci_s6']   # G4 = integrity and fair competition (bridge_groups.csv)
raw=sum(zs(P[c]) for c in cols)/len(cols); g4=zs(raw); g4.index=ids
o24=O[O.year==2024].set_index('province_id').loc[ids]; ln=np.log(o24.grdp/o24['pop'])
q=np.percentile(ln,[25,50,75]); print('quartile edges of ln GRDPpc 2024',q.round(4))
qo=lambda v:1 if v<=q[0] else 2 if v<=q[1] else 3 if v<=q[2] else 4
h='tp-ho-chi-minh'; peers=[i for i in ids if i!=h and qo(ln[i])==qo(ln[h])]
print('HCMC quartile',qo(ln[h]),'peers',len(peers),peers)
print('HCMC G4 score %.4f  peer median %.4f  gap %.4f  rank %d/34'%(g4[h],np.median(g4[peers]),g4[h]-np.median(g4[peers]),1+(g4>g4[h]).sum()))
print('peers G4:',g4[peers].round(2).to_dict())
print('Sensitivity: HCMC GRDPpc rank', int(ln.rank(ascending=False)[h]),'; other peer sets:')
for name,pp in {'all others':[i for i in ids if i!=h],'8 nearest':list(ln.drop(h).sub(ln[h]).abs().sort_values().index[:8])}.items():
    print('  %-10s median %.4f gap %.4f'%(name,np.median(g4[pp]),g4[h]-np.median(g4[pp])))
print("="*70,"\nNUMBER 2: 2025 OLS, G1 (=pci_s1), HC3")
y=(P.firms_new/P['pop']).values; x=P.pci_s1.values
def hc3(X,y):
    XtXi=np.linalg.inv(X.T@X); b=XtXi@X.T@y; e=y-X@b; hh=np.einsum('ij,jk,ik->i',X,XtXi,X)
    M=(X*(e/(1-hh))[:,None]).T@(X*(e/(1-hh))[:,None]); V=XtXi@M@XtXi; return b,np.sqrt(np.diag(V)),hh
X=np.column_stack([np.ones(34),x]); b,se,hh=hc3(X,y)
print('raw coef %.6f  HC3 se %.6f  z-CI [%.4f, %.4f]  t33-CI [%.4f, %.4f]  p(z)=%.4f p(t32)=%.4f'%(b[1],se[1],b[1]-1.96*se[1],b[1]+1.96*se[1],b[1]-stats.t.ppf(.975,32)*se[1],b[1]+stats.t.ppf(.975,32)*se[1],2*(1-stats.norm.cdf(abs(b[1]/se[1]))),2*(1-stats.t.cdf(abs(b[1]/se[1]),32))))
print('standardised coef (x,y z-scored): %.4f ; dashboard-style %.4f'%(b[1]*x.std(ddof=1)/y.std(ddof=1), b[1]*x.std(ddof=1)/y.std(ddof=1)))
print('Stage2 file: coef 0.167506 se 0.093723 | max leverage %.3f at %s; HCMC/HN y per 1000: %s'%(hh.max(),ids[int(hh.argmax())],{i:round(y[ids.index(i)],2) for i in ['tp-ho-chi-minh','ha-noi']}))
print('y25 mean %.3f median %.3f max %.3f'%(y.mean(),np.median(y),y.max()))
k=np.array([i not in ('ha-noi','tp-ho-chi-minh') for i in ids]); b2,se2,_=hc3(X[k],y[k]); print('excl HCMC/HN: coef %.4f se %.4f'%(b2[1],se2[1]))
# influence: drop-one
dr=[hc3(np.delete(X,i,0),np.delete(y,i))[0][1] for i in range(34)]; print('drop-one range of coef: %.3f..%.3f'%(min(dr),max(dr)))
print("="*70,"\nNUMBER 3: panel TWFE G3, k=2, two-way FE, cluster-by-province")
def twfe(g,k,pids):
    o=O[['province_id','year','firms_new_per_1000']].assign(year=lambda d:d.year-k); o['y']=np.log(o.firms_new_per_1000)
    d=PAN[PAN.province_id.isin(pids)][['province_id','year',g+'_w_z34']].merge(o[['province_id','year','y']],on=['province_id','year'])
    X=d.pivot(index='province_id',columns='year',values=g+'_w_z34').loc[pids].values; Y=d.pivot(index='province_id',columns='year',values='y').loc[pids].values
    f=lambda A:A-A.mean(1,keepdims=True)-A.mean(0,keepdims=True)+A.mean(); xd,yd=f(X),f(Y)
    b=(xd*yd).sum()/(xd**2).sum(); u=yd-b*xd; G,T=X.shape; N=G*T
    meat=((xd*u).sum(1)**2).sum(); V0=meat/(xd**2).sum()**2
    return b,V0,G,T,N,X,Y
for g,k in [('G3',2),('G5',3),('G1',3)]:
    b,V0,G,T,N,*_=twfe(g,k,ids)
    K=1+(G-1)+(T-1)  # slope + FE dummies
    s={'CR0':np.sqrt(V0),'CR1 (G/(G-1))':np.sqrt(V0*G/(G-1)),'CR1 +(N-1)/(N-T) [matches file]':np.sqrt(V0*G/(G-1)*(N-1)/(N-T))}
    mr=MR[(MR.block=='panel_fe')&(MR.outcome==f'ln_firms_new_per1000_t+{k}')&(MR['sample']=='all')&(MR.row==g)&(MR.controls=='weighted')].set_index('stat').value
    print(f'{g} k={k}: coef {b:.6f} (file {mr['coef']:.6f}); file se {mr['se']:.5f}; ci [{mr.ci_low:.4f},{mr.ci_high:.4f}] p={mr['p']:.4f}; pct/SD file {mr.pct_per_sd:.3f} vs 100*(exp(b)-1)={100*(np.exp(b)-1):.3f}')
    for n_,v in s.items(): print('   se %-22s %.5f  t33 p=%.4f'%(n_,v,2*(1-stats.t.cdf(abs(b/v),33))))
    print('   T=%d years, G=%d clusters, N=%d'%(T,G,N))
# sign flips across horizons
print('\nsign of panel coef by horizon (all sample):')
print(MR[(MR.block=='panel_fe')&(MR['sample']=='all')&(MR.stat=='coef')&(MR.controls=='weighted')].pivot(index='row',columns='outcome',values='value').round(4).to_string())
