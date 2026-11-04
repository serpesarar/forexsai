"""Script çıktı kanalları → ikili tepki durumları (EK-7 kuralları; sonuçlara bakmadan sabit).

Olay kanalları (plotshape/plotchar/alertcondition/alert()/bgcolor/barcolor/plotarrow/strateji girişi):
    'on'  = değer var ve sıfırdan farklı;  girişte long/short, okta up/down ayrı.
Sayısal plot:
    fiyat ölçeğindeyse (medyan |p/close−1| < 0,25): 'px+' close>p, 'px-' close<p, 'up'/'dn' eğim
    osilatörse: iki işaret de ≥%5 ise 'z+'/'z-'; 'up'/'dn' eğim; 'hi'/'lo' son 200 barın %90/%10 dilimi (nedensel)
    seyrekse (geçerli <%5): olay kanalı gibi 'on'
Çizim olayları (EK-P4; label/box/line.new — oluşturulduğu bar): 'on'; etikette 'up'/'dn' stil (label_up/arrowup… /
    label_down/arrowdown…) ya da stil yoksa metin (buy/long/bull … / sell/short/bear …); renk sınıfı dolgu rengi (nötrse
    yazı/kenar rengi).
Renkli kanallarda yeşil/kırmızı ikisi de ≥%1 ise 'col+'/'col-'.
Elemeler: görülme oranı <%0,2 ya da >%99,8 → atılır; aynı dizi tekrarı atılır; script başına en çok 40 durum.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_STATES = 40
MIN_RATE, MAX_RATE = 0.002, 0.998
PRICE_SCALE = 0.25
OSC_SIGN_MIN = 0.05
COLOR_MIN = 0.01
Q_WIN = 200


def _slope(v):
    prev = np.r_[np.nan, v[:-1]]
    ok = ~np.isnan(v) & ~np.isnan(prev)
    return ok & (v > prev), ok & (v < prev)


def _roll_q(v, q):
    return pd.Series(v).rolling(Q_WIN, min_periods=Q_WIN // 2).quantile(q).values


def channel_states(kind: str, v: np.ndarray, c: np.ndarray, close: np.ndarray) -> dict:
    out = {}
    valid = ~np.isnan(v)
    if kind == "entry":
        out["long"], out["short"] = valid & (v > 0), valid & (v < 0)
    elif kind == "arrow":
        out["up"], out["dn"] = valid & (v > 0), valid & (v < 0)
    elif kind in ("label", "box", "line"):                 # EK-P4: çizim oluşturma olayları
        out["on"] = valid
        if kind == "label":
            out["up"], out["dn"] = valid & (v == 1), valid & (v == -1)
    elif kind != "plot" or valid.mean() < 0.05:
        out["on"] = valid & (v != 0)
    else:
        vv = np.where(valid, v, np.nan)
        med = np.nanmedian(np.abs(vv / close - 1)) if valid.any() else np.inf
        out["up"], out["dn"] = _slope(vv)
        if med < PRICE_SCALE:
            out["px+"], out["px-"] = valid & (close > vv), valid & (close < vv)
        else:
            pos, neg = (vv > 0).mean(), (vv < 0).mean()
            if pos >= OSC_SIGN_MIN and neg >= OSC_SIGN_MIN:
                out["z+"], out["z-"] = valid & (vv > 0), valid & (vv < 0)
            hi, lo = _roll_q(vv, 0.9), _roll_q(vv, 0.1)
            out["hi"] = valid & ~np.isnan(hi) & (vv > hi)
            out["lo"] = valid & ~np.isnan(lo) & (vv < lo)
    if c is not None and np.isfinite(c).any():
        g, r = c == 1, c == -1
        if g.mean() >= COLOR_MIN and r.mean() >= COLOR_MIN:
            out["col+"], out["col-"] = g, r
    return out


def script_states(outputs: dict, close: np.ndarray) -> dict:
    states, seen = {}, set()
    for site, rec in outputs.items():
        kind = rec["kind"]
        title = (rec.get("title") or "")[:30] if isinstance(rec.get("title"), str) else ""
        for sname, arr in channel_states(kind, rec["v"].astype(float), rec["c"].astype(float), close).items():
            arr = np.asarray(arr, bool)
            rate = arr.mean()
            if rate < MIN_RATE or rate > MAX_RATE:
                continue
            key = np.packbits(arr).tobytes()
            if key in seen:
                continue
            seen.add(key)
            states[f"{kind}{site}|{title}|{sname}"] = arr
            if len(states) >= MAX_STATES:
                return states
    return states
