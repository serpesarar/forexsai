"""destek.py — K1 + XP: geçmiş günlerin/haftaların desteklerine limit girişi + hayalet seviye (E105) + tepki testi.

python destek.py test   # birim testleri
python destek.py kos    # tüm beslemeler → results/destek.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/xp_limit_20261118/src"))
import xl  # noqa: E402  (rapor + G + FIN)

R, G, NY, FIN = xl.R, xl.G, xl.NY, xl.FIN
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
ESKI_END = pd.Timestamp("2021-10-31")
DMIN, DMAX = 15, 300          # seviye uzaklığı bp aralığı
GRID = np.arange(DMIN, DMAX + 1)
REACT_BP = 50.0               # tepki: ±50 bp yarışı
NPERM = 500
FAMS = ["D5", "D5_2", "D20", "P5", "P20", "W8"]
PIV = 3                       # fraktal: iki yanda 3 mum


def ts(d, hh: int, mm: int) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def trading_days(b: pd.DataFrame, step: int) -> list:
    dp = G.day_prices(b, NY, [570, 900, 960], step)
    return [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]


def hourly(b: pd.DataFrame) -> pd.DataFrame:
    h = b.assign(hb=(b.t // 3600) * 3600).groupby("hb").agg(l=("l", "min"))
    return h.reset_index()


def pivots(hr: pd.DataFrame) -> pd.DataFrame:
    """Fraktal salınım dipleri; conf_t = onay mumunun (k+PIV) kapanış zamanı."""
    l = hr.l.values
    n = len(l)
    ok = np.zeros(n, bool)
    for k in range(PIV, n - PIV):
        if l[k] < l[k - PIV:k].min() and l[k] < l[k + 1:k + 1 + PIV].min():
            ok[k] = True
    idx = np.flatnonzero(ok)
    return pd.DataFrame({"t": hr.hb.values[idx], "conf_t": hr.hb.values[idx + PIV] + 3600, "l": l[idx]})


def nearest_below(cands: np.ndarray, ask0: float, rank: int = 0) -> float:
    """ask0'ın DMIN..DMAX bp altındaki adaylardan en yakın (rank=1: ikinci) seviye."""
    c = np.asarray(cands, float)
    c = c[np.isfinite(c)]
    dist = (ask0 - c) / ask0 * 1e4
    c = np.unique(c[(dist >= DMIN) & (dist <= DMAX)])[::-1]   # yüksekten alçağa = yakından uzağa
    return float(c[rank]) if len(c) > rank else np.nan


def levels_for(i: int, days: list, daylow: pd.Series, weeklow: pd.Series, piv: pd.DataFrame, ask0: float, u0: int) -> dict:
    a = days[i]
    prev5, prev20 = days[max(0, i - 5):i], days[max(0, i - 20):i]
    d5 = daylow.reindex(prev5).values
    d20 = daylow.reindex(prev20).values
    wk = pd.Timestamp(a) - pd.Timedelta(days=pd.Timestamp(a).weekday())
    w8 = weeklow[weeklow.index < wk].tail(8).values
    out = {"D5": nearest_below(d5, ask0), "D5_2": nearest_below(d5, ask0, 1), "D20": nearest_below(d20, ask0), "W8": nearest_below(w8, ask0)}
    for nm, back in (("P5", prev5), ("P20", prev20)):
        start = ts(back[0], 0, 0) if back else u0
        p = piv[(piv.t >= start) & (piv.conf_t <= u0)].l.values
        out[nm] = nearest_below(p, ask0)
    return out


def path_tables(o, h, l, sp, i0: int, iend: int, ix: int, ask0: float, px_out: float, fin: float):
    """Her ızgara uzaklığı (bp) için: limit dolum değeri (W) ve tepki sonucu (+1 yukarı / 0 aşağı / nan çözülmedi)."""
    ask_low = l[i0:iend] + sp[i0:iend]
    cm = np.minimum.accumulate(ask_low)
    L = ask0 * (1 - GRID / 1e4)
    k = np.searchsorted(-cm, -L, side="left")          # cm azalan: cm[k] <= L olan ilk k
    filled = k < len(cm)
    fill_px = np.where(filled, np.minimum(L, o[i0 + np.minimum(k, len(cm) - 1)] + sp[i0 + np.minimum(k, len(cm) - 1)]), np.nan)
    val = np.where(filled, (px_out / fill_px - 1) * 1e4 - fin, np.nan)
    react = np.full(len(GRID), np.nan)
    hh, ll = h[:ix], l[:ix]
    for g in np.flatnonzero(filled):
        s = i0 + k[g] + 1
        if s >= ix:
            continue
        up = np.flatnonzero(hh[s:] >= L[g] * (1 + REACT_BP / 1e4))
        dn = np.flatnonzero(ll[s:] <= L[g] * (1 - REACT_BP / 1e4))
        fu = up[0] if up.size else np.inf
        fd = dn[0] if dn.size else np.inf
        if np.isinf(fu) and np.isinf(fd):
            continue
        react[g] = 1.0 if fu < fd else 0.0               # aynı mum → aşağı (muhafazakâr)
    return val, react


def build(name: str, b: pd.DataFrame, step: int) -> pd.DataFrame:
    sg = xl.signals(b, step)
    days = trading_days(b, step)
    pos = {d: i for i, d in enumerate(days)}
    x = G._local(b, NY)
    daylow = x.groupby("day").l.min()
    dl = daylow.copy()
    dl.index = pd.to_datetime(dl.index)
    weeklow = dl.groupby(dl.index - pd.to_timedelta(dl.index.weekday, unit="D")).min()
    piv = pivots(hourly(b))
    t, o, h, l, sp = b.t.values, b.o.values, b.h.values, b.l.values, b.sp.values
    tol = 300 if step == 60 else step
    rows = []
    for r in sg.itertuples():
        if r.d not in pos:
            continue
        u0, ux, un = ts(r.d, 16, 0), ts(r.ex, 16, 0), ts(r.nxt, 16, 0)
        i0, ix, inx = (int(np.searchsorted(t, u)) for u in (u0, ux, un))
        if i0 >= len(t) or t[i0] - u0 > tol or ix >= len(t) or t[ix] - ux > tol:
            continue
        ask0, px_out = o[i0] + sp[i0], o[ix]
        fin = FIN * (pd.Timestamp(r.ex) - pd.Timestamp(r.d)).days
        base = (px_out / ask0 - 1) * 1e4 - fin
        lv = levels_for(pos[r.d], days, daylow, weeklow, piv, ask0, u0)
        vW2, rW2 = path_tables(o, h, l, sp, i0, ix, ix, ask0, px_out, fin)
        vW1, _ = path_tables(o, h, l, sp, i0, inx, ix, ask0, px_out, fin)
        rec = {"d": pd.Timestamp(r.d), "base": base, "ask0": ask0, "vW2": vW2, "vW1": vW1, "rW2": rW2}
        for f in FAMS:
            rec[f] = lv[f]
            rec[f + "_bp"] = (ask0 - lv[f]) / ask0 * 1e4 if np.isfinite(lv[f]) else np.nan
        rows.append(rec)
    print(name, "sinyal", len(rows), flush=True)
    return pd.DataFrame(rows)


def at(arr: np.ndarray, dist_bp: float) -> float:
    return arr[int(round(dist_bp)) - DMIN]


def per_signal(z: pd.DataFrame, dist: np.ndarray, win: str, rule: str, M: dict | None = None) -> np.ndarray:
    """Sinyal başı değer. dist nan → seviye yok: A=0, B=piyasa. YARIM: ½ piyasa + ½ limit(dolmazsa 0)."""
    M = M or mats(z)
    base = z.base.values
    has = np.isfinite(dist)
    col = np.where(has, np.rint(np.nan_to_num(dist, nan=DMIN)).astype(int) - DMIN, 0)
    v = M["v" + win][np.arange(len(z)), col]
    lim = np.where(np.isfinite(v), v, 0.0)
    val = 0.5 * base + 0.5 * lim if rule == "YARIM" else lim
    return np.where(has, val, 0.0 if rule == "A" else base)


def mats(z: pd.DataFrame) -> dict:
    return {k: np.stack(z[k].values) if len(z) else np.zeros((0, len(GRID))) for k in ("vW2", "vW1", "rW2")}


def summ(v: np.ndarray, d: pd.Series) -> dict:
    eq = pd.Series(v, index=d.values).sort_index().cumsum()
    nz = v
    return {"ort": round(float(nz.mean()), 1), "toplam": round(float(nz.sum()), 0), "en_kotu": round(float(nz.min()), 1),
            "kotu10": round(float(np.sort(nz)[:max(1, len(nz) // 10)].mean()), 1), "maksDD": round(float((eq - eq.cummax()).min()), 0)}


def react_rate(z: pd.DataFrame, dist: np.ndarray, M: dict | None = None) -> tuple[float, int]:
    M = M or mats(z)
    has = np.isfinite(dist)
    col = np.rint(dist[has]).astype(int) - DMIN
    v = M["rW2"][np.flatnonzero(has), col]
    v = v[np.isfinite(v)]
    return (float(v.mean()) if len(v) else np.nan), len(v)


def analyse(S: pd.DataFrame, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    out = {}
    for era, m in (("TUM", np.ones(len(S), bool)), ("KESIF", (S.d <= ESKI_END).values), ("TEST", (S.d > ESKI_END).values)):
        z = S[m].reset_index(drop=True)
        rec = {"n_sinyal": len(z), "piyasa": summ(z.base.values, z.d)}
        M = mats(z)
        for f in FAMS:
            dist = z[f + "_bp"].values
            has = np.isfinite(dist)
            fr = {"seviye_var_%": round(float(has.mean() * 100), 1), "uzaklik_medyan_bp": round(float(np.nanmedian(dist)), 1) if has.any() else None}
            for win in ("W2", "W1"):
                for rule in ("B", "A", "YARIM"):
                    v = per_signal(z, dist, win, rule, M)
                    fr[f"{win}_{rule}"] = summ(v, z.d)
            filled = np.isfinite(M["vW2"][np.flatnonzero(has), np.rint(dist[has]).astype(int) - DMIN]) if has.any() else np.array([], bool)
            fr["dolum_%"] = round(float(filled.mean() * 100), 1) if filled.size else None
            base_h = z.base.values[has]
            if filled.size:
                fr["kacan_piyasa_ort"] = round(float(base_h[~filled].mean()), 1) if (~filled).any() else None
                fr["kacan_kazanan_%"] = round(float((base_h[~filled] > 0).mean() * 100), 1) if (~filled).any() else None
            # hayalet: uzaklıkları seviyesi olan sinyaller arasında karıştır
            real_v = per_signal(z, dist, "W2", "B", M).mean()
            rr, nr = react_rate(z, dist, M)
            gv, gr = [], []
            idx = np.flatnonzero(has)
            for _ in range(NPERM):
                gd = dist.copy()
                gd[idx] = dist[rng.permutation(idx)]
                gv.append(per_signal(z, gd, "W2", "B", M).mean())
                gr.append(react_rate(z, gd, M)[0])
            gv, gr = np.array(gv), np.array(gr)
            fr["hayalet"] = {"gercek_ort": round(float(real_v), 1), "hayalet_ort": round(float(gv.mean()), 1), "P_gercek_ust": round(float((real_v > gv).mean()), 3),
                             "tepki_gercek_%": round(rr * 100, 1) if np.isfinite(rr) else None, "tepki_n": nr,
                             "tepki_hayalet_%": round(float(np.nanmean(gr)) * 100, 1), "P_tepki_ust": round(float((rr > gr).mean()), 3)}
            rec[f] = fr
        out[era] = rec
    return out


def unit_tests() -> None:
    assert nearest_below(np.array([99.0, 98.0, 99.9, 90.0]), 100.0) == 99.0          # 99.9 = 10 bp < DMIN elenir
    assert nearest_below(np.array([99.0, 98.0, 99.9]), 100.0, 1) == 98.0
    assert np.isnan(nearest_below(np.array([50.0]), 100.0))                          # 5000 bp > DMAX
    hr = pd.DataFrame({"hb": np.arange(10) * 3600, "l": [5, 4, 3, 2, 1, 2, 3, 4, 5, 6.0]})
    p = pivots(hr)
    assert len(p) == 1 and p.l.iloc[0] == 1 and p.conf_t.iloc[0] == 8 * 3600       # dip 4. mum, onay 7. mumun kapanışı
    # yol: ask0=100, dip 98.5 → 150 bp limit dolar, 160 bp dolmaz
    n = 6
    o = np.array([100, 99, 98.6, 99, 100, 101.0]); h = o + 0.2; l = np.array([99.8, 98.8, 98.5, 98.9, 99.9, 100.9]); sp = np.zeros(n)
    v, r = path_tables(o, h, l, sp, 0, 5, 5, 100.0, 101.0, 0.0)
    assert np.isfinite(at(v, 150)) and np.isnan(at(v, 160))
    assert abs(at(v, 150) - (101 / 98.5 - 1) * 1e4) < 1e-6
    print("birim testleri geçti")


def main() -> None:
    RES.mkdir(exist_ok=True)
    feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (R.KD.mt5_m30("NAS100"), 1800), "MT5_US500": (R.KD.mt5_m30("US500", "2018-06-01"), 1800),
             "MT5_US30": (R.KD.mt5_m30("US30"), 1800), "MT5_US2000": (R.KD.mt5_m30("US2000"), 1800)}
    res, lv = {}, []
    for nm, (b, st) in feeds.items():
        S = build(nm, b, st)
        res[nm] = analyse(S)
        lv.append(S[["d", "ask0", "base"] + FAMS + [f + "_bp" for f in FAMS]].assign(besleme=nm))
        (RES / "destek.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    pd.concat(lv).to_csv(RES / "seviyeler.csv", index=False)


if __name__ == "__main__":
    unit_tests() if sys.argv[1] == "test" else (unit_tests(), main())
