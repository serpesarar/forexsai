"""USOIL BUY gerçek sinyal setleri (1m broker barları) + M5'ten rejim etiketi.

A : botun canlı-aile USOIL BUY girişleri (BREAKOUT hariç), config geometrisiyle yeniden oynatılmış
B : pulse1/2/3 USOIL BUY sinyalleri 2026-06-20→09-02, 15 dk tekilleştirme (çakışmaya izin)
"""
import pickle
import numpy as np
import pandas as pd
from usoil_lab import Set, _path, causal_ema, regime_at, TP_PCT, SL_PCT, SPREAD

BROKER_OFF = pd.Timedelta(hours=3)          # Haz–Eyl 2026 (yaz saati)
HZ = 48 * 60


def m5_regime():
    z = np.load("spotcrude_m5.npz")
    t = pd.to_datetime(z["t"], unit="s"); C = z["c"]
    return t, C, causal_ema(C, 3 * 288)


def label(ts_utc, t5, C5, ema5):
    i = t5.searchsorted((ts_utc.tz_convert(None) if ts_utc.tzinfo else ts_utc) + BROKER_OFF)
    return regime_at(C5, ema5, i, 288) if i > 300 else (np.nan,) * 3


def build():
    m = pd.read_pickle("fx_USOIL.FOREX_1m.pkl")[["open", "high", "low", "close"]].astype(float)
    T = m.index; O, H, L, C = (m[c].values for c in ("open", "high", "low", "close"))
    t5, C5, ema5 = m5_regime()
    # A
    tb = pd.read_pickle("trades_base.pkl")
    tb = tb[(tb.sym == "USOIL.FOREX") & (tb.dir == "BUY") & (tb.fo == 1) & (tb.fc == 1)
            & ~tb.scope.fillna("").str.contains("BREAKOUT")]
    pa, ra = [], []
    for r in tb.itertuples():
        i = T.searchsorted(r.open_utc.floor("min")) + 1          # giriş dakikası atlanır
        e = r.open_price; risk = e * SL_PCT / 100
        pa.append(_path(O, H, L, C, i, HZ, e, risk))
        ra.append(dict(t=r.open_utc, lot=r.volume, voters=r.voters, real_R=r.R_real,
                       **dict(zip(("r24", "dist", "slope"), label(r.open_utc, t5, C5, ema5)))))
    A = Set(pa, pd.DataFrame(ra), 1)
    # B
    pl = pd.read_pickle("pl_usoil.pkl"); pl["t"] = pd.to_datetime(pl.created_at)
    pl = pl[(pl.t >= "2026-06-20") & (pl.t < "2026-09-02") & (pl.ml_direction == "BUY")].sort_values("t")
    pb, rb, lastt = [], [], pd.Timestamp("2000-01-01", tz="UTC")
    for s in pl.itertuples():
        if s.t - lastt < pd.Timedelta(minutes=15):
            continue
        i = T.searchsorted(s.t.ceil("min"))
        if i + 30 >= len(T) or (T[i] - s.t) > pd.Timedelta(minutes=5):
            continue
        lastt = s.t
        e = O[i] + SPREAD; risk = e * SL_PCT / 100
        pb.append(_path(O, H, L, C, i, HZ, e, risk))
        rb.append(dict(t=s.t, model=s.model_type, **dict(zip(("r24", "dist", "slope"), label(s.t, t5, C5, ema5)))))
    B = Set(pb, pd.DataFrame(rb), 1)
    return A, B


if __name__ == "__main__":
    import usoil_lab as U
    A, B = build()
    Lg = U.build_L()
    pickle.dump((A, B, Lg), open("usoil_sets.pkl", "wb"))
    for nm, s in (("A bot (config geometri)", A), ("B pulse", B), ("L 17 ay sentetik", Lg)):
        print(f"{nm}: n={len(s.base)}  ΣR={s.base.sum():+.1f}  ort={s.base.mean():+.3f}R  WR={(s.base>0).mean():.3f}")
