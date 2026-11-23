"""EK-4: oynaklığa göre genişleyen braket + eşit $ risk (lot = 30·110/SL). lag 1 tabanına karşı."""
import importlib.util, numpy as np, pandas as pd
from eng import HERE, run2, SL
sp=importlib.util.spec_from_file_location('my_s1',HERE/'s1_tarama.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
def vb(meas,k):
    def r(m,kk,f,c):
        sc=c['sc']
        if meas=='atr5':x=f['atr5']
        elif meas=='atr1h':x=f['atr1h']
        else:x=f['atr1m']*np.sqrt(30)
        slp=SL if not np.isfinite(x) else max(SL,k*x/sc)
        return {'kind':'mkt','sl':slp,'tp':slp*80/110}
    return r
V={}
for k in (2,2.5,3):V[f'V1 SL=max(110,{k}×ATR5)']=vb('atr5',k)
for k in (0.75,1):V[f'V3 SL=max(110,{k}×ATR1h)']=vb('atr1h',k)
for k in (1,1.5,2):V[f'V4 SL=max(110,{k}×ATR1√30)']=vb('n',k)
def go(rule,**ex):
    t=pd.concat([run2(S.M[k],S.SIG[k],rule=rule,**ex)[0] for k in S.MK]);return t[t.period!='-']
CORE=['ESKI-A','ESKI-B','Y24','Y25']
def boot(t,b,reps=2000):
    t,b=t[t.period.isin(CORE+['Y26b'])],b[b.period.isin(CORE+['Y26b'])]
    d=pd.concat([t.groupby('day').R.sum().rename('r'),b.groupby('day').R.sum().rename('b')],axis=1).fillna(0);x=(d.r-d.b).to_numpy()
    g=np.random.default_rng(5);return float((x[g.integers(0,len(x),(reps,len(x)))].mean(1)>0).mean())
out=[]
for ex in (dict(lag=1),dict(lag=1,spread=2.25,slip=0.2),dict(lag=0)):
    b=go(None,**ex);bb=b[b.period!='VAKA'];by0=bb.groupby(bb.et.dt.year).R.sum()
    print('\n### taban',ex,'ΣR %+.1f n %d'%(bb.R.sum(),len(bb)),flush=True)
    for n,r in V.items():
        t=go(r,**ex);tt=t[t.period!='VAKA'];by=tt.groupby(tt.et.dt.year).R.sum().reindex(by0.index,fill_value=0)-by0
        per={p:tt[tt.period==p].R.sum()-bb[bb.period==p].R.sum() for p in CORE}
        perm={p:tt[tt.period==p].R.mean()-bb[bb.period==p].R.mean() for p in CORE}
        k1=all(per[p]>0 and perm[p]>0 for p in CORE);s4=all(by.get(y,0)>0 for y in (2023,2024,2025,2026))
        sl=1-(tt.why=='SL').sum()/(bb.why=='SL').sum();tp=1-(tt.why=='TP').sum()/(bb.why=='TP').sum()
        P=boot(t,b) if ex.get('spread') is None else np.nan
        print(f"{n:28s} "+" ".join(f"{y}:{d:+5.1f}" for y,d in by.items())+f" | ΔΣ {tt.R.sum()-bb.R.sum():+6.1f} yıl+ {(by>0).sum()}/9 K1 {'✓' if k1 else '✗'} S4 {'✓' if s4 else '✗'} P {P:.2f} | SL engel %{100*sl:.0f} TP kayıp %{100*tp:.0f}",flush=True)
        out.append(dict(ex=str(ex),aday=n,dSR=tt.R.sum()-bb.R.sum(),k1=k1,s4=s4,P=P,sl_engel=sl,tp_kayip=tp,**{str(y):d for y,d in by.items()}))
pd.DataFrame(out).to_csv(HERE.parent/'results/vol_braket.csv',index=False)
