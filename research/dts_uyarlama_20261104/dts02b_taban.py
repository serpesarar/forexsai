"""DTS-02b (sonradan) — ORB kırılım şartı, kapısız 'aralık sonunda hep gir' tabanını aşıyor mu?"""
import zlib
import numpy as np
import pandas as pd
import dts02_orb as M
from common import SPREAD, load, month_boot

CELLS = [("NDX", "5m", 15, "or_mid", 2.0), ("NDX", "5m", 15, "or_mid", 1.0), ("NDX", "15m", 15, "or_low", 2.0),
         ("NDX", "15m", 15, "or_low", 1.0), ("NDX", "15m", 30, "or_low", 1.0), ("NDX", "5m", 30, "or_low", 1.0),
         ("XAUUSD", "5m", 15, "or_mid", 2.0), ("GDAXI", "15m", 15, "or_mid", 2.0), ("USOIL", "5m", 15, "or_mid", 2.0)]


def base_trade(d, idx, mins, o0, f0, orm, stop, tgt, sp):
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    rng = [i for i in idx if mins[i] < o0 + orm]; post = [i for i in idx if mins[i] >= o0 + orm]
    if not rng or not post:
        return None
    oh, ol = h[rng].max(), l[rng].min()
    e = o[post[0]] + sp
    st = (oh + ol) / 2 if stop == "or_mid" else ol
    risk = e - st
    if risk <= M.MIN_RISK * e:
        return None
    tg = e + tgt * risk
    for j in post:
        if l[j] <= st:
            return -1.0
        if h[j] >= tg:
            return tgt
    return (c[post[-1]] - e) / risk


rows = []
for sym, tf, orm, stop, tgt in CELLS:
    d = load(sym, tf); M.ATR = M.atr14(d); bar_min = int(tf[:-1])
    days, mins = M.days_of(d, sym); o0, f0 = M.hm(M.SESS[sym][1]), M.hm(M.SESS[sym][2]); sp = SPREAD[sym]
    dates = sorted(days); mid = dates[len(dates) // 2]
    orb, base, both, dd = [], [], [], []
    for dt in dates:
        r = M.trade(d, days[dt], mins, o0, f0, orm, bar_min, stop, tgt, "long", sp, False)
        b = base_trade(d, days[dt], mins, o0, f0, orm, stop, tgt, sp)
        if b is not None:
            base.append(b)
        if r is not None and b is not None:
            both.append((r, b)); dd.append(dt)
    x = np.array([r - b for r, b in both]); dd = np.array(dd); first = dd < mid
    months = np.array([str(t)[:7] for t in dd])
    rows.append({"sym": sym, "tf": tf, "or": orm, "stop": stop, "tgt": tgt, "taban_n": len(base), "taban_ortR": float(np.mean(base)),
                 "eşli_n": len(x), "orb_ortR_eşli": float(np.mean([r for r, _ in both])), "taban_ortR_eşli": float(np.mean([b for _, b in both])),
                 "fark": float(x.mean()), "P": month_boot(x, months, zlib.crc32(f"{sym}{tf}{orm}{stop}{tgt}".encode())),
                 "fark_y1": float(x[first].mean()), "fark_y2": float(x[~first].mean())})
pd.set_option("display.width", 230)
out = pd.DataFrame(rows); out.to_csv("dts02b_taban.csv", index=False)
print(out.round(3).to_string(index=False))
