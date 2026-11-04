"""prereg.md §5 sinyal tanımları → olay listeleri (karar dakikası t; giriş e = t+1) → cache/signals.pkl

Her kayıt: hid (hipotez ID), par (hücre parametresi), dir (+1 BUY / -1 SELL), kind (event|regime), Hset, t (np.int64 dizi).
Geometri (r × H) çaprazlaması 04_eval.py'de yapılır.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

G6 = (15, 60)


def metrics_table() -> pd.DataFrame:
    m = pd.read_parquet(C.DATA / "metrics_5m_effective.parquet")
    m = m.sort_values("eff_ts").reset_index(drop=True)
    m["em"] = ((m["eff_ts"] - C.T0) / pd.Timedelta(minutes=1)).astype(np.int64)
    m = m[(m["em"] >= 0) & (m["em"] < C.N - 2)].reset_index(drop=True)
    return m


def add(sig: list, hid: str, par: str, d: int, kind: str, t: np.ndarray, Hset=G6, ep: bool = True) -> None:
    t = np.asarray(t, dtype=np.int64)
    t = t[(t >= 1) & (t < C.N - 2)]
    if ep:
        t = C.episode(t)
    else:
        t = np.sort(np.unique(t))
    sig.append({"hid": hid, "par": par, "dir": d, "kind": kind, "Hset": Hset, "t": t})


def main() -> None:
    B = np.load(C.CACHE / "base.npz")
    o, c, perp = B["o"], B["c"], B["perp_close"]
    m = metrics_table()
    em = m["em"].to_numpy()
    pos = pd.Series(np.arange(len(m)), index=em)
    # nedensellik kontrolü: 1m ızgarada t=em satırının metrics_eff_ts'i em olmalı
    meff = B["m_eff"]
    samp = em[::997]
    ok = np.isclose(meff[samp], samp) | np.isnan(meff[samp])
    print("metrics hizalama (t=eff satırı eff'i görüyor):", ok.mean())
    sig: list = []

    # ---------- DV01 OI × fiyat ----------
    oi = m["sum_open_interest"].to_numpy(np.float64)
    for W in (15, 60):
        j = pos.reindex(em - W).to_numpy()
        has = ~np.isnan(j)
        doi = np.full(len(m), np.nan)
        jj = j[has].astype(np.int64)
        doi[has] = oi[has] / oi[jj] - 1
        dP = np.full(len(m), np.nan)
        a = em - 1
        b = em - W - 1
        okp = b >= 0
        dP[okp] = np.log(perp[a[okp]] / perp[b[okp]])
        zP = C.roll_z(pd.Series(dP), 8640, 2000, center=False).to_numpy()
        zO = C.roll_z(pd.Series(doi).replace([np.inf, -np.inf], np.nan), 8640, 2000).to_numpy()
        for k in (1.5, 2.5):
            par = f"W{W}_k{k}"
            q = {
                "a": (zP >= k) & (zO >= k), "b": (zP >= k) & (zO <= -k),
                "c": (zP <= -k) & (zO >= k), "d": (zP <= -k) & (zO <= -k),
            }
            # a: yeni long (C=BUY, R=SELL); b: short kapatma (R=SELL, C=BUY); c: yeni short (C=SELL, R=BUY); d: long tasfiye (R=BUY, C=SELL)
            dirs = {"a": {"C": 1, "R": -1}, "b": {"R": -1, "C": 1}, "c": {"C": -1, "R": 1}, "d": {"R": 1, "C": -1}}
            for qn, msk in q.items():
                for mode, d in dirs[qn].items():
                    add(sig, f"DV01{qn}-{mode}", par, d, "event", em[msk])

    # ---------- DV02 tasfiye vekilleri ----------
    zoi = m["z_oi"].to_numpy()
    for side, col in (("L", "liq_proxy_long_5m"), ("S", "liq_proxy_short_5m")):
        t5 = em[m[col].to_numpy() == 1]
        fade = 1 if side == "L" else -1
        add(sig, f"DV02-P5{side}-F", "P5", fade, "event", t5)
        add(sig, f"DV02-P5{side}-W", "P5", -fade, "event", t5)
        t1 = np.where(B["p1L" if side == "L" else "p1S"] == 1)[0]
        add(sig, f"DV02-P1{side}-F", "P1", fade, "event", t1)
        add(sig, f"DV02-P1{side}-W", "P1", -fade, "event", t1)
        effc = 5 * ((t1 + 1 + 4) // 5)  # t1 dakikasını içeren [eff-5, eff) penceresinin sonu
        jj = pos.reindex(effc).to_numpy()
        hv = ~np.isnan(jj)
        conf = np.zeros(len(t1), dtype=bool)
        conf[hv] = zoi[jj[hv].astype(np.int64)] <= -2
        tc = effc[conf]
        add(sig, f"DV02-P1o{side}-F", "P1oi", fade, "event", tc)
        add(sig, f"DV02-P1o{side}-W", "P1oi", -fade, "event", tc)

    # ---------- DV03 funding ----------
    fp, fl, flt, mtnf, a1 = B["fp"], B["fl"], B["fl_time"], B["mtnf"], B["atr1"]
    tt = np.arange(C.N)
    hourly = (tt % 60 == 0)
    for th in (1.5, 3.0):
        add(sig, "DV03a-L", f"th{th}", -1, "regime", tt[hourly & (mtnf <= 450) & (fp >= th)], ep=False)
    for th in (0.0, -1.0):
        cond = (fp < 0) if th == 0.0 else (fp <= th)
        add(sig, "DV03a-S", f"th{th}", 1, "regime", tt[hourly & (mtnf <= 450) & cond], ep=False)
    body = c - o
    add(sig, "DV03b-L", "th1.5", -1, "event", tt[(fp >= 1.5) & (body <= -2 * a1)])
    add(sig, "DV03b-S", "th0", 1, "event", tt[(fp <= 0) & (body >= 2 * a1)])
    S = np.arange(480, C.N, 480)
    tpre = S - 31
    for th in (1.5, 3.0):
        add(sig, "DV03c-L", f"th{th}", -1, "event", tpre[fp[tpre] >= th], Hset=(35,), ep=False)
    for th in (0.0, -1.0):
        cond = (fp[tpre] < 0) if th == 0.0 else (fp[tpre] <= th)
        add(sig, "DV03c-S", f"th{th}", 1, "event", tpre[cond], Hset=(35,), ep=False)
    Sv = S[np.isclose(flt[S], S)]
    print("DV03d uzlaşma satırı eşleşmesi:", len(Sv), "/", len(S))
    for th in (1.5, 3.0):
        add(sig, "DV03d-L", f"th{th}", 1, "event", Sv[fl[Sv] >= th], ep=False)
    for th in (0.0, -1.0):
        cond = (fl[Sv] < 0) if th == 0.0 else (fl[Sv] <= th)
        add(sig, "DV03d-S", f"th{th}", -1, "event", Sv[cond], ep=False)

    # ---------- DV04 premium / baz ----------
    prem = pd.Series(B["prem"])
    zp = C.roll_z(prem, 1440, 1000).to_numpy()
    for k in (3.0, 5.0):
        add(sig, "DV04a-H", f"k{k}", -1, "event", tt[zp >= k])
        add(sig, "DV04a-L", f"k{k}", 1, "event", tt[zp <= -k])
    lc = np.log(c)
    r5 = np.full(C.N, np.nan)
    r5[5:] = lc[5:] - lc[:-5]
    z5 = C.roll_z(pd.Series(r5), 43200, 10000, center=False).to_numpy()
    bas = B["basis"]
    db = np.full(C.N, np.nan)
    db[5:] = bas[5:] - bas[:-5]
    for bb in (1.0, 3.0):
        par = f"b{bb}"
        add(sig, "DV04b-U", par, -1, "event", tt[(z5 >= 3) & (db >= bb)])
        add(sig, "DV04b-D", par, 1, "event", tt[(z5 <= -3) & (db <= -bb)])
        add(sig, "DV04c-U", par, 1, "event", tt[(z5 >= 3) & (db <= -bb)])
        add(sig, "DV04c-D", par, -1, "event", tt[(z5 <= -3) & (db >= bb)])

    # ---------- DV05 L/S oranları ----------
    def zser(col: str) -> np.ndarray:
        x = np.log(m[col].astype(float).where(m[col] > 0))
        return C.roll_z(x, 8640, 2000).to_numpy()

    zt, zg = zser("sum_toptrader_long_short_ratio"), zser("count_long_short_ratio")
    th_ = tt[hourly]
    # karar barı t: eff ≤ t olan son metrics satırı, yaş (t+1-eff) ≤ 15
    ii = np.searchsorted(em, th_, side="right") - 1
    okk = (ii >= 0)
    ii = np.where(okk, ii, 0)
    fresh = okk & ((th_ + 1 - em[ii]) <= 15)
    ztt = np.where(fresh, zt[ii], np.nan)
    zgg = np.where(fresh, zg[ii], np.nan)
    for k in (2.0, 3.0):
        add(sig, "DV05-TOP-L", f"k{k}", -1, "regime", th_[ztt >= k], ep=False)
        add(sig, "DV05-TOP-S", f"k{k}", 1, "regime", th_[ztt <= -k], ep=False)
        add(sig, "DV05-GLB-L", f"k{k}", -1, "regime", th_[zgg >= k], ep=False)
        add(sig, "DV05-GLB-S", f"k{k}", 1, "regime", th_[zgg <= -k], ep=False)
    add(sig, "DV05-DIV-B", "d", 1, "regime", th_[(ztt >= 2) & (zgg <= -1)], ep=False)
    add(sig, "DV05-DIV-S", "d", -1, "regime", th_[(ztt <= -2) & (zgg >= 1)], ep=False)

    with open(C.CACHE / "signals.pkl", "wb") as f:
        pickle.dump(sig, f)
    rows = []
    for s in sig:
        sg = C.seg_of(s["t"] + 1)
        rows.append({"hid": s["hid"], "par": s["par"], "dir": s["dir"], "kind": s["kind"], "n_all": len(s["t"]),
                     "n_DISC": int((sg == 0).sum()), "n_OOS": int((sg == 1).sum()), "n_BLIND": int((sg == 2).sum())})
    df = pd.DataFrame(rows)
    C.OUT.mkdir(exist_ok=True, parents=True)
    df.to_csv(C.OUT / "event_counts.csv", index=False)
    pd.set_option("display.width", 200)
    print(df.to_string())
    print("hipotez sayısı", df["hid"].nunique(), "sinyal hücresi", len(df))


if __name__ == "__main__":
    main()
