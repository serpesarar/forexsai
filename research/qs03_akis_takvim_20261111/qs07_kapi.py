"""QS-07 H1: akış kapısı — canlı uzun kuralların (C3b, KSG, ORB×VIX) işlemlerini ay sonu akış pencerelerine göre sınıfla
(RÜZGAR / NÖTR / KARŞI), kapı + büyütme portföy etkisi. PROTOCOL_QS07.md."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, synth_bond, st, H
from qs04 import monthly, side, TH

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, rsi2_state  # noqa: E402
RNG = np.random.default_rng(71)
MAXH = 5
T0930, T1600 = pd.Timedelta(minutes=570), pd.Timedelta(minutes=960)


# ---------- akış pencereleri ----------
def windows(eq: pd.Series, bond: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp, int]]:
    cal = eq.dropna().index.intersection(bond.dropna().index)
    M = monthly(eq, bond, {"_": eq}); s = side(M.dm.to_numpy()); out = []
    for k, r in M.iterrows():
        p = cal.get_loc(r.d_D)
        if p + 3 >= len(cal):
            continue
        D, D1, D3 = cal[p], cal[p + 1], cal[p + 3]
        if s[k] != 0:
            out.append((D + T0930, D + T1600, int(s[k])))           # W1 son seans
            out.append((D + T1600, D1 + T0930, int(-s[k])))         # W2 son gece
        if r.dD >= TH:
            out.append((D1 + T0930, D3 + T1600, 1))                 # W3 ay başı uzun
    return out


def flow_score(a: pd.Timestamp, b: pd.Timestamp, W) -> int:
    f = 0
    for w0, w1, d in W:
        if max(a, w0) < min(b, w1):
            f += d
    return f


def label(f: int) -> str:
    return "RUZGAR" if f > 0 else ("KARSI" if f < 0 else "NOTR")


# ---------- işlem listeleri ----------
def c3b_daily(close: pd.Series, a: str, b: str, cost: float = 2.0) -> pd.DataFrame:
    c = close.dropna(); rsi, _, _ = rsi2_state(c); S = c.to_numpy(); sig = (rsi < 10).to_numpy(); idx = c.index
    rows, i, n = [], 0, len(S)
    while i < n:
        if sig[i]:
            j = next((k for k in range(i + 1, min(i + MAXH + 1, n)) if S[k] > S[k - 1]), min(i + MAXH, n - 1))
            if j > i:
                if pd.Timestamp(a) <= idx[i] < pd.Timestamp(b):
                    rows.append(dict(t0=idx[i] + T1600, t1=idx[j] + T1600, bp=(S[j] / S[i] - 1) * 1e4 - cost))
                i = j; continue
        i += 1
    return pd.DataFrame(rows)


def c3b_broker() -> pd.DataFrame:
    mk = Mkt("NAS100"); s = mk.day_series(930); S = s.S.to_numpy(); bi = s.bi.to_numpy()
    rsi, _, _ = rsi2_state(s.S); sig = (rsi < 10).to_numpy(); rows, i, n = [], 0, len(S)
    while i < n:
        if sig[i]:
            j = next((k for k in range(i + 1, min(i + MAXH + 1, n)) if S[k] > S[k - 1]), min(i + MAXH, n - 1))
            if j > i:
                rows.append(dict(t0=mk.et[bi[i]], t1=mk.et[bi[j]], bp=mk.pnl(bi[i], bi[j]))); i = j; continue
        i += 1
    return pd.DataFrame(rows)


def ksg_broker() -> pd.DataFrame:
    mk = Mkt("NAS100")
    rth = (mk.m >= 570) & (mk.m < 960) & (mk.wd < 5)
    cnt = pd.Series(1, index=mk.d[rth]).groupby(level=0).sum()
    b = lambda d, m: mk.at(d + pd.Timedelta(minutes=int(m)))
    days = pd.DatetimeIndex([d for d in cnt.index[cnt >= 12] if min(b(d, x) for x in (570, 900, 960)) >= 0])
    rows = []
    for i in range(len(days) - 1):
        d0, d1 = days[i], days[i + 1]
        if (d1 - d0).days > 4:
            continue
        i15, i16, ix = b(d0, 900), b(d0, 960), b(d1, 570)
        if mk.o[i16] / mk.o[i15] - 1 < 0:
            rows.append(dict(t0=mk.et[i16], t1=mk.et[ix], bp=mk.pnl(i16, ix)))
    return pd.DataFrame(rows)


def orb_vix() -> pd.DataFrame:
    T = pd.read_csv(H.parent / "kazanan_turev_20261111/results/c_orb_islemler.csv", parse_dates=["d"])
    T = T[(T.kural == "taban") & (T.vix >= 18.4)]
    return pd.DataFrame({"t0": T.d + pd.Timedelta(minutes=585), "t1": T.d + pd.Timedelta(minutes=955), "bp": T.bp.values})


# ---------- değerlendirme ----------
def evaluate(tr: pd.DataFrame, W) -> dict:
    tr = tr.copy(); tr["F"] = [flow_score(a, b, W) for a, b in zip(tr.t0, tr.t1)]; tr["g"] = tr.F.map(label)
    g = {k: tr.bp[tr.g == k].to_numpy() for k in ("RUZGAR", "NOTR", "KARSI")}
    out = {k: st(v) for k, v in g.items()}
    if len(g["RUZGAR"]) >= 2 and len(g["KARSI"]) >= 2:
        bR = g["RUZGAR"][RNG.integers(0, len(g["RUZGAR"]), (5000, len(g["RUZGAR"])))].mean(1)
        bK = g["KARSI"][RNG.integers(0, len(g["KARSI"]), (5000, len(g["KARSI"])))].mean(1)
        out["RUZGAR-KARSI"] = round(float(g["RUZGAR"].mean() - g["KARSI"].mean()), 1); out["P_fark"] = round(float((bR > bK).mean()), 3)
    # portföy: aylık P&L
    m = tr.t0.dt.to_period("M")
    base = tr.groupby(m).bp.sum()
    gated = tr.assign(w=np.where(tr.g == "KARSI", 0.0, np.where(tr.g == "RUZGAR", 2.0, 1.0))).assign(x=lambda d: d.w * d.bp).groupby(m).x.sum()
    only_block = tr.assign(x=np.where(tr.g == "KARSI", 0.0, tr.bp)).groupby(m).x.sum()
    allm = pd.period_range(m.min(), m.max(), freq="M")
    sr = lambda v: round(float(v.reindex(allm, fill_value=0).mean() / v.reindex(allm, fill_value=0).std(ddof=1) * np.sqrt(12)), 2)
    out["portfoy"] = {"SR_taban": sr(base), "SR_kapi": sr(only_block), "SR_kapi+buyutme": sr(gated),
                      "top_taban": round(float(base.sum()), 0), "top_kapi": round(float(only_block.sum()), 0), "top_kapi+buyutme": round(float(gated.sum()), 0)}
    out["n_toplam"] = int(len(tr))
    return out


def main():
    res = {}
    W_new = windows(px("SPY"), px("TLT"))
    spy_c, tnx = px("SPY"), px("TNX", "Close")
    W_old = windows(spy_c, synth_bond(tnx))
    # C3b günlük
    q = c3b_daily(px("QQQ"), "2002-08-01", "2026-11-01"); s_ = c3b_daily(px("SPY"), "2002-08-01", "2026-11-01")
    res["C3b_gunluk_QQQ_2002_26"] = evaluate(q, W_new); res["C3b_gunluk_SPY_2002_26"] = evaluate(s_, W_new)
    res["C3b_gunluk_havuz_2002_26"] = evaluate(pd.concat([q, s_], ignore_index=True), W_new)
    res["C3b_gunluk_SPY_1993_2002"] = evaluate(c3b_daily(px("SPY"), "1993-03-01", "2002-08-01"), [w for w in W_old if w[0] < pd.Timestamp("2002-08-01")])
    # broker
    res["C3b_broker_NAS100"] = evaluate(c3b_broker(), W_new)
    res["KSG_broker_NAS100"] = evaluate(ksg_broker(), W_new)
    res["ORBxVIX_dukascopy"] = evaluate(orb_vix(), W_new)
    H_ = res["C3b_gunluk_havuz_2002_26"]
    c1 = (H_["KARSI"].get("ort", 0) < H_["NOTR"].get("ort", 0) < H_["RUZGAR"].get("ort", 0)) and H_.get("P_fark", 0) >= .9
    c2 = res["C3b_gunluk_SPY_1993_2002"].get("RUZGAR-KARSI", -1) > 0
    c3 = all(res[k].get("RUZGAR-KARSI", -1) > 0 for k in ("C3b_broker_NAS100", "KSG_broker_NAS100", "ORBxVIX_dukascopy"))
    c4 = all(res[k]["portfoy"]["SR_kapi+buyutme"] >= res[k]["portfoy"]["SR_taban"] for k in ("C3b_broker_NAS100", "KSG_broker_NAS100", "ORBxVIX_dukascopy")) and \
        H_["portfoy"]["SR_kapi+buyutme"] > H_["portfoy"]["SR_taban"]
    res["olcut"] = {"1": bool(c1), "2": bool(c2), "3": bool(c3), "4": bool(c4),
                    "sinif": "B" if all([c1, c2, c3, c4]) else ("C+" if c1 and c2 else ("C" if c1 else "X"))}
    (H / "results/qs07_kapi.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for k, v in res.items():
        if k == "olcut":
            print("ÖLÇÜT", v); continue
        print("==", k, "n", v["n_toplam"], "| fark", v.get("RUZGAR-KARSI"), "P", v.get("P_fark"))
        for g in ("RUZGAR", "NOTR", "KARSI"):
            print(f"     {g:7s}", v[g])
        print("     portföy", v["portfoy"])


if __name__ == "__main__":
    main()
