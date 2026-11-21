"""Compare JS OLS coefficients with NumPy OLS for each PCI component on complete cases."""
import json, subprocess, shutil
import numpy as np, pandas as pd
from common import DATA, ROOT

def main():
    if not shutil.which('node'):
        raise SystemExit('Node.js not found. Install Node.js 20+ to run the JS/Python parity test.')
    df=pd.read_csv(DATA/'derived_features_2025.csv',encoding='utf-8-sig')
    outcome='firms_new_per_1000'
    if outcome not in df: raise SystemExit('Run derive_and_model.py first with firms_new outcome.')
    diffs=[]
    for i in range(1,10):
        x=f'pci_s{i}'; s=df[[x,outcome]].replace([np.inf,-np.inf],np.nan).dropna()
        if len(s)<3: continue
        X=np.column_stack([np.ones(len(s)),s[x].to_numpy(float)])
        py=np.linalg.lstsq(X,s[outcome].to_numpy(float),rcond=None)[0]
        payload=[{'x':float(a),'y':float(b)} for a,b in zip(s[x],s[outcome])]
        proc=subprocess.run(['node',str(ROOT/'analysis/ols_reference.js')],input=json.dumps(payload),text=True,capture_output=True,check=True)
        js=json.loads(proc.stdout)
        diffs.extend([abs(float(py[0])-js['intercept']),abs(float(py[1])-js['slope'])])
    largest=max(diffs,default=0.0)
    print(f'Largest absolute coefficient difference: {largest:.12g}')
    if largest>=1e-6: raise SystemExit('FAIL: JS/Python OLS difference >= 1e-6')
    print('PASS: JS and Python coefficients agree within 1e-6')
if __name__=='__main__': main()
