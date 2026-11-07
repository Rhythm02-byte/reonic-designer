# Prototype: derive per-option system sizes (kWp, battery kWh, HP kW, roof type) from BOM lines.
# Usage: python research/derive_features.py dataset <out_dir>   (reads raw data; outputs must stay out of git)
import sys, re, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_rows',200); pd.set_option('display.max_colwidth',60); pd.set_option('display.max_columns',40)
base=sys.argv[1]
def opt_features(g):
    r={}
    mod=g[g.component_type=='Module']
    r['n_mod_module']=mod.quantity.sum() if len(mod) else np.nan
    r['wp']=mod.module_watt_peak.median() if len(mod) else np.nan
    sub=g[(g.component_type=='ModuleFrameConstruction') & g.component_name.str.contains('Substructure') & ~g.component_name.str.contains('Ballast')]
    r['n_mod_sub']=sub.quantity.sum() if len(sub) else np.nan
    dc=g[g.component_name.str.startswith('DC Install')]
    r['n_mod_dc']=dc.quantity.sum() if len(dc) else np.nan
    pk=g.component_name.str.extract(r'(\d+(?:\.\d+)?)kWp \+ (\d+(?:\.\d+)?)kWh')
    pk=pk.dropna()
    r['pkg_kwp']=float(pk.iloc[0,0]) if len(pk) else np.nan
    r['pkg_kwh']=float(pk.iloc[0,1]) if len(pk) else np.nan
    b=g[g.component_type=='BatteryStorage']
    b=b[~b.component_name.str.contains('Coupling')]
    r['bat_kwh']=(b.inverter_power_kw*b.quantity).sum()/1000 if len(b) else 0.0
    inv=g[g.component_type=='Inverter']
    r['inv_kw']=inv.battery_capacity_kwh.max()/1000 if len(inv) else np.nan
    r['has_wallbox_new']=int((g.component_type=='Wallbox').any())
    hp=g[g.component_type=='Heatpump']
    r['hp_kw']=hp.heatpump_nominal_power_kw.max()/1000 if len(hp) else 0.0
    r['roof']= (sub.component_name.iloc[0].replace('Substructure ','') if len(sub) else None)
    r['n_lines']=len(g)
    return pd.Series(r)
for d in ['23c108b7','2a8ba8e2']:
    print('\n'+'='*30, d)
    p=pd.read_csv(f'{base}/{d}/project_options_parts.csv', encoding='latin1')
    sq=pd.read_csv(f'{base}/{d}/projects_status_quo.csv')
    f=p.groupby(['project_id','option_id','option_number']).apply(opt_features).reset_index()
    f['n_mod']=f.n_mod_module.fillna(f.n_mod_sub).fillna(f.n_mod_dc)
    f['kwp_est']=np.where(f.pkg_kwp.notna(), f.pkg_kwp, f.n_mod*f.wp.fillna(450)/1000)
    f['bat_kwh']=np.where((f.bat_kwh==0)&f.pkg_kwh.notna(), f.pkg_kwh, f.bat_kwh)
    print('n_mod source coverage', f[['n_mod_module','n_mod_sub','n_mod_dc','pkg_kwp']].notna().mean().round(2).to_dict(), 'n_mod any', f.n_mod.notna().mean().round(3))
    print(f[['kwp_est','bat_kwh','inv_kw','hp_kw','n_lines']].describe().T)
    print('battery share', (f.bat_kwh>0).mean().round(3), 'wallbox share', f.has_wallbox_new.mean().round(3), 'hp share',(f.hp_kw>0).mean().round(3))
    print('roof types'); print(f.roof.value_counts().head(15).to_string())
    f.to_csv(f'{sys.argv[2]}/feat_{d}.csv',index=False)
    # multi-option examples
    multi=f.groupby('project_id').filter(lambda x: len(x)>1)
    print('multi-option example rows'); print(multi[['project_id','option_number','kwp_est','bat_kwh','inv_kw','hp_kw','has_wallbox_new','n_lines']].head(30).to_string())
    # within project variation
    v=multi.groupby('project_id').agg(kwp_sd=('kwp_est','std'),bat_sd=('bat_kwh','std'),bat_nuniq=('bat_kwh','nunique'),kwp_nuniq=('kwp_est','nunique'))
    print('multi-option projects: kwp differs',(v.kwp_nuniq>1).mean().round(2),'bat differs',(v.bat_nuniq>1).mean().round(2))
    # join with first option (lowest option_number)
    first=f.sort_values('option_number').drop_duplicates('project_id')
    j=sq.merge(first,on='project_id')
    j['demand_kwh']=j.energy_demand_wh/1000
    print('corr demand vs kwp', j[['demand_kwh','kwp_est']].corr().iloc[0,1].round(3), 'kwp/MWh ratio median', (j.kwp_est/(j.demand_kwh/1000)).median().round(2))
    print('battery by has_ev'); print(j.groupby('has_ev').agg(n=('bat_kwh','size'),bat_share=('bat_kwh',lambda x:(x>0).mean()),bat_med=('bat_kwh','median'),kwp_med=('kwp_est','median'),wb=('has_wallbox_new','mean')).round(2))
    print('by heating type'); print(j.groupby(j.heating_existing_type.fillna('NA')).agg(n=('hp_kw','size'),hp_share=('hp_kw',lambda x:(x>0).mean()),kwp_med=('kwp_est','median'),bat_med=('bat_kwh','median')).round(2))
    print('by has_solar'); print(j.groupby('has_solar').agg(n=('kwp_est','size'),kwp_med=('kwp_est','median'),bat_share=('bat_kwh',lambda x:(x>0).mean())).round(2))
    j['dem_bin']=pd.cut(j.demand_kwh,[0,2500,3500,4500,5500,7000,10000,60000])
    print(j.groupby('dem_bin').agg(n=('kwp_est','size'),kwp_med=('kwp_est','median'),kwp_q25=('kwp_est',lambda x:x.quantile(.25)),kwp_q75=('kwp_est',lambda x:x.quantile(.75)),bat_share=('bat_kwh',lambda x:(x>0).mean()),bat_med=('bat_kwh','median')).round(2))
    print('battery sizes'); print(j.bat_kwh.round(1).value_counts().head(15).to_string())
    j.to_csv(f'{sys.argv[2]}/joined_{d}.csv',index=False)
