"""Her işlem için 1m yol dizileri (girişten itibaren +POST dk) → paths.pkl

Bar fiyatları BID. BUY: çıkış bid'le (high/low doğrudan). SELL: çıkış ask'la
(high+spread / low+spread). Giriş barı: girişin olduğu dakika barı DAHİL EDİLMEZ
(dakika içi sıra bilinmez); yol bir sonraki dakikadan başlar, giriş barı ayrıca
tutulur (ambiguity bayrağı).
"""
import numpy as np
import pandas as pd

POST_MIN = 600          # kapanıştan sonra da 10 saat yol (karşı-olgusal için)
SPREAD = {"USOIL.FOREX": 0.03, "NDX.INDX": 1.5, "GDAXI.INDX": 1.5}

bars = {}
for s in SPREAD:
    m = pd.read_pickle(f"fx_{s}_1m.pkl")          # index = onarılmış UTC zaman
    bars[s] = m[["open", "high", "low", "close"]].astype(float)

df = pd.read_pickle("trades_base.pkl"); df = df[(df.fo == 1) & (df.fc == 1)].copy()
out = []
for r in df.itertuples():
    m = bars[r.sym]
    t0 = r.open_utc.floor("min")
    seg = m.loc[t0: r.close_utc + pd.Timedelta(minutes=POST_MIN)]
    if len(seg) < 2:
        out.append(None); continue
    sgn = 1.0 if r.dir == "BUY" else -1.0
    sp = 0.0 if r.dir == "BUY" else SPREAD[r.sym]
    # lehe/aleyhe (R cinsinden), çıkış tarafı fiyatıyla
    fav = ((seg["high"].values + sp) - r.open_price) / r.risk if sgn > 0 else \
          (r.open_price - (seg["low"].values + sp)) / r.risk
    adv = ((seg["low"].values + sp) - r.open_price) / r.risk if sgn > 0 else \
          (r.open_price - (seg["high"].values + sp)) / r.risk
    cls = ((seg["close"].values + sp) - r.open_price) * sgn / r.risk
    opn = ((seg["open"].values + sp) - r.open_price) * sgn / r.risk
    out.append(dict(t=seg.index.values, fav=fav, adv=adv, cls=cls, opn=opn,
                    close_idx=int(np.searchsorted(seg.index.values,
                                                  np.datetime64(r.close_utc.floor("min").tz_convert(None)))),
                    ))
df["path"] = out
df = df[df["path"].notna()].copy()
df.to_pickle("paths.pkl")
print("yol kurulan işlem:", len(df))
