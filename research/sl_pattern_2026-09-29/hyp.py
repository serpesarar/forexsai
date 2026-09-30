"""Önceden tanımlı giriş hipotezleri — "bu işlemi hiç açma" filtresi olarak.

Her filtre için: elenen kümenin toplam R'si ve $'ı (negatifse filtre kazandırır),
train/test ayrı, sembol-yön grupları ayrı, bootstrap P(elenen küme < 0).
"""
import numpy as np
import pandas as pd

SPLIT = pd.Timestamp("2026-08-01", tz="UTC")
df = pd.read_pickle("feat.pkl")
df["usd_R"] = df.risk * df.volume * np.where(df.sym == "USOIL.FOREX", 100.0, 1.0)
df["usd"] = df.simR * df.usd_R
df["test"] = df.open_utc >= SPLIT
df["grp"] = df.sym.str[:5] + "_" + df.dir

H = {
    "H1 rr<0.5": df.rr < 0.5,
    "H1b rr<0.4": df.rr < 0.4,
    "H2 SL>2ATR & TP<1.5ATR": (df.sl_atr1h > 2) & (df.tp_atr1h < 1.5),
    "H2b SL>1.5ATR": df.sl_atr1h > 1.5,
    "H3 bıçak chg60<-1ATR": df.chg60_atr_dir < -1.0,
    "H3b bıçak chg60<-0.7ATR": df.chg60_atr_dir < -0.7,
    "H3c chg15<-0.5ATR": df.chg15_atr_dir < -0.5,
    "H4 tek oy": df.n_voters <= 1,
    "H5 1h trend karşı": df["1h_trend_against"] == 1,
    "H5b 5m EMA200 karşı": df["5m_ema200_with"] == 0,
    "H6 kovalama wave>0.8": df.wave_pos_dir > 0.8,
    "H7 dip wave<0.2": df.wave_pos_dir < 0.2,
}


def row(name, mask, sub):
    x = sub[mask.loc[sub.index]]
    if len(x) == 0:
        return None
    rng = np.random.default_rng(1)
    bs = np.array([x.simR.values[rng.integers(0, len(x), len(x))].sum() for _ in range(2000)])
    return dict(h=name, n=len(x), wr=(x.simR > 0).mean().round(2), sumR=x.simR.sum().round(1),
                usd=x.usd.sum().round(0), R_tr=x[~x.test].simR.sum().round(1),
                R_te=x[x.test].simR.sum().round(1), n_te=int(x.test.sum()),
                p_neg=(bs < 0).mean().round(3))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    print("TÜMÜ:")
    print(pd.DataFrame([row(k, v, df) for k, v in H.items()]).to_string(index=False))
    for g, sub in df.groupby("grp"):
        rows = [row(k, v, sub) for k, v in H.items()]
        rows = [r for r in rows if r and r["n"] >= 5]
        print(f"\n{g}  (n={len(sub)}, ΣR={sub.simR.sum():.1f}, $={sub.usd.sum():.0f})")
        print(pd.DataFrame(rows).to_string(index=False))
