"""at.py — algo tuzak yapıları, son 5 yıl (PROTOCOL). python at.py kesif | dogrula"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_kuresel_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import kk  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

G = kk.G
RES = ROOT / "research/algo_tuzak_20261118/results"
MODE = int(__import__("os").environ.get("AT_MODE", "1"))
NY = "America/New_York"
ERA = (("ESKI_YAPI", "2018-04-01", "2021-10-31"), ("KESIF", "2021-11-01", "2024-06-30"), ("TEST", "2024-07-01", "2026-12-31"))
MINS = [570, 600, 690, 720, 780, 900, 960]
N_MIN, MAX_FROZEN = 30, 4
P_T = 1 - 0.10 / MAX_FROZEN


def era_of(d) -> str:
    s = pd.Timestamp(d)
    for nm, a, b in ERA:
        if pd.Timestamp(a) <= s <= pd.Timestamp(b):
            return nm
    return "DIS"


def intraday_cells(b: pd.DataFrame, step: int, mode: int = 1) -> pd.DataFrame:
    dp = G.day_prices(b, NY, MINS, step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and all(np.isfinite(dp.loc[z, f"o{m}"]) for m in MINS)]
    D = dp.loc[days]
    rows = []
    specs = [("T1a", 570, 720, 960), ("T1b", 570, 780, 960), ("T2_1130", 570, 600, 690), ("T2_1600", 570, 600, 960), ("T5", 570, 900, 960)]
    for nm, a, e, x in specs:
        R = D[f"o{e}"] / D[f"o{a}"] - 1
        sig = R.shift(1).rolling(20, min_periods=15).std()
        side = -np.sign(R) * mode
        pin = np.where(side > 0, D[f"o{e}"] + D[f"s{e}"], D[f"o{e}"])
        pout = np.where(side > 0, D[f"o{x}"], D[f"o{x}"] + D[f"s{x}"])
        net = side * (pout / pin - 1) * 1e4
        extra = 0.5 * (D[f"s{e}"] + D[f"s{x}"]) / D[f"o{e}"] * 1e4
        for k in (1.0, 1.5):
            m = (R.abs() >= k * sig).values
            for d, v, ex_ in zip(np.array(days)[m], net[m], extra.values[m]):
                rows.append({"hucre": f"{nm}_k{k}", "d": d, "net": v, "n15": v - ex_})
    return pd.DataFrame(rows)


def trap_cells(b: pd.DataFrame, step: int, mode: int = 1) -> pd.DataFrame:
    x = G._local(b, NY)
    rth = x[(x.mn >= 570) & (x.mn < 960)]
    pdh = rth.groupby("day").h.max()
    pdl = rth.groupby("day").l.min()
    dp = G.day_prices(b, NY, [960], step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"]) and z in pdh.index]
    prev = {days[i]: days[i - 1] for i in range(1, len(days))}
    t, o, sp = b.t.values, b.o.values, b.sp.values
    rng = np.random.default_rng(31)
    win = 30 * 60 // step
    rows = []
    for d, g in x[(x.mn >= 600) & (x.mn < 870)].groupby("day"):
        if d not in prev:
            continue
        H, L = pdh[prev[d]], pdl[prev[d]]
        idx = g.index.values
        hh, ll, cc = g.h.values, g.l.values, g.c.values
        x16 = dp.loc[d, "o960"]
        for side0, lvl, brk, back in ((-1, H, hh > H * 1.001, cc < H), (+1, L, ll < L * 0.999, cc > L)):
            side = side0 * mode
            hit = np.flatnonzero(brk)
            r_i = idx[rng.integers(len(idx))]
            for tag, j in (("rnd", r_i),):
                k = j + 1
                if k < len(t):
                    pin = o[k] + (sp[k] if side > 0 else 0)
                    pout = x16 + (sp[k] if side < 0 else 0)
                    rows.append({"hucre": f"T3_{'PDH' if side0 < 0 else 'PDL'}", "tag": "rnd", "d": d, "net": side * (pout / pin - 1) * 1e4,
                                 "n15": side * (pout / pin - 1) * 1e4 - 0.5 * sp[k] / pin * 1e4})
            if not hit.size:
                continue
            h0 = hit[0]
            bk = np.flatnonzero(back[h0 + 1:h0 + 1 + win])
            if not bk.size:
                continue
            k = idx[h0 + 1 + bk[0]] + 1
            if k >= len(t):
                continue
            pin = o[k] + (sp[k] if side > 0 else 0)
            pout = x16 + (sp[k] if side < 0 else 0)
            v = side * (pout / pin - 1) * 1e4
            rows.append({"hucre": f"T3_{'PDH' if side0 < 0 else 'PDL'}", "tag": "trap", "d": d, "net": v, "n15": v - 0.5 * sp[k] / pin * 1e4})
    return pd.DataFrame(rows)


def calm_cells(b: pd.DataFrame, step: int, mode: int = 1) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [960], step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    p = dp.loc[days, "o960"].astype(float)
    s = dp.loc[days, "s960"].astype(float)
    r = p.pct_change()
    r10 = p / p.shift(10) - 1
    rv = r.rolling(10).std()
    lo = rv.rolling(250, min_periods=120).quantile(1 / 3).shift(1)
    idx = pd.Series(pd.to_datetime(days), index=p.index)
    rows = []
    for h in (5, 10):
        pn, sn = p.shift(-h), s.shift(-h)
        nights = (idx.shift(-h) - idx).dt.days
        sat = (-((pn + sn) / p - 1) * 1e4 if mode > 0 else (pn / (p + s) - 1) * 1e4) - kk.FIN * nights
        m = (r10 >= 0.04) & (rv <= lo)
        for d, v, mm in zip(days, sat.values, m.values):
            if np.isfinite(v):
                rows.append({"hucre": f"T4_h{h}", "tag": "trap" if mm else "rnd", "d": d, "net": v, "n15": v})
    return pd.DataFrame(rows)


def build(b: pd.DataFrame, step: int, mode: int = 1) -> pd.DataFrame:
    a = intraday_cells(b, step, mode)
    a["tag"] = "trap"
    df = pd.concat([a, trap_cells(b, step, mode), calm_cells(b, step, mode)], ignore_index=True)
    df["era"] = [era_of(d) for d in df.d]
    return df


def stat(df: pd.DataFrame, cell: str, era: str) -> dict:
    z = df[(df.hucre == cell) & (df.era == era)]
    a = z[z.tag == "trap"]
    base = z[z.tag == "rnd"]
    if len(a) < 3:
        return {"n": int(len(a))}
    tb = float(base.net.mean()) if len(base) else 0.0
    if len(base):
        P = G.KS.diff_p(a.net.values, a.d.astype(str).values, base.net.values, base.d.astype(str).values, n=3000)
    else:
        P = G.KS.diff_p(a.net.values, a.d.astype(str).values, np.zeros(1), np.array(["x"]), n=3000)
    se = a.net.std(ddof=1) / np.sqrt(len(a))
    return {"n": int(len(a)), "ort": round(float(a.net.mean()), 2), "taban": round(tb, 2), "s15": round(float(a.n15.mean()), 2),
            "t": round(float((a.net.mean() - tb) / se), 2) if se > 0 else None, "isabet": round(float((a.net > 0).mean()), 3), "P": round(float(P), 4)}


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    df = build(G.ndx_bars(), 60, MODE)
    df.to_parquet(RES / f"olaylar_DUKA_m{MODE}.parquet")
    cells = sorted(df.hucre.unique())
    rows = []
    for c in cells:
        rows.append({"hucre": c, **{f"{e}_{k}": v for e in ("ESKI_YAPI", "KESIF") for k, v in stat(df, c, e).items()}})
    g = pd.DataFrame(rows)
    g.to_csv(RES / f"kesif_m{MODE}.csv", index=False)
    print(g[["hucre", "ESKI_YAPI_n", "ESKI_YAPI_ort", "ESKI_YAPI_taban", "KESIF_n", "KESIF_ort", "KESIF_taban", "KESIF_t", "KESIF_P"]].to_string(index=False))
    ok = g[(g.KESIF_n >= N_MIN) & (g.KESIF_ort > 0) & (g.KESIF_ort > g.KESIF_taban) & (g.KESIF_P >= 0.90)]
    fr = ok.sort_values("KESIF_t", ascending=False).head(MAX_FROZEN).hucre.tolist()
    (RES / f"kesif_ozet_m{MODE}.json").write_text(json.dumps({"hucre": len(g), "aday": len(ok), "donmus": fr}, indent=1))
    print("dondurulan:", fr)


def dogrula() -> None:
    fr = json.loads((RES / f"kesif_ozet_m{MODE}.json").read_text())["donmus"]
    df = pd.read_parquet(RES / f"olaylar_DUKA_m{MODE}.parquet")
    m5 = build(KD.mt5_m30("NAS100"), 1800, MODE)
    out = []
    for c in fr:
        y, e, k = stat(df, c, "TEST"), stat(df, c, "ESKI_YAPI"), stat(df, c, "KESIF")
        mt = stat(m5, c, "TEST")
        ok = {"1_test": bool(y.get("ort", -1) > 0 and y.get("ort", -1) > y.get("taban", 0) and y.get("P", 0) >= P_T),
              "2_mt5": bool(mt.get("ort", -1) > 0), "3_surtunme": bool(y.get("s15", -1) > 0)}
        soft = y.get("ort", -1) > 0 and y.get("ort", -1) > y.get("taban", 0) and ok["2_mt5"]
        hk = "B" if all(ok.values()) else ("C+" if soft else "X")
        yap = "son 5 yıla özgü" if e.get("ort", 1) <= e.get("taban", 0) and k.get("ort", -1) > 0 and y.get("ort", -1) > 0 else "—"
        rec = {"hucre": c, "ESKI_YAPI": e, "KESIF": k, "TEST": y, "MT5_TEST": mt, "olcut": ok, "hukum": hk, "yapi_degisimi": yap}
        out.append(rec)
        print(f"\n{c}: {hk} {ok} | yapı: {yap}\n  ESKİ {e}\n  KEŞİF {k}\n  TEST {y}\n  MT5 TEST {mt}", flush=True)
    (RES / f"dogrulama_m{MODE}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula}[sys.argv[1]]()
