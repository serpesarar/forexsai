"""EK-3: canlı-gerçekçi taban (lag 1) karşısında D/E adayları, yıl başına; ayrıca spread×1,5 ile."""
import importlib.util, pandas as pd
from eng import HERE, run2
sp=importlib.util.spec_from_file_location('my_s1',HERE/'s1_tarama.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
def go(kw,**ex):
    t=pd.concat([run2(S.M[k],S.SIG[k],**kw,**ex)[0] for k in S.MK]);return t[(t.period!='-')]
names=["D buy-stop +0.25ATR5 15dk","D buy-stop +0.25ATR5 30dk","D buy-stop +0.5ATR5 15dk","D buy-stop +0.5ATR5 30dk","D buy-stop +1.0ATR5 30dk","E probasyon 10 bar","E0 probasyon 10 bar + kayıpsız"]
for ex in (dict(lag=1),dict(lag=1,spread=2.25,slip=0.2)):
    b=go({},**ex);bb=b[b.period!='VAKA'];by0=bb.groupby(bb.et.dt.year).R.sum()
    print('\n### taban',ex,'ΣR %+.1f n %d ortR %+.3f'%(bb.R.sum(),len(bb),bb.R.mean()))
    for n in names:
        t=go(S.C[n],**ex);tt=t[t.period!='VAKA'];by=tt.groupby(tt.et.dt.year).R.sum()-by0
        v=t[t.period=='VAKA'];v0=b[b.period=='VAKA']
        s4=all(by.get(y,0)>0 for y in (2023,2024,2025,2026));pos=(by>0).sum()
        sl=(tt.why=='SL').sum()/(bb.why=='SL').sum();tp=(tt.why=='TP').sum()/(bb.why=='TP').sum()
        print(f"{n:32s} "+" ".join(f"{y}:{d:+5.1f}" for y,d in by.items())+f" | ΔΣ {tt.R.sum()-bb.R.sum():+6.1f} ortR {tt.R.mean():+.3f} yıl+ {pos}/9 S4 {'✓' if s4 else '✗'} | SL engel %{100*(1-sl):.0f} TP kayıp %{100*(1-tp):.0f} | VAKA SL {(v.why=='SL').sum()}/{(v0.why=='SL').sum()} TP {(v.why=='TP').sum()}/{(v0.why=='TP').sum()}",flush=True)
