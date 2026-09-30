"""Pulse USOIL sinyallerini broker barlarında botun geometrisiyle yeniden oyna.

Dönem: besleme farkı ≈0 olan 2026-06-20 → 2026-09-02 (sinyaller broker fiyatıyla
aynı grafikten üretilmiş). Giriş = sinyal dakikasından SONRAKİ 1m bar açılışı
(+spread, BUY ask). TP %1.04 / SL %1.49 (config USOIL BUY). 30 dk'lık tekilleştirme
(aynı yönde açık pozisyon varken yeni giriş yok — botun MAX_OPEN_PER_SCOPE=1'i).
Test edilen: (a) chg15 filtresi, (b) kâr kilidi, (c) erken kes, (d) ikisi birlikte.
"""
import numpy as np
import pandas as pd
from sim import simulate

SP = 0.03
TP_PCT, SL_PCT = 1.04, 1.49
m = pd.read_pickle("fx_USOIL.FOREX_1m.pkl")[["open", "high", "low", "close"]].astype(float)
h1 = pd.read_pickle("fx_USOIL.FOREX_1h.pkl")
atr1h = h1["ind"].apply(lambda d: (d or {}).get("atr14")).astype(float)
T = m.index
O, H, L, C = m.open.values, m.high.values, m.low.values, m.close.values

pl = pd.read_pickle("pl_usoil.pkl")
pl["t"] = pd.to_datetime(pl.created_at)
pl = pl[(pl.t >= "2026-06-20") & (pl.t < "2026-09-02")].sort_values("t")


def run(direction: str):
    sig = pl[pl.ml_direction == direction]
    rows, busy_until = [], pd.Timestamp("2000-01-01", tz="UTC")
    for s in sig.itertuples():
        if s.t < busy_until:
            continue
        i = T.searchsorted(s.t.ceil("min"))
        if i + 5 >= len(T) or (T[i] - s.t) > pd.Timedelta(minutes=5):
            continue
        e = O[i] + (SP if direction == "BUY" else 0.0)
        risk = e * SL_PCT / 100; rr = TP_PCT / SL_PCT
        seg = slice(i, min(i + 2880, len(T)))
        sg = 1 if direction == "BUY" else -1
        if sg > 0:
            fav = (H[seg] - e) / risk; adv = (L[seg] - e) / risk; cls = (C[seg] - e) / risk
        else:
            fav = (e - L[seg] - SP) / risk; adv = (e - H[seg] - SP) / risk; cls = (e - C[seg] - SP) / risk
        p = dict(fav=fav, adv=adv, cls=cls)
        base, idx, why = simulate(p, rr, start=0)
        a = atr1h.loc[:s.t - pd.Timedelta(hours=1)]
        a = a.iloc[-1] if len(a) else np.nan
        chg15 = (C[i - 1] - C[i - 16]) * sg / a if i > 16 and a == a else np.nan
        chg60 = (C[i - 1] - C[i - 61]) * sg / a if i > 61 and a == a else np.nan
        lock = simulate(p, rr, be_trig=0.6 * rr, be_lock=0.5 * rr, start=0)[0]
        cut = base
        hit = np.where(adv[:121] <= -0.4)[0]
        if len(hit) and hit[0] <= idx:
            cut = -0.4
        rows.append(dict(t=s.t, model=s.model_type, conf=s.ml_confidence, base=base, lock=lock,
                         cut=cut, chg15=chg15, chg60=chg60, exit=why))
        busy_until = T[min(i + idx, len(T) - 1)]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    for d in ("BUY", "SELL"):
        R = run(d)
        R["half"] = np.where(R.t < pd.Timestamp("2026-07-27", tz="UTC"), "H1", "H2")
        print(f"\n=== pulse USOIL {d}  n={len(R)}  ΣR={R.base.sum():.1f}  WR={(R.base>0).mean():.2f}")
        R["knife15"] = R.chg15 < -0.5
        print(R.groupby("knife15").agg(n=("base", "size"), wr=("base", lambda x: (x > 0).mean()),
                                        R=("base", "sum"), meanR=("base", "mean")).round(3))
        print(R.groupby(["half", "knife15"]).agg(n=("base", "size"), meanR=("base", "mean")).round(3))
        R["b15"] = pd.qcut(R.chg15, 5)
        print(R.groupby("b15", observed=True).agg(n=("base", "size"), wr=("base", lambda x: (x > 0).mean()),
                                                  meanR=("base", "mean")).round(3))
        for k in ("lock", "cut"):
            dd = R[k] - R.base
            print(f"  {k}: ΔR={dd.sum():+.1f}  H1 {dd[R.half=='H1'].sum():+.1f}  H2 {dd[R.half=='H2'].sum():+.1f}"
                  f"  WR {(R.base>0).mean():.2f}→{(R[k]>0).mean():.2f}")
        R.to_pickle(f"pulse_replay_{d}.pkl")
