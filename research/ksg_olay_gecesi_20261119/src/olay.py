"""olay.py — KSG × olay öncesi gece bileşik sınaması (PROTOCOL OG-01). python olay.py"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES = HERE / "results"
for p in ("research/ksg_opex_canli_20261119/src", "research/korku_evren_20261119/src", "research/ndx_10y_1m_20261116/src",
          "research/ndx_tf_yapilandirma_20261117/src"):
    sys.path.insert(0, str(ROOT / p))
import oynat as Oy  # noqa: E402
import esik as E  # noqa: E402
import lib  # noqa: E402

NY = "America/New_York"
S_FEEDS = ["MT5_NAS100", "DUKA_NDX", "MT5_US500", "MT5_US30", "MT5_US2000"]
BLIND = ["MT5_US500", "MT5_US30", "MT5_US2000"]
ETFS = ["QQQ", "SPY", "DIA", "IWM"]
KESIF_SON = pd.Timestamp("2021-10-31")
U2_SPLIT = pd.Timestamp("2013-03-01")
DOSE = 1.5
NB = 3000
RNG = np.random.default_rng(53)


# ---------------- takvim ----------------
def calendar() -> dict:
    ev = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev["date"] = pd.to_datetime(ev.date)
    ern = json.loads((ROOT / "research/ksg_derin_20261119/data/earnings.json").read_text())
    return {"FOMC": set(ev[ev.event == "FOMC"].date), "CPI": set(ev[ev.event == "CPI"].date), "NFP": set(ev[ev.event == "NFP"].date),
            "BIL": {pd.Timestamp(k) for k in ern}}


def tag(N: pd.DataFrame, C: dict) -> pd.DataFrame:
    N = N.copy()
    N["fomc"] = N.nd.isin(C["FOMC"])
    N["cpi"] = N.nd.isin(C["CPI"])
    N["nfp"] = N.nd.isin(C["NFP"])
    N["bil"] = N.d.isin(C["BIL"])
    N["O"] = N.fomc | N.cpi | N.nfp | N.bil
    N["yeni"] = (N.nfp | N.bil) & ~N.fomc & ~N.cpi
    N["blk"] = N.d.dt.to_period("M").astype(str)
    return N


# ---------------- geceler ----------------
def nights_intraday(b: pd.DataFrame, fin: float) -> pd.DataFrame:
    """Tüm işlem günleri: d 16:00 açılış + spread → nd 09:30 açılış; ksg = 16:00 < 15:00 (M30 açılışları, canlı kodla aynı)."""
    ny = pd.to_datetime(b.t, unit="s", utc=True).dt.tz_convert(NY)
    b = b.assign(day=ny.dt.date, hm=ny.dt.hour * 60 + ny.dt.minute)
    by = {k: g.set_index("hm") for k, g in b.groupby("day")}
    days = sorted(k for k in by if k.weekday() < 5 and not lib.nyse.is_holiday(k))
    rows = []
    for i, d in enumerate(days[:-1]):
        g, nd = by[d], days[i + 1]
        if lib.nyse.is_early_close(d) or not {900, 960}.issubset(g.index) or 570 not in by[nd].index or (nd - d).days > 5:
            continue
        o15, o16 = float(g.loc[900, "o"]), float(g.loc[960, "o"])
        ask = o16 + float(g.loc[960, "sp"])
        net = (float(by[nd].loc[570, "o"]) / ask - 1) * 1e4 - fin * (nd - d).days
        rows.append({"d": pd.Timestamp(d), "nd": pd.Timestamp(nd), "net": net, "ksg": o16 < o15})
    return pd.DataFrame(rows)


def feed_S(name: str) -> pd.DataFrame:
    b = Oy.bars30(name)
    N = nights_intraday(b, E.VR.FIN)
    return N[N.d >= ("2018-06-01" if name == "MT5_US500" else "2018-05-25")]


def feed_U1(name: str) -> pd.DataFrame:
    import kaynak
    if name == "DUKA_M30_2016_17":
        d = kaynak.load_duka_m30_export()
    else:
        d = pd.read_parquet(ROOT / "research/ndx_tf_yapilandirma_20261117/out/ek/EET30_kalibre.parquet")
    d = d.sort_values("t").drop_duplicates("t")
    d = d[d.t < int(pd.Timestamp("2018-01-01", tz="UTC").timestamp())]
    b = pd.DataFrame({"t": d.t.values.astype(np.int64), "o": d.open.values, "sp": np.full(len(d), 1.5)})
    return nights_intraday(b, lib.FIN_BP_PER_DAY)


def feed_daily(sym: str, start: str, end: str) -> pd.DataFrame:
    v = pd.read_parquet(ROOT / f"research/qs03_akis_takvim_20261111/data/{sym}.parquet")
    if isinstance(v.columns, pd.MultiIndex):
        v.columns = v.columns.get_level_values(0)
    v.index = pd.to_datetime(v.index).tz_localize(None).normalize()
    v = v[(v.index >= start) & (v.index <= end)]
    d, nd = v.index[:-1], v.index[1:]
    c, o = v.Close.values[:-1], v.Open.values[1:]
    div = v.Dividends.values[1:] if "Dividends" in v else 0.0
    gap = (nd - d).days
    net = ((o + div) / c - 1) * 1e4 - 2.0 - 1.8 * gap
    N = pd.DataFrame({"d": d, "nd": nd, "net": net, "ksg": np.nan})
    return N[gap <= 5].reset_index(drop=True)


# ---------------- istatistik ----------------
def _boot(N: pd.DataFrame, fn) -> float:
    blks = N.blk.unique()
    idx = {k: np.flatnonzero(N.blk.values == k) for k in blks}
    out = []
    for _ in range(NB):
        ii = np.concatenate([idx[k] for k in RNG.choice(blks, len(blks))])
        v = fn(N.iloc[ii])
        if v == v:
            out.append(v > 0)
    return round(float(np.mean(out)), 3) if out else None


def d_mean(N: pd.DataFrame, flag: str) -> float:
    a, b = N[N[flag]].net, N[~N[flag]].net
    return float(a.mean() - b.mean()) if len(a) and len(b) else np.nan


def did(N: pd.DataFrame) -> float:
    k = N.ksg.astype(bool)
    return d_mean(N[k], "O") - d_mean(N[~k], "O")


def summ(N: pd.DataFrame) -> dict:
    """Bir besleme/dönem için H1 + H2 özet."""
    k = N.ksg.astype(bool) if N.ksg.notna().all() else None
    r = {"n": len(N), "n_O": int(N.O.sum()), "ort_O": _r(N[N.O].net.mean()), "ort_degil": _r(N[~N.O].net.mean()),
         "D_TUM": _r(d_mean(N, "O")), "P_D_TUM": _boot(N, lambda z: d_mean(z, "O")),
         "D_yeni": _r(d_mean(N[~N.fomc & ~N.cpi], "yeni")),
         "bilesen": {c: {"n": int(N[c].sum()), "ort": _r(N[N[c]].net.mean())} for c in ("fomc", "cpi", "nfp", "bil")}}
    if k is not None:
        K = N[k]
        r.update({"n_KSG": len(K), "n_KSG_O": int(K.O.sum()), "KSG_O": _r(K[K.O].net.mean()), "KSG_degil_O": _r(K[~K.O].net.mean()),
                  "D_KSG": _r(d_mean(K, "O")), "P_D_KSG": _boot(K, lambda z: d_mean(z, "O")),
                  "D_KSGdegil": _r(d_mean(N[~k], "O")), "DiD": _r(did(N)), "P_DiD": _boot(N, did),
                  "KSG_bilesen": {c: {"n": int(K[c].sum()), "ort": _r(K[K[c]].net.mean())} for c in ("fomc", "cpi", "nfp", "bil")}})
    return r


def _r(x) -> float | None:
    return None if x is None or x != x else round(float(x), 1)


def sharpe_dose(N: pd.DataFrame, vix: pd.Series) -> dict:
    """KSG kitabı (canlı VIX ≥ 25 dozu) vs + O gecelerinde ×1,5."""
    K = N[N.ksg.astype(bool)].copy()
    vp = [vix[vix.index < d] for d in K.d]
    K["lot"] = [Oy.ks.entry_lot(1.0, float(v.iloc[-1]) if len(v) else None) for v in vp]
    days = pd.bdate_range(K.d.min(), K.d.max())

    def sh(lot):
        s = (K.net * lot).groupby(K.d).sum().reindex(days).fillna(0)
        return round(float(s.mean() / s.std() * np.sqrt(252)), 3)
    return {"taban": sh(K.lot), "doz": sh(K.lot * np.where(K.O, DOSE, 1.0))}


def weekday_matched(N: pd.DataFrame) -> dict:
    K = N[N.ksg.astype(bool)]
    base = K[~K.O].groupby(K[~K.O].d.dt.dayofweek).net.mean()
    o = K[K.O]
    m = o.d.dt.dayofweek.map(base)
    return {"KSG_O": _r(o.net.mean()), "esli_taban": _r(m.mean()), "fark": _r((o.net - m).mean())}


# ---------------- ana ----------------
def main() -> None:
    RES.mkdir(exist_ok=True)
    Oy.kl.ay.NYSE_HOLIDAYS = set(Oy.kl.ay.NYSE_HOLIDAYS) | Oy.holidays()
    C, vix = calendar(), Oy.vix_prev()
    res: dict = {"S": {}, "U1": {}, "U2": {}, "U3": {}}
    S = {f: tag(feed_S(f), C) for f in S_FEEDS}
    live = Oy.nights("MT5_NAS100")
    res["kontrol_canli_ksg_ortusme"] = {"canli": len(live), "jenerik_ksg": int(S["MT5_NAS100"].ksg.sum()),
                                        "ortak": int(len(set(live.d) & set(S["MT5_NAS100"][S["MT5_NAS100"].ksg].d)))}
    print("kontrol:", res["kontrol_canli_ksg_ortusme"], flush=True)
    for f, N in S.items():
        res["S"][f] = {"TUM": summ(N), "KESIF": summ(N[N.d <= KESIF_SON]), "TEST": summ(N[N.d > KESIF_SON])}
        print("S", f, json.dumps({k: v for k, v in res["S"][f]["TUM"].items() if "bilesen" not in k}, ensure_ascii=False), flush=True)
    M = S["MT5_NAS100"]
    res["S"]["MT5_NAS100"]["hafta_gunu_esli"] = weekday_matched(M)
    res["S"]["MT5_NAS100"]["doz"] = {"KESIF": sharpe_dose(M[M.d <= KESIF_SON], vix), "TEST": sharpe_dose(M[M.d > KESIF_SON], vix)}
    U1 = {f: tag(feed_U1(f), C) for f in ("DUKA_M30_2016_17", "EET30")}
    for f, N in U1.items():
        res["U1"][f] = summ(N) | {"aralik": [str(N.d.min().date()), str(N.d.max().date())]}
        print("U1", f, json.dumps({k: v for k, v in res["U1"][f].items() if "bilesen" not in k}, ensure_ascii=False), flush=True)
    res["U1"]["DUKA_M30_2016_17"]["doz"] = sharpe_dose(U1["DUKA_M30_2016_17"], vix)
    pool = pd.concat([M.assign(blk="S" + M.blk), U1["DUKA_M30_2016_17"].assign(blk="U" + U1["DUKA_M30_2016_17"].blk)], ignore_index=True)
    res["havuz_S_MT5_U1_Duka"] = {"DiD": _r(did(pool)), "P_DiD": _boot(pool, did), "D_KSG": _r(d_mean(pool[pool.ksg.astype(bool)], "O"))}
    print("havuz:", res["havuz_S_MT5_U1_Duka"], flush=True)
    # U2 / U3 günlük
    U2 = {s: tag(feed_daily(s, "2008-01-01", "2018-05-24"), C) for s in ETFS}
    for s, N in U2.items():
        r = summ(N)
        r["yarilar"] = {"ilk": _r(d_mean(N[N.d < U2_SPLIT], "O")), "ikinci": _r(d_mean(N[N.d >= U2_SPLIT], "O"))}
        r["yarilar_yeni"] = {"ilk": _r(d_mean(N[(N.d < U2_SPLIT) & ~N.fomc & ~N.cpi], "yeni")),
                             "ikinci": _r(d_mean(N[(N.d >= U2_SPLIT) & ~N.fomc & ~N.cpi], "yeni"))}
        res["U2"][s] = r
        print("U2", s, json.dumps({k: v for k, v in r.items() if k != "bilesen"}, ensure_ascii=False), "|", r["bilesen"], flush=True)
    P2 = pd.concat(U2.values(), ignore_index=True)
    res["U2"]["havuz"] = {"D_TUM": _r(d_mean(P2, "O")), "P_D_TUM": _boot(P2, lambda z: d_mean(z, "O")),
                          "D_yeni": _r(d_mean(P2[~P2.fomc & ~P2.cpi], "yeni")),
                          "P_D_yeni": _boot(P2[~P2.fomc & ~P2.cpi], lambda z: d_mean(z, "yeni")),
                          "yarilar": {"ilk": _r(d_mean(P2[P2.d < U2_SPLIT], "O")), "ikinci": _r(d_mean(P2[P2.d >= U2_SPLIT], "O"))}}
    print("U2 havuz:", res["U2"]["havuz"], flush=True)
    for s in ETFS:
        N = tag(feed_daily(s, "2002-04-01", "2007-12-31"), C)
        res["U3"][s] = {"n_bil": int(N.bil.sum()), "bil": _r(N[N.bil].net.mean()), "diger": _r(N[~N.bil].net.mean()),
                        "D": _r(d_mean(N, "bil"))}
    print("U3:", res["U3"], flush=True)
    res["hukum"] = verdict(res)
    print("HÜKÜM:", res["hukum"])
    (RES / "olay.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


def verdict(r: dict) -> dict:
    u, e = r["U1"]["DUKA_M30_2016_17"], r["U1"]["EET30"]
    m = r["S"]["MT5_NAS100"]
    dz = [m["doz"]["KESIF"], m["doz"]["TEST"], u["doz"]]
    h1_all_pos = (u["D_KSG"] or -1) > 0 and (e["D_KSG"] or -1) > 0
    dose_ok = all(x["doz"] > x["taban"] for x in dz)
    h = r["havuz_S_MT5_U1_Duka"]
    if h1_all_pos and (h["DiD"] or -1) > 0 and (h["P_DiD"] or 0) >= 0.90 and dose_ok:
        h1 = "B"
    elif h1_all_pos and (m["TUM"]["D_KSG"] or -1) > 0:
        h1 = "C+"
    else:
        h1 = "X"
    U2 = r["U2"]
    pos = sum(1 for s in ETFS if (U2[s]["D_TUM"] or -1) > 0)
    newpos = sum(1 for s in ETFS if (U2[s]["D_yeni"] or -1) > 0)
    hv = U2["havuz"]
    u2_ok = pos >= 3 and (hv["P_D_TUM"] or 0) >= 0.95 and min(hv["yarilar"].values()) > 0
    kor = sum(1 for f in BLIND if (r["S"][f]["TUM"]["D_TUM"] or -1) > 0)
    rest = newpos >= 3 and (u["ort_O"] or -1) > 0 and (m["TUM"]["ort_O"] or -1) > 0 and (m["TUM"]["D_TUM"] or -1) > 0 and kor >= 2
    h2 = "B" if u2_ok and rest else ("C" if u2_ok else "X")
    return {"H1": h1, "H2": h2, "h1_U1_pozitif": h1_all_pos, "h1_doz": dose_ok, "h2_U2_etf_pozitif": f"{pos}/4", "h2_yeni_pozitif": f"{newpos}/4",
            "h2_kor": f"{kor}/3"}


if __name__ == "__main__":
    main()
