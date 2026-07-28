import numpy as np, pandas as pd
from audit_res import load, resolve

GEOMS=[(0.727,1.0),(1.0,1.0),(1.5,1.0),(2.0,1.0),(3.0,1.0),(4.0,1.0)]
d=load("long_1h.csv")
pc=d.close.shift(1)
tr=pd.concat([d.high-d.low,(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
d["atr_pct"]=(tr.ewm(alpha=1/14,adjust=False).mean()/d.close).shift(1)

def evs(H, cost_pts, slip_pts, tie="split"):
    e=d[(d.ts<=d.ts.max()-pd.Timedelta(hours=H+2))&d.atr_pct.gt(0)]
    ets=e.ts.values; epx=e.open.to_numpy(); a=e.atr_pct.to_numpy()
    yr=pd.DatetimeIndex(e.ts).year; years=sorted(set(yr))
    c=cost_pts/epx; s=slip_pts/epx      # FIYAT-DUYARLI surtunme (2016'da 1 puan cok daha pahali)
    rows=[]
    for tp_a,sl_a in GEOMS:
        tp,sl=a*tp_a,a*sl_a
        row=dict(rr=round(tp_a/sl_a,2))
        for dr in ("BUY","SELL"):
            rr_=[]
            for t in (("sl","tp") if tie=="split" else (tie,)):
                w,l,o,er,amb=resolve(d,ets,epx,tp,sl,H,dr,t)
                sgn=1.0 if dr=="BUY" else -1.0
                r=np.where(w,(tp-c)/sl,np.where(l,-(sl+c+s)/sl,0.0))
                r=np.where(o,(sgn*er-c)/sl,r); rr_.append(r)
            r=np.mean(rr_,axis=0)
            row[f"ev_{dr}"]=round(float(r.mean()),4)
            if dr=="BUY":
                row["poz_yil"]=sum(1 for y in years if r[yr==y].mean()>0)
                row["acik%"]=round(float(o.mean())*100,1)
        rows.append(row)
    return pd.DataFrame(rows)

print("=== 1) UFUK DUYARLILIGI (adil beraberlik, surtunme 1 puan fiyat-duyarli) ===")
for H in (12,24,48,72):
    t=evs(H,1.0,0.0)
    print(f"\n-- ufuk {H} saat --"); print(t.to_string(index=False))
    print(f"   RR0.73->RR3.0 fark: {t.ev_BUY.iloc[4]-t.ev_BUY.iloc[0]:+.4f}")

print("\n\n=== 2) GERCEKCI SURTUNME (ufuk 24s, adil beraberlik) ===")
for cost,slip,lbl in [(1.0,0.0,"1 puan (iddianin varsayimi, ama fiyat-duyarli)"),
                      (2.0,1.0,"2 puan + 1 puan stop kaymasi"),
                      (3.0,2.0,"3 puan + 2 puan stop kaymasi"),
                      (4.0,3.0,"4 puan + 3 puan stop kaymasi")]:
    t=evs(24,cost,slip)
    print(f"\n-- {lbl} --"); print(t.to_string(index=False))
    print(f"   RR0.73->RR3.0 fark: {t.ev_BUY.iloc[4]-t.ev_BUY.iloc[0]:+.4f}")

print("\n\n=== 3) IDDIANIN SABIT-ORAN SURTUNMESI vs FIYAT-DUYARLI (1 puan) ===")
e=d[(d.ts<=d.ts.max()-pd.Timedelta(hours=26))&d.atr_pct.gt(0)]
px=e.open.to_numpy()
print(f"NDX acilis fiyati: 2016 medyan={np.median(px[pd.DatetimeIndex(e.ts).year==2016]):.0f}"
      f"  2026 medyan={np.median(px[pd.DatetimeIndex(e.ts).year==2026]):.0f}")
print(f"1 puan oransal maliyet: 2016'da {1/np.median(px[pd.DatetimeIndex(e.ts).year==2016])*1e4:.2f} bp,"
      f" 2026'da {1/np.median(px[pd.DatetimeIndex(e.ts).year==2026])*1e4:.2f} bp"
      f"  -> iddianin kodu HER YIL 2026 seviyesini (1/29000) kullaniyor")
