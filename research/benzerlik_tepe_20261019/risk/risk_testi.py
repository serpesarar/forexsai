"""ME-11 — "dalgalı tepe" yapısı sonrası RİSK (oynaklık + düşüş derinliği), çoklu zaman dilimi.

Ön-kayıt: PROTOCOL.md (değiştirmeden uygular). Çalıştır:
    python3 research/benzerlik_tepe_20261019/risk/risk_testi.py
Dedektörler: D1 = şablon-şekil (ME-09 ölçüsü, pencere mum sayısı cinsinden), D2 = kural K1 (ME-10, gün → 23 barlık adım).
"""
from __future__ import annotations

import json
import math
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "sablon"))
sys.path.insert(0, str(HERE.parent / "kural"))
from ortak import DEV_END, HO_START, TEMPL, shapes, tpl_index  # noqa: E402
from ortak import load_ndx as load_ndx_1h  # noqa: E402
from tepe_ozellik import REF_MIN, features  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
STEP = 23                      # adım = 23 bar (1h'te ≈ 1 işlem günü)
LS = (166, 207, 248)           # D1 pencere uzunlukları (bar)
W = 9                          # D2 pencere = 9 adım = 207 bar
HS = (23, 69, 115)             # ufuklar (bar) = 1, 3, 5 adım
TRAIL = 207                    # eşli taban: geriye-dönük getiri / oynaklık penceresi (bar)
HAR_L = (23, 115, 460)
MIN_HIST = 460
MIN_BASE = 5
GAP = 10                       # olay ayrımı: > 10 adım boşluk
TAIL_SIG = -2.0
B = 10_000
K1 = {"pos": (0.222, "le"), "net_s": (-1.524, "le"), "dist60_s": (-4.827, "ge"),
      "rv_ratio": (0.742, "ge"), "swings": (3, "ge"), "eff": (0.129, "le")}
EX0, EX1 = pd.Timestamp("2026-07-06", tz="UTC"), pd.Timestamp("2026-08-20 23:59", tz="UTC")
DAX_START = pd.Timestamp("2020-01-01", tz="UTC")
FIX = ROOT / "research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed"
MOT = ROOT / "research/ndx_pattern_motifs/data"
GF = ROOT / "research/ndx_gate_forge/data"
# hedef → risk-artışı işareti (+1: büyük değer = risk, −1: küçük değer = risk)
TARGETS = {"lrv": +1, "dd": -1, "tail": +1, "har": +1}
PRIMARY = ("lrv", "dd")


# ─────────────────────────────── veri ───────────────────────────────
def _ohlc(d: pd.DataFrame) -> pd.DataFrame:
    return d[["ts", "open", "high", "low", "close"]].dropna().sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def _extend(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    a, b = _ohlc(a), _ohlc(b)
    return _ohlc(pd.concat([a, b[b.ts > a.ts.max()]]))


def to_4h(d: pd.DataFrame) -> pd.DataFrame:
    """1h → 4h, NY 17:00 sınırlı kovalar (17, 21, 01, 05, 09, 13 NY)."""
    ny = d.ts.dt.tz_convert("America/New_York").dt.tz_localize(None)
    key = (ny - pd.Timedelta(hours=17)).dt.floor("4h")
    g = d.assign(k=key.to_numpy()).groupby("k", sort=True)
    out = g.agg(ts=("ts", "first"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    return _ohlc(out.reset_index(drop=True))


def load_all() -> dict[tuple[str, str], pd.DataFrame]:
    ndx1h = _ohlc(load_ndx_1h())
    dax = {tf: _ohlc(pd.read_parquet(FIX / f"dax_{tf}.parquet")) for tf in ("15m", "30m", "1h")}
    dax = {tf: x[x.ts >= DAX_START].reset_index(drop=True) for tf, x in dax.items()}
    return {
        ("NDX", "5m"): _ohlc(pd.read_parquet(MOT / "bars_5m.parquet")),
        ("NDX", "15m"): _extend(pd.read_parquet(GF / "long_15m_utc.parquet"), pd.read_parquet(MOT / "bars_15m.parquet")),
        ("NDX", "30m"): _extend(pd.read_parquet(GF / "long_30m_utc.parquet"), pd.read_parquet(MOT / "bars_30m.parquet")),
        ("NDX", "1h"): ndx1h,
        ("NDX", "4h"): to_4h(ndx1h),
        ("DAX", "15m"): dax["15m"], ("DAX", "30m"): dax["30m"], ("DAX", "1h"): dax["1h"], ("DAX", "4h"): to_4h(dax["1h"]),
    }


def template_vectors(ndx1h: pd.DataFrame) -> list[np.ndarray]:
    c = np.log(ndx1h.close.to_numpy())
    return [shapes(c, np.array([a]), b - a + 1)[0] for a, b in tpl_index(ndx1h.ts, TEMPL).values()]


# ─────────────────────────────── yardımcılar ───────────────────────────────
def shape_dist(c: np.ndarray, Q: np.ndarray, tvs: list[np.ndarray]) -> np.ndarray:
    D = np.full(len(Q), np.inf)
    for L in LS:
        st = Q - L + 1
        ok = st >= 0
        S = shapes(c, np.clip(st, 0, None), L)
        for tv in tvs:
            dist = np.sqrt(((S - tv) ** 2).sum(1))
            dist[~ok | ~np.isfinite(dist)] = np.inf
            D = np.minimum(D, dist)
    return D


def k1_fire(f: pd.DataFrame) -> np.ndarray:
    fire = np.ones(len(f), bool)
    for col, (thr, op) in K1.items():
        x = f[col].to_numpy(float)
        fire &= (x <= thr) if op == "le" else (x >= thr)
    return fire


def decile_bins(x: np.ndarray, ref: np.ndarray) -> np.ndarray:
    edges = np.nanpercentile(ref, np.linspace(10, 90, 9))
    b = np.searchsorted(edges, x, side="right")
    return np.where(np.isfinite(x), b, -1)


def matched_base(y: np.ndarray, non: np.ndarray, keys: list[np.ndarray], need: np.ndarray) -> np.ndarray:
    """need sorguları için taban (yapı-olmayan) sorguların aynı hücre ortalaması; < MIN_BASE ise kaba düzeye düş."""
    base = np.full(len(y), np.nan)
    for key in keys:
        todo = need & np.isnan(base)
        if not todo.any():
            break
        g = pd.DataFrame({"k": key[non], "y": y[non]}).groupby("k").y.agg(["mean", "size"])
        m = g.reindex(key[todo])
        good = (m["size"].fillna(0) >= MIN_BASE).to_numpy()
        idx = np.flatnonzero(todo)
        base[idx[good]] = m["mean"].to_numpy()[good]
    todo = need & np.isnan(base)
    base[todo] = np.nanmean(y[non])
    return base


def mboot(x: np.ndarray, month: np.ndarray, seed: int) -> float:
    """Takvim-ayı blok bootstrap: P(ortalama > 0)."""
    ok = np.isfinite(x)
    x, month = x[ok], month[ok]
    if len(x) < 10:
        return np.nan
    u, inv = np.unique(month, return_inverse=True)
    S, N = np.bincount(inv, x), np.bincount(inv)
    i = np.random.default_rng(seed).integers(0, len(u), size=(B, len(u)))
    return float(((S[i].sum(1) / N[i].sum(1)) > 0).mean())


def episode_stats(k: np.ndarray, x: np.ndarray) -> tuple[int, float, float]:
    """k: yapı sorgularının adım indeksleri (sıralı), x: fark. Dönüş: (olay, olay-ortalamalarının medyanı, olay ort. dizisi)."""
    if len(k) == 0:
        return 0, np.nan, np.array([])
    lab = np.r_[0, np.cumsum(np.diff(k) > GAP)]
    em = pd.Series(x).groupby(lab).mean().to_numpy()
    return int(len(em)), float(np.median(em)), em


def binom_sf(k: int, n: int, p: float) -> float:
    return float(sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1)))


# ─────────────────────────────── bir seri ───────────────────────────────
def prepare(d: pd.DataFrame, tvs: list[np.ndarray]) -> dict:
    ts = d.ts.reset_index(drop=True)
    c, lo = np.log(d.close.to_numpy()), np.log(d.low.to_numpy())
    n = len(c)
    Q = np.arange(n - 1, -1, -STEP)[::-1]           # son bar son sorgu (bugünkü durum için)
    r1 = np.diff(c, prepend=c[0])
    S = np.cumsum(r1 ** 2)                          # S[b] − S[a] = Σ_{a<j≤b} r_j²
    f = features(d.reset_index(drop=True), Q, W)
    sref = f.sref.to_numpy()
    kk = np.arange(len(Q))
    base_ok = (kk >= REF_MIN + 1) & np.isfinite(sref) & (Q >= MIN_HIST)
    qs = np.clip(Q, MIN_HIST, None)
    rv = lambda a, b: np.sqrt(np.maximum(S[b] - S[a], 0))  # noqa: E731
    X = {"trail_ret": c[Q] - c[np.clip(Q - TRAIL, 0, None)], "trail_rv": rv(np.clip(Q - TRAIL, 0, None), Q)}
    har = [np.log(rv(qs - L, qs)) for L in HAR_L]
    har += [c[qs] - c[qs - TRAIL], np.minimum(c[qs] - c[qs - 23], 0)]
    Xh = np.column_stack([np.ones(len(Q))] + har)
    Y = {}
    for H in HS:
        qe = np.clip(Q + H, None, n - 1)
        fmin = pd.Series(lo).rolling(H).min().shift(-H).to_numpy()
        valid = (Q + H < n) & base_ok & np.isfinite(Xh).all(1)
        lrv = np.log(rv(Q, qe))
        dd = (fmin[Q] - c[Q]) / (sref * np.sqrt(H / STEP))
        valid &= np.isfinite(lrv) & np.isfinite(dd)
        Y[H] = {"lrv": lrv, "dd": dd, "tail": (dd <= TAIL_SIG).astype(float), "valid": valid,
                "end_ts": ts.iloc[qe].reset_index(drop=True)}
    t_q = ts.iloc[Q].reset_index(drop=True)
    ex = ((ts.iloc[np.clip(Q - max(LS), 0, None)].reset_index(drop=True) <= EX1).to_numpy()
          & (ts.iloc[np.clip(Q + max(HS), None, n - 1)].reset_index(drop=True) >= EX0).to_numpy())
    D = shape_dist(c, Q, tvs)
    return {"ts": ts, "Q": Q, "t_q": t_q, "f": f, "D": D, "fire": k1_fire(f), "X": X, "Xh": Xh, "Y": Y,
            "base_ok": base_ok, "ex": ex, "month": t_q.dt.strftime("%Y-%m").to_numpy()}


def run_series(sym: str, tf: str, pr: dict) -> tuple[list[dict], dict]:
    t_q, base_ok, ex, D = pr["t_q"], pr["base_ok"], pr["ex"], pr["D"]
    devq = base_ok & ~ex & (t_q <= DEV_END).to_numpy()
    thr2, thr5 = np.percentile(D[devq & np.isfinite(D)], 2), np.percentile(D[devq & np.isfinite(D)], 5)
    det = {"D1_sekil": (D <= thr2, D > thr5), "D2_kural": (pr["fire"], ~pr["fire"])}
    rb = decile_bins(pr["X"]["trail_ret"], pr["X"]["trail_ret"][devq])
    vb = decile_bins(pr["X"]["trail_rv"], pr["X"]["trail_rv"][devq])
    keys = [rb * 10 + vb, rb]
    tdev = t_q[devq]
    mid = tdev.min() + (tdev.max() - tdev.min()) / 2
    first = (t_q < mid).to_numpy()
    ho = (t_q >= HO_START).to_numpy()
    cells = []
    for H in HS:
        y = pr["Y"][H]
        dev = y["valid"] & ~ex & (y["end_ts"] <= DEV_END).to_numpy()
        beta = np.linalg.lstsq(pr["Xh"][dev], y["lrv"][dev], rcond=None)[0]
        resid = y["lrv"] - pr["Xh"] @ beta
        for dname, (sim, non) in det.items():
            for per, pm in (("gelistirme", dev), ("dogrulama", y["valid"] & ~ex & ho)):
                s, nn = pm & sim, pm & non
                for tg, sgn in TARGETS.items():
                    if tg == "har":
                        diff = resid
                    else:
                        yy = y[tg]
                        diff = yy - matched_base(yy, nn, keys, s)
                    seed = zlib.crc32(f"{sym}|{tf}|{H}|{dname}|{per}|{tg}".encode())
                    k = np.flatnonzero(s)
                    dx = diff[k]
                    P_up = mboot(sgn * dx, pr["month"][k], seed) if len(k) else np.nan
                    n_ep, ep_med, em = episode_stats(k, dx)
                    cell = {"sembol": sym, "tf": tf, "ufuk_bar": H, "dedektor": dname, "donem": per, "hedef": tg,
                            "sorgu": int(len(k)), "olay": n_ep, "fark": float(np.mean(dx)) if len(k) else np.nan,
                            "P_risk_artar": P_up, "olay_medyan": ep_med,
                            "olay_risk_payi_%": 100 * float(np.mean(sgn * em > 0)) if n_ep else np.nan}
                    if tg in ("lrv", "dd", "tail"):
                        allm = pm & ~sim
                        cell["yapi_ort"] = float(np.mean(y[tg][k])) if len(k) else np.nan
                        cell["kosulsuz_fark"] = float(np.mean(y[tg][k]) - np.mean(y[tg][allm])) if len(k) else np.nan
                    if per == "gelistirme":
                        for nm, hm in (("yari1", first), ("yari2", ~first)):
                            kh = np.flatnonzero(s & hm)
                            cell[f"fark_{nm}"] = float(np.mean(diff[kh])) if len(kh) else np.nan
                    cells.append(cell)
    # tanımlayıcı: bugünkü durum + son 60 adımda yanan sorgular
    last = len(pr["Q"]) - 1
    pct = float(100 * np.mean(D[devq] <= D[last]))
    recent = lambda m: [str(t_q.iloc[i])[:16] for i in range(max(0, last - 60), last + 1) if m[i]]  # noqa: E731
    desc = {"bar": int(len(pr["ts"])), "ilk": str(pr["ts"].iloc[0])[:10], "son": str(pr["ts"].iloc[-1])[:16],
            "sorgu_gelistirme": int(devq.sum()), "D1_esik_%2": float(thr2),
            "D1_yanan_pay_%": float(100 * np.mean((D <= thr2)[devq])), "D2_yanan_pay_%": float(100 * np.mean(pr["fire"][devq])),
            "bugun": {"sorgu": str(t_q.iloc[last])[:16], "D1_yuzdelik_%": pct, "D1_yapi": bool(D[last] <= thr2),
                      "D2_yapi": bool(pr["fire"][last])},
            "son60_adim_D1": recent(D <= thr2)[-8:], "son60_adim_D2": recent(pr["fire"])[-8:]}
    return cells, desc


def judge(cdf: pd.DataFrame) -> pd.DataFrame:
    """Ön-kayıtlı hücre ölçütü (geliştirme) — risk-artışı ve ayna (risk-azalışı) yönünde."""
    dv = cdf[(cdf.donem == "gelistirme")].copy()
    sg = dv.hedef.map(TARGETS)
    for name, s in (("gecti", sg), ("ayna_gecti", -sg)):
        Pdir = dv.P_risk_artar if name == "gecti" else 1 - dv.P_risk_artar
        dv[name] = ((Pdir >= 0.975) & (s * dv.fark_yari1 > 0) & (s * dv.fark_yari2 > 0) & (dv.olay >= 20)
                    & (s * dv.olay_medyan > 0))
    dv["bonferroni"] = dv.gecti & (dv.P_risk_artar >= 1 - 0.025 / 60)
    return dv


def main() -> None:
    data = load_all()
    tvs = template_vectors(data[("NDX", "1h")])
    cells, desc = [], {}
    for (sym, tf), d in data.items():
        pr = prepare(d, tvs)
        c, ds = run_series(sym, tf, pr)
        cells += c
        desc[f"{sym}_{tf}"] = ds
        print(f"{sym} {tf}: {ds['bar']} bar {ds['ilk']}→{ds['son']}  gel.sorgu={ds['sorgu_gelistirme']}  "
              f"D1 %{ds['D1_yanan_pay_%']:.1f}  D2 %{ds['D2_yanan_pay_%']:.1f}  bugün={ds['bugun']}", flush=True)
    cdf = pd.DataFrame(cells)
    cdf.to_csv(OUT / "hucreler.csv", index=False)
    dv = judge(cdf)
    dv.to_csv(OUT / "gelistirme_karar.csv", index=False)
    ndxp = dv[(dv.sembol == "NDX") & dv.hedef.isin(PRIMARY)]
    n_cell, k_pass, k_mirror = len(ndxp), int(ndxp.gecti.sum()), int(ndxp.ayna_gecti.sum())
    # DAX işaret uyumu: NDX'te geçen (dedektör, ufuk, hedef) üçlüleri için DAX geliştirme hücrelerinin risk-yönü payı
    daxp = dv[(dv.sembol == "DAX") & dv.hedef.isin(PRIMARY)]
    passed = ndxp[ndxp.gecti][["dedektor", "ufuk_bar", "hedef"]].drop_duplicates()
    dx = daxp.merge(passed, on=["dedektor", "ufuk_bar", "hedef"])
    dax_same = float(np.mean(dx.hedef.map(TARGETS) * dx.fark > 0)) if len(dx) else np.nan
    summ = {"NDX_birincil_hucre": n_cell, "gecen": k_pass, "ayna_gecen": k_mirror,
            "binom_p_gecen": binom_sf(k_pass, n_cell, 0.025), "binom_p_ayna": binom_sf(k_mirror, n_cell, 0.025),
            "bonferroni_gecen": int(ndxp.bonferroni.sum()),
            "DAX_birincil_hucre": len(daxp), "DAX_gecen": int(daxp.gecti.sum()), "DAX_ayna_gecen": int(daxp.ayna_gecti.sum()),
            "DAX_isaret_uyumu_ndx_gecenlerde": dax_same,
            "risk_yonu_payi_NDX_gel_%": float(100 * np.mean(ndxp.hedef.map(TARGETS) * ndxp.fark > 0)),
            "risk_yonu_payi_DAX_gel_%": float(100 * np.mean(daxp.hedef.map(TARGETS) * daxp.fark > 0))}
    (OUT / "ozet.json").write_text(json.dumps({"ozet": summ, "seriler": desc}, ensure_ascii=False, indent=2, default=str))
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 500)
    cols = ["sembol", "tf", "dedektor", "ufuk_bar", "hedef", "sorgu", "olay", "yapi_ort", "kosulsuz_fark", "fark",
            "P_risk_artar", "fark_yari1", "fark_yari2", "olay_medyan", "olay_risk_payi_%", "gecti", "ayna_gecti"]
    print("\n=== GELİŞTİRME (birincil + ikincil) ===")
    print(dv[cols].round(3).to_string(index=False))
    ho = cdf[cdf.donem == "dogrulama"]
    print("\n=== DOĞRULAMA (bir kez) ===")
    print(ho[["sembol", "tf", "dedektor", "ufuk_bar", "hedef", "sorgu", "olay", "fark", "P_risk_artar", "olay_medyan"]]
          .round(3).to_string(index=False))
    print("\n=== ÖZET ===")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
