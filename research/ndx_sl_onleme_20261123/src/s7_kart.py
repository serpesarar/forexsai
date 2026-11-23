"""EK-4 adayları V1 2×/2,5× ATR5: 2. KURAL canlıya alma kartı (6 ölçüt) + braket plasebosu (aynı SL dağılımı, rastgele atanmış)."""
import importlib.util, json, numpy as np, pandas as pd
from eng import HERE, run2, SL, CORE
sp=importlib.util.spec_from_file_location('my_s1',HERE/'s1_tarama.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
def vb(k):
    def r(m,kk,f,c):
        x=f['atr5'];sl=SL if not np.isfinite(x) else max(SL,k*x/c['sc']);return {'kind':'mkt','sl':sl,'tp':sl*80/110}
    return r
def plac(ratios,seed):
    g=np.random.default_rng(seed)
    def r(m,kk,f,c):
        sl=SL*float(g.choice(ratios));return {'kind':'mkt','sl':sl,'tp':sl*80/110}
    return r
def go(rule,**ex):
    t=pd.concat([run2(S.M[k],S.SIG[k],rule=rule,**ex)[0] for k in S.MK]);return t[(t.period!='-')&(t.period!='VAKA')]
def card(t,t15,t0,name):
    R=t.R.to_numpy();u,inv=np.unique(t.day.to_numpy(),return_inverse=True);s=np.bincount(inv,weights=R);n=np.bincount(inv)
    g=np.random.default_rng(3);pk=g.integers(0,len(u),(4000,len(u)));mm=s[pk].sum(1)/n[pk].sum(1);h=len(R)//2
    dc=t[t.fam=='DC']
    chk={'1_hacim':len(R)>=150,'2_beklenti':bool(R.mean()>0 and (mm>0).mean()>=.9),'3_kararlilik':bool(R[:h].mean()>=0 and R[h:].mean()>=0),
         '4_surtunme':bool(t15.R.mean()>0),'5_icra':bool(abs(t0.R.mean()-R.mean())<=abs(R.mean())/2),'6_sira_bagimli':bool(dc.R.mean()>0)}
    d=dict(ad=name,n=len(R),ortR=round(float(R.mean()),4),P=round(float((mm>0).mean()),3),CI=[round(float(np.percentile(mm,2.5)),4),round(float(np.percentile(mm,97.5)),4)],
           yarilar=[round(float(R[:h].mean()),4),round(float(R[h:].mean()),4)],spread15_ortR=round(float(t15.R.mean()),4),lag0_ortR=round(float(t0.R.mean()),4),
           tek_poz_DC_ortR=round(float(dc.R.mean()),4),checks=chk,verdikt='LIVE' if all(chk.values()) else 'SHADOW')
    print(json.dumps(d,ensure_ascii=False));return d
b=go(None,lag=1);bR=b.R.sum()
res={}
for k in (2.0,2.5):
    t=go(vb(k),lag=1);t15=go(vb(k),lag=1,spread=2.25,slip=0.2);t0=go(vb(k),lag=0)
    res[k]=card(t,t15,t0,f'V1 SL=max(110,{k}xATR5) lag1')
    # plasebo: aynı SL oranı dağılımı (bu adayın kendi işlem barlarından), rastgele atanmış
    ratios=[]
    for mk in S.MK:
        m=S.M[mk];tt,_=run2(m,S.SIG[mk],lag=1)
        for kk in tt.kk:
            f=m.feat(int(kk));sc=m.sc(int(kk));x=f['atr5'];ratios.append(1.0 if not np.isfinite(x) else max(1.0,k*x/sc/SL))
    ratios=np.array(ratios);sims=[go(plac(ratios,s),lag=1).R.sum()-bR for s in range(30)]
    real=t.R.sum()-bR;p=float(np.mean(np.array(sims)>=real))
    print(f"  braket plasebosu k={k}: gerçek Δ {real:+.1f}R | plasebo medyan {np.median(sims):+.1f} %90 {np.percentile(sims,90):+.1f} | p = {p:.3f}",flush=True)
    res[k]['plasebo']=dict(real=real,median=float(np.median(sims)),p90=float(np.percentile(sims,90)),p=p)
json.dump({str(k):v for k,v in res.items()},open(HERE.parent/'results/kart_v1.json','w'),ensure_ascii=False,indent=1,default=str)
