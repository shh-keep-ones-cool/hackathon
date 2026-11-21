"""Create raw-derived features and exploratory OLS associations for PCI 2025.
The outcome is a rate per 1,000 people; pop is stored in thousand people, so rate = count/pop.
Separate one-index models are used because n=34 is too small for 9 indices + controls in one model.
"""
import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm
from common import DATA

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--outcome',choices=['firms_new','firms_active'],default='firms_new')
    p.add_argument('--minimum-n',type=int,default=20)
    args=p.parse_args()
    df=pd.read_csv(DATA/'pci_provinces.csv',encoding='utf-8-sig')
    df['pop']=pd.to_numeric(df['pop'],errors='coerce')
    for c in ['firms_new','firms_active','grdp','grdp_pc']:
        if c in df: df[c]=pd.to_numeric(df[c],errors='coerce')
    # Derived features are computed here, never stored as raw source inputs.
    if args.outcome not in df or df[args.outcome].notna().sum()==0:
        raise SystemExit(f'Chưa có {args.outcome} trong pci_provinces.csv. Hãy import GSO trước.')
    if df['pop'].isna().any() or (df['pop'].dropna()<=0).any():
        print('Cảnh báo: có tỉnh thiếu dân số/giá trị dân số không hợp lệ; sẽ chỉ dùng complete cases.')
    df[f'{args.outcome}_per_1000']=df[args.outcome]/df['pop'] # pop is thousands of persons
    df[f'ln_{args.outcome}']=np.log(df[args.outcome].where(df[args.outcome]>0))
    for c in [f'pci_s{i}' for i in range(1,10)]: df[c]=pd.to_numeric(df[c],errors='coerce')
    df.to_csv(DATA/'derived_features_2025.csv',index=False,encoding='utf-8-sig')
    ycol=f'{args.outcome}_per_1000'; results=[]
    for i in range(1,10):
        xcol=f'pci_s{i}'; sample=df[[xcol,ycol]].replace([np.inf,-np.inf],np.nan).dropna()
        n=len(sample)
        if n<args.minimum_n:
            print(f'SKIP {xcol}: n={n} < minimum {args.minimum_n}'); continue
        X=sm.add_constant(sample[[xcol]])
        fit=sm.OLS(sample[ycol],X).fit(cov_type='HC3')
        beta=float(fit.params[xcol]); se=float(fit.bse[xcol]); ci=fit.conf_int().loc[xcol]
        results.append({'outcome':ycol,'predictor':xcol,'model_spec':'OLS bivariate; HC3 robust SE; cross-sectional association','n':n,'coef':beta,'std_err_hc3':se,'p_value':float(fit.pvalues[xcol]),'r_squared':float(fit.rsquared),'ci95_low':float(ci.iloc[0]),'ci95_high':float(ci.iloc[1]),'interpretation':'Association only; not causal.'})
    pd.DataFrame(results,columns=['outcome','predictor','model_spec','n','coef','std_err_hc3','p_value','r_squared','ci95_low','ci95_high','interpretation']).to_csv(DATA/'model_results.csv',index=False,encoding='utf-8-sig')
    print(f'Wrote {len(results)} separate OLS models to data/model_results.csv')
if __name__=='__main__': main()
