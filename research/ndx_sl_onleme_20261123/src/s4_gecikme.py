"""Gecikme taraması (EK-3): filtresiz ek bekleme L dk, yıl başına Σ R — 'bekle' etkisi mi zincir kaosu mu?"""
import importlib.util, pandas as pd
from eng import HERE, run2
sp=importlib.util.spec_from_file_location('my_s1',HERE/'s1_tarama.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
rows=[]
for lag in (0,1,2,3,4,5,6,8,10,12,15,20,30):
    ts=[run2(S.M[k],S.SIG[k],lag=lag)[0] for k in S.MK];t=pd.concat(ts);t=t[(t.period!='-')&(t.period!='VAKA')]
    by=t.groupby(t.et.dt.year).R.sum();r={'lag':lag,**{str(y):round(v,1) for y,v in by.items()},'ΣR':round(t.R.sum(),1),'n':len(t),'ortR':round(t.R.mean(),3)}
    rows.append(r);print(r,flush=True)
pd.DataFrame(rows).to_csv(HERE.parent/'results/gecikme.csv',index=False)
