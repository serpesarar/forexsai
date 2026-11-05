"""DTS-02 — repo ORB zinciri (entry: aralık sonrası ilk kapanış > aralık tepesi; exit: or_mid stop, 2R, kapanışta düz).
Ön-kayıt: PROTOCOL.md. Kart ölçütleri: n≥150, ortR>0 & P≥0,90, iki yarı ≥0, spread×1,5>0, iyimser−gerçekçi ≤ ortR/2."""
import itertools, json, zlib
from multiprocessing import Pool
import numpy as np
import pandas as pd
from common import SPREAD, load, month_boot

SESS = {"NDX": ("America/New_York", "09:30", "15:55"), "GDAXI": ("Europe/Berlin", "09:00", "17:25"),
        "XAUUSD": ("America/New_York", "08:20", "13:25"), "USOIL": ("America/New_York", "09:00", "14:25")}
TFS = {"NDX": ("5m", "15m"), "GDAXI": ("15m",), "XAUUSD": ("5m", "15m"), "USOIL": ("5m", "15m")}
ORS, STOPS, TGTS, SIDES = (15, 30), ("or_mid", "or_low", "atr1.5"), (2.0, 1.0), ("long", "short")
LAST_ENTRY_MIN, MIN_RISK = 25, 0.0005


def hm(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)


def days_of(d, sym):
    tz, op, fl = SESS[sym]
    loc = d.ts.dt.tz_convert(tz)
    mins = (loc.dt.hour * 60 + loc.dt.minute).to_numpy(); date = loc.dt.date.to_numpy()
    o0, f0 = hm(op), hm(fl)
    keep = (mins >= o0) & (mins < f0)
    out = {}
    for i in np.flatnonzero(keep):
        out.setdefault(date[i], []).append(i)
    return out, mins


def atr14(d):
    c = d.close.to_numpy(); pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(d.high - d.low, np.maximum(abs(d.high - pc), abs(d.low - pc))).to_numpy()
    return pd.Series(tr).rolling(14).mean().to_numpy()


def trade(d, idx, mins, o0, f0, orm, bar_min, stop, tgt, side, sp, optimistic):
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    rng = [i for i in idx if mins[i] < o0 + orm]
    if len(rng) * bar_min < orm:
        return None
    oh, ol = h[rng].max(), l[rng].min()
    post = [i for i in idx if mins[i] >= o0 + orm]
    long = side == "long"
    for p, k in enumerate(post):
        if mins[k] + bar_min > f0 - LAST_ENTRY_MIN:
            return None
        if (c[k] > oh) if long else (c[k] < ol):
            break
    else:
        return None
    rest = post[p + 1:]
    if not rest:
        return None
    if optimistic:
        e, walk = c[k], rest
    else:
        e, walk = (o[rest[0]] + sp) if long else (o[rest[0]] - sp), rest
    if stop == "or_mid":
        st = (oh + ol) / 2
    elif stop == "or_low":
        st = ol if long else oh
    else:
        a = ATR[k]
        if not np.isfinite(a):
            return None
        st = e - 1.5 * a if long else e + 1.5 * a
    risk = (e - st) if long else (st - e)
    if risk <= MIN_RISK * e:
        return None
    tg = e + tgt * risk if long else e - tgt * risk
    for j in walk:
        if (l[j] <= st) if long else (h[j] >= st):
            return -1.0
        if (h[j] >= tg) if long else (l[j] <= tg):
            return tgt
    x = c[walk[-1]]
    return ((x - e) if long else (e - x)) / risk


def run(sym_tf):
    global ATR
    sym, tf = sym_tf
    d = load(sym, tf); ATR = atr14(d); bar_min = int(tf[:-1])
    days, mins = days_of(d, sym); o0, f0 = hm(SESS[sym][1]), hm(SESS[sym][2]); sp = SPREAD[sym]
    dates = sorted(days); mid = dates[len(dates) // 2]
    rows = []
    for orm, stop, tgt, side in itertools.product(ORS, STOPS, TGTS, SIDES):
        R, Ro, Rs, dd = [], [], [], []
        for dt in dates:
            idx = days[dt]
            r = trade(d, idx, mins, o0, f0, orm, bar_min, stop, tgt, side, sp, False)
            if r is None:
                continue
            R.append(r); dd.append(dt)
            Ro.append(trade(d, idx, mins, o0, f0, orm, bar_min, stop, tgt, side, sp, True))
            Rs.append(trade(d, idx, mins, o0, f0, orm, bar_min, stop, tgt, side, sp * 1.5, False))
        R = np.array(R, float); Ro = np.array([x if x is not None else np.nan for x in Ro]); Rs = np.array([x if x is not None else np.nan for x in Rs])
        if len(R) == 0:
            continue
        dd = np.array(dd); months = np.array([str(x)[:7] for x in dd]); first = dd < mid
        seed = zlib.crc32(f"{sym}{tf}{orm}{stop}{tgt}{side}".encode())
        ortR = float(R.mean())
        rows.append({"sym": sym, "tf": tf, "or": orm, "stop": stop, "tgt": tgt, "side": side, "n": len(R),
                     "WR": float((R > 0).mean()), "ortR": ortR, "P": month_boot(R, months, seed),
                     "y1": float(R[first].mean()) if first.any() else np.nan, "y2": float(R[~first].mean()) if (~first).any() else np.nan,
                     "stres": float(np.nanmean(Rs)), "iyimser": float(np.nanmean(Ro)), "ilk": str(dates[0]), "son": str(dates[-1])})
    return rows


def main():
    jobs = [(s, t) for s in TFS for t in TFS[s]]
    with Pool(6) as p:
        rows = sum(p.map(run, jobs), [])
    df = pd.DataFrame(rows)
    df["icra_farki"] = df.iyimser - df.ortR
    df["kart"] = (df.n >= 150) & (df.ortR > 0) & (df.P >= 0.90) & (df.y1 >= 0) & (df.y2 >= 0) & (df.stres > 0) & (df.icra_farki <= df.ortR / 2)
    prim = df[(df["or"] == 15) & (df.stop == "or_mid") & (df.tgt == 2.0) & (df.side == "long") &
              (((df.sym != "GDAXI") & (df.tf == "5m")) | ((df.sym == "GDAXI") & (df.tf == "15m")))]
    df.to_csv("dts02_hucreler.csv", index=False)
    pd.set_option("display.width", 230); pd.set_option("display.max_rows", 300)
    print("BİRİNCİL (repo varsayılanı):"); print(prim.round(3).to_string(index=False))
    print(f"\nkart geçen hücre: {int(df.kart.sum())} / {len(df)}; ortR>0 & P≥0,975 hücre: {int(((df.ortR>0)&(df.P>=0.975)).sum())}, ters (P≤0,025): {int((df.P<=0.025).sum())}")
    print(df[df.kart].round(3).to_string(index=False))
    print(df.groupby(["sym", "side"]).agg(hucre=("ortR", "size"), ort=("ortR", "mean"), poz=("ortR", lambda x: int((x > 0).sum()))).round(3).to_string())
    json.dump({"birincil": prim.to_dict("records"), "kart_gecen": int(df.kart.sum()), "hucre": len(df)}, open("dts02_ozet.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
