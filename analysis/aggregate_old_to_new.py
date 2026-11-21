"""Aggregate 63-province outcome counts to 34 new provinces.
Counts and population are apportioned by crosswalk share before rates are computed.
Per-capita GRDP is aggregated as a population-weighted mean; do not sum GRDP per capita.
"""
import pandas as pd
from common import DATA

def main():
    x=pd.read_csv(DATA/'outcomes_panel_63.csv',encoding='utf-8-sig')
    cw=pd.read_csv(DATA/'crosswalk_63_to_34.csv',encoding='utf-8-sig')
    x['province_id_old']=x['province_id_old'].astype(str); cw['old_province_id']=cw['old_province_id'].astype(str)
    cw['share']=pd.to_numeric(cw['share'],errors='coerce')
    sums=cw.groupby('old_province_id')['share'].sum()
    if not ((sums-1).abs()<1e-9).all(): raise ValueError('Share crosswalk không bằng 1 cho mọi tỉnh cũ')
    m=x.merge(cw[['old_province_id','new_province_id','share']],left_on='province_id_old',right_on='old_province_id',how='left',validate='many_to_one')
    if m['new_province_id'].isna().any(): raise ValueError('Có tỉnh cũ chưa map')
    for c in ['firms_new','firms_active','pop']:
        m[c]=pd.to_numeric(m[c],errors='coerce')*m['share']
    m['grdp_pc']=pd.to_numeric(m['grdp_pc'],errors='coerce')
    m['pop_for_weight']=m['pop']
    rows=[]
    for (pid,year),g in m.groupby(['new_province_id','year']):
        pop=g['pop'].sum(min_count=1)
        # Keep an aggregate NA if any contributing old province is missing that variable.
        # This prevents a partial sum from masquerading as a complete province total.
        row={'province_id':pid,'year':year,
             'firms_new':g['firms_new'].sum() if g['firms_new'].notna().all() else pd.NA,
             'firms_active':g['firms_active'].sum() if g['firms_active'].notna().all() else pd.NA,
             'pop':g['pop'].sum() if g['pop'].notna().all() else pd.NA,
             'grdp_pc':((g['grdp_pc']*g['pop_for_weight']).sum()/g['pop_for_weight'].sum()) if g['grdp_pc'].notna().all() and g['pop_for_weight'].notna().all() and g['pop_for_weight'].sum()>0 else pd.NA,
             'grdp_pc_price_basis':g['grdp_pc_price_basis'].dropna().iloc[0] if 'grdp_pc_price_basis' in g and g['grdp_pc_price_basis'].dropna().nunique()==1 else ('mixed_or_missing' if 'grdp_pc_price_basis' in g else ''),
             'n_old_provinces':g['province_id_old'].nunique()}
        if 'grdp_pc_price_basis' in g and g['grdp_pc_price_basis'].dropna().nunique()>1:
            raise ValueError(f'{pid} {year}: mixed GRDP price bases in old provinces')
        rows.append(row)
    out=pd.DataFrame(rows)
    out.to_csv(DATA/'outcomes_panel_34.csv',index=False,encoding='utf-8-sig')
    # Conservation check applies to each variable/year only when inputs are complete.
    for year,g in m.groupby('year'):
        for c in ['firms_new','firms_active','pop']:
            if g[c].notna().all() and out.loc[out.year.eq(year),c].notna().all():
                before=g[c].sum(); after=out.loc[out.year.eq(year),c].sum()
                if abs(before-after)>1e-6:
                    raise AssertionError(f'{year} {c}: before={before}, after={after}')
            else:
                print(f'WARN {year} {c}: conservation check skipped because source values are incomplete')
    print(f'Wrote outcomes_panel_34.csv ({len(out)} rows); counts/population conserved where source values complete.')
if __name__=='__main__': main()
