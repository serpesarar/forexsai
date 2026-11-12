"""QS-11: altında 4 kombinasyon hipotezi (PROTOCOL.md). Her biri tek donmuş hücre; taban üstü fark + broker + Holm."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

H = Path(__file__).resolve().parent
Q3 = H.parent / "qs03_akis_takvim_20261111"
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402

COST = 2.0
RNG = np.random.default_rng(127)
FULL, HALF = ("2004-12-01", "2026-10-31"), "2015-01-01"


def adj(p: Path) -> pd.Series:
    x = pd.read_parquet(p)
    return (x["Adj Close"] if "Adj Close" in x else x.Close).dropna()


def trades_h1(C: pd.Series) -> pd.DataFrame:
    s50, s200 = C.rolling(50).mean(), C.rolling(200).mean()
    tr = (C > s200) & (s50 > s200); r1 = C.pct_change(); f = C.shift(-3) / C - 1
    T = pd.DataFrame({"side": 1, "g": f * 1e4, "base_pool": tr & f.notna()}, index=C.index)
    T["sig"] = tr & (r1 <= -0.01) & f.notna()
    return T


def trades_h2(G: pd.Series, S: pd.Series) -> pd.DataFrame:
    cal = G.index.intersection(S.index); G, S = G.reindex(cal), S.reindex(cal)
    rel = G.pct_change(20) - S.pct_change(20); z = rel / rel.rolling(252).std()
    f = (G.shift(-5) / G - 1).to_numpy(); zz = z.to_numpy()
    side = np.zeros(len(cal)); k = 0
    while k < len(cal) - 5:
        if np.isfinite(zz[k]) and abs(zz[k]) >= 1 and np.isfinite(f[k]):
            side[k] = 1 if zz[k] <= -1 else -1; k += 5
        else:
            k += 1
    T = pd.DataFrame({"side": side, "g": f * 1e4, "base_pool": np.isfinite(f)}, index=cal)
    T["sig"] = side != 0
    return T


def trades_h3(C: pd.Series, a: bool) -> pd.DataFrame:
    cal = C.index; v = C.to_numpy()
    last = pd.Series(np.arange(len(cal)), index=cal).groupby(cal.to_period("M")).max().to_numpy()
    T = pd.DataFrame({"side": 1 if a else -1, "g": np.nan, "base_pool": False, "sig": False}, index=cal)
    f3 = np.full(len(v), np.nan); f3[:-3] = (v[3:] / v[:-3] - 1) * 1e4
    T["g"] = f3; T["base_pool"] = np.isfinite(f3)
    for Dp in last:
        e = Dp - 4; i = e if a else e - 3
        if i >= 0 and i + 3 < len(cal):
            T.iloc[i, T.columns.get_loc("sig")] = True
    return T


def trades_h4(G: pd.Series, SP: pd.Series) -> pd.DataFrame:
    cal = G.index.intersection(SP.index); G, SP = G.reindex(cal), SP.reindex(cal)
    f = G.shift(-5) / G - 1
    T = pd.DataFrame({"side": 1, "g": f * 1e4, "base_pool": f.notna()}, index=cal)
    T["sig"] = (SP.pct_change() <= -0.02) & (G.pct_change() <= -0.01) & f.notna()
    return T


def mboot(x: pd.Series) -> float:
    g = x.groupby(x.index.to_period("M")).agg(["sum", "count"]).to_numpy()
    if len(g) < 6:
        return np.nan
    b = g[RNG.integers(0, len(g), (5000, len(g)))]
    return float(((b[..., 0].sum(1) / b[..., 1].sum(1)) > 0).mean())


def evaluate(T: pd.DataFrame, a: str, b: str) -> dict:
    t = T[(T.index >= a) & (T.index <= b)]
    sig = t[t.sig]
    if len(sig) < 5:
        return {"n": int(len(sig))}
    pool = t[t.base_pool]
    out = {"n": int(len(sig)), "islem_ay": round(len(sig) / max(1, (pd.Timestamp(b) - pd.Timestamp(a)).days / 30.44), 2)}
    net = sig.side * sig.g - COST
    exc = pd.Series(0.0, index=sig.index)
    for sd in (1, -1):
        m = sig.side == sd
        if m.any():
            exc[m] = sd * (sig.g[m] - pool.g.mean())
    out.update({"net": round(float(net.mean()), 1), "isabet": round(float((net > 0).mean()), 3),
                "taban_ustu": round(float(exc.mean()), 1), "P_taban_ustu": round(mboot(exc), 3),
                "uzun_n": int((sig.side == 1).sum()), "kisa_n": int((sig.side == -1).sum())})
    if out["uzun_n"] and out["kisa_n"]:
        out["uzun_taban_ustu"] = round(float(exc[sig.side == 1].mean()), 1); out["kisa_taban_ustu"] = round(float(exc[sig.side == -1].mean()), 1)
    return out


def single_pos(T: pd.DataFrame, hold: int, a: str, b: str) -> dict:
    t = T[(T.index >= a) & (T.index <= b)]; idx = np.flatnonzero(t.sig.to_numpy()); keep, nxt = [], -1
    for i in idx:
        if i >= nxt:
            keep.append(i); nxt = i + hold
    s = t.iloc[keep]; net = s.side * s.g - COST
    return {"n": int(len(s)), "net": round(float(net.mean()), 1) if len(s) else None}


def broker(T: pd.DataFrame, hold: int) -> dict:
    mk = Mkt("XAUUSD", stress=1.5); cal = T.index; out, base = [], []
    pos = {d: k for k, d in enumerate(cal)}
    for d in T.index[T.sig & (T.index >= "2018-06-01") & (T.index <= FULL[1])]:
        k = pos[d]
        if k + hold >= len(cal):
            continue
        i, j = mk.at(d + pd.Timedelta(minutes=960)), mk.at(cal[k + hold] + pd.Timedelta(minutes=960))
        if i < 0 or j < 0 or not np.isfinite(mk.cost(i)):
            continue
        sd = T.side.loc[d]
        out.append(sd * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j]))
    a = np.array(out)
    if len(a) < 5:
        return {"n": int(len(a))}
    P = float((a[RNG.integers(0, len(a), (5000, len(a)))].mean(1) > 0).mean())
    return {"n": int(len(a)), "net_x1.5": round(float(a.mean()), 1), "isabet": round(float((a > 0).mean()), 3), "P": round(P, 3)}


def holm(p: dict) -> dict:
    ks = sorted(p, key=p.get); m = len(ks); out, run = {}, 0.0
    for i, k in enumerate(ks):
        run = max(run, min(1.0, (m - i) * p[k])); out[k] = round(run, 3)
    return out


def main() -> None:
    G, S, SP = adj(Q3.parent / "qs10_altin_aysonu_20261112/data/GLD.parquet"), adj(H / "data/SLV.parquet"), adj(Q3 / "data/SPY.parquet")
    gc = pd.read_parquet(H.parent / "qs09_gunluk_kapi_20261112/data/GC.parquet").Close.dropna()
    si = pd.read_parquet(H / "data/SI.parquet").Close.dropna(); spo = pd.read_parquet(Q3 / "data/SPY.parquet")["Adj Close"].dropna()
    hyp = {"H1_trend_dusus_gunu": (trades_h1(G), trades_h1(gc), 3), "H2_altin_gumus": (trades_h2(G, S), trades_h2(gc, si), 5),
           "H3a_vade_sonrasi_uzun": (trades_h3(G, True), trades_h3(gc, True), 3), "H3b_vade_oncesi_kisa": (trades_h3(G, False), trades_h3(gc, False), 3),
           "H4_likidasyon_gunu": (trades_h4(G, SP), trades_h4(gc, spo), 5)}
    res = {}
    for k, (T, Tg, hold) in hyp.items():
        f = evaluate(T, *FULL); y1 = evaluate(T, FULL[0], "2014-12-31"); y2 = evaluate(T, HALF, FULL[1])
        res[k] = {"tum": f, "yari1": y1, "yari2": y2, "tek_pozisyon": single_pos(T, hold, *FULL), "broker_2018_26": broker(T, hold),
                  "destek_GC_2000_04": evaluate(Tg, "2000-08-01", "2004-11-30")}
    p = {k: 1 - (v["tum"].get("P_taban_ustu") or 0) for k, v in res.items()}
    hm = holm(p)
    for k, v in res.items():
        f = v["tum"]; ca = f.get("taban_ustu", -1) > 0 and (f.get("P_taban_ustu") or 0) >= .9
        cb = min(v["yari1"].get("taban_ustu", -1), v["yari2"].get("taban_ustu", -1)) >= 0
        cc = v["broker_2018_26"].get("net_x1.5", -1) > 0; cd = hm[k] <= 0.10
        v["olcut"] = {"a": ca, "b": cb, "c": cc, "d_holm": hm[k]}
        v["sinif"] = "B-" if ca and cb and cc and cd else ("C" if ca and cb else "X")
    (H / "results/qs11.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for k, v in res.items():
        print(f"\n=== {k} → {v['sinif']}  {v['olcut']}")
        for s in ("tum", "yari1", "yari2", "tek_pozisyon", "broker_2018_26", "destek_GC_2000_04"):
            print(f"  {s}: {v[s]}")


if __name__ == "__main__":
    main()
