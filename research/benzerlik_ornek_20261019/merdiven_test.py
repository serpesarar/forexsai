"""ME-08 — kullanıcı tanımlı "aylık merdiven yükseliş" benzerliği. Ön-kayıt: PROTOCOL_MERDIVEN.md (değiştirmeden uygular).
Çalıştır: python3 research/benzerlik_ornek_20261019/merdiven_test.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
P = 64
LS = (460, 510, 560)
FS = (1 / 3, 1 / 2, 2 / 3, 1.0)
DEV_END = pd.Timestamp("2025-11-30 23:00", tz="UTC")
HO_START = pd.Timestamp("2025-12-01", tz="UTC")
SPLIT = pd.Timestamp("2021-01-01", tz="UTC")
TEMPL = {"T1": ("2026-04-20", "2026-05-21 23:00"), "T2": ("2026-04-14", "2026-05-13 23:00"),
         "T3": ("2025-09-02", "2025-09-29 23:00"), "T4": ("2025-06-30", "2025-07-30 23:00")}
B = 10_000
rng = np.random.default_rng(1019)


def load() -> pd.DataFrame:
    a = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_1h_utc.parquet")[["ts", "open", "high", "low", "close"]]
    b = pd.read_parquet(ROOT / "research/ndx_pattern_motifs/data/bars_15m.parquet")[["ts", "open", "high", "low", "close"]]
    b = b[b.ts > a.ts.max()].set_index("ts").resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna().reset_index()
    return pd.concat([a, b]).sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def shapes(c: np.ndarray, starts: np.ndarray, length: int) -> np.ndarray:
    pos = starts[:, None] + np.linspace(0, length - 1, P)[None, :]
    lo = np.floor(pos).astype(int); w = pos - lo; hi = np.minimum(lo + 1, len(c) - 1)
    x = c[lo] * (1 - w) + c[hi] * w
    return (x - x.mean(1, keepdims=True)) / x.std(1, keepdims=True)


def mboot(diff: np.ndarray, month: np.ndarray) -> float:
    ok = np.isfinite(diff); diff, month = diff[ok], month[ok]
    if len(diff) < 10:
        return np.nan
    u, inv = np.unique(month, return_inverse=True); S = np.bincount(inv, diff); N = np.bincount(inv)
    i = rng.integers(0, len(u), size=(B, len(u)))
    return float(((S[i].sum(1) / N[i].sum(1)) > 0).mean())


def main() -> None:
    d = load(); ts = d.ts; c = np.log(d.close.to_numpy()); n = len(c)
    ix = lambda t: int(ts.searchsorted(pd.Timestamp(t, tz="UTC")))  # noqa: E731
    tpl = {k: (ix(a), ix(b) - 1) for k, (a, b) in TEMPL.items()}
    Q = np.flatnonzero((ts.dt.hour == 20).to_numpy())
    Q = Q[Q >= max(LS)]
    # şablonlarla çakışan sorgular (pencere ∪ en uzun ufuk) dışarıda
    tpl_bad = np.zeros(len(Q), bool)
    for a, b in tpl.values():
        tpl_bad |= (Q + 480 >= a - max(LS)) & (Q - max(LS) <= b)
    rows = {}
    for f in FS:
        D = np.full(len(Q), np.inf)
        for k, (a, b) in tpl.items():
            tl = int(round(f * (b - a + 1)))
            tv = shapes(c, np.array([a]), tl)[0]
            for L in LS:
                Lf = int(round(f * L))
                st = Q - Lf + 1
                ok = st >= 0
                S = shapes(c, np.clip(st, 0, None), Lf)
                dist = np.sqrt(((S - tv) ** 2).sum(1)); dist[~ok] = np.inf
                D = np.minimum(D, dist)
        rows[f] = D
    res = {"sorgu_gun": int(len(Q))}
    dev = (ts.iloc[Q] <= DEV_END).to_numpy()
    month = ts.iloc[Q].dt.strftime("%Y-%m").to_numpy()
    first_half = (ts.iloc[Q] < SPLIT).to_numpy()
    cells = []
    for f in FS:
        D = rows[f]
        thr2, thr5 = np.percentile(D[dev & ~tpl_bad], 2), np.percentile(D[dev & ~tpl_bad], 5)
        Lt = int(round(f * 510))
        trail = np.full(len(Q), np.nan); okq = Q - Lt >= 0; trail[okq] = c[Q[okq]] - c[Q[okq] - Lt]
        hs = {"1s": 1, "1g": 24, "5g": 120} | ({"20g": 480} if f == 1.0 else {"kalan": int(round((1 - f) * 510))})
        res[f"f={f:.2f}"] = {"esik_%2": float(thr2), "esik_%5": float(thr5),
                             "benzer_gun_payi_%": float(100 * (D[dev & ~tpl_bad] <= thr2).mean())}
        for per, pmask in (("gelistirme", dev), ("dogrulama", (ts.iloc[Q] >= HO_START).to_numpy())):
            for hn, h in hs.items():
                endt = np.full(len(Q), pd.NaT)
                valid = Q + h < n
                end_ts = pd.Series(pd.NaT, index=range(len(Q)), dtype="datetime64[ns, UTC]")
                end_ts[valid] = ts.iloc[Q[valid] + h].to_numpy()
                inside = (end_ts <= DEV_END).to_numpy() if per == "gelistirme" else (end_ts.notna()).to_numpy()
                m = pmask & ~tpl_bad & valid & inside & np.isfinite(trail)
                r = np.full(len(Q), np.nan); r[valid] = c[Q[valid] + h] - c[Q[valid]]
                sim = m & (D <= thr2); non = m & (D > thr5)
                # trend-eşli taban: geliştirme dönemi ondalıkları (geriye dönük getiri)
                edges = np.nanpercentile(trail[dev & ~tpl_bad], np.linspace(0, 100, 11))
                binq = np.clip(np.searchsorted(edges, trail, side="right") - 1, 0, 9)
                base_bin = np.array([np.nanmean(r[non & (binq == b)]) if (non & (binq == b)).any() else np.nan for b in range(10)])
                diff_tr = r - base_bin[binq]
                diff_all = r - np.nanmean(r[m])
                idx = np.flatnonzero(sim)
                ep = int(1 + (np.diff(idx) > 10).sum()) if len(idx) else 0
                cell = {"f": round(f, 2), "donem": per, "ufuk": hn, "benzer_gun": int(sim.sum()), "olay": ep,
                        "ort_bp_benzer": 1e4 * float(np.nanmean(r[sim])) if sim.any() else np.nan,
                        "yukari_%_benzer": 100 * float(np.nanmean(r[sim] > 0)) if sim.any() else np.nan,
                        "ort_bp_tum": 1e4 * float(np.nanmean(r[m])),
                        "fark_kosulsuz_bp": 1e4 * float(np.nanmean(diff_all[sim])) if sim.any() else np.nan,
                        "fark_trend_esli_bp": 1e4 * float(np.nanmean(diff_tr[sim])) if sim.any() else np.nan,
                        "P_trend_esli": mboot(diff_tr[sim], month[sim]) if sim.any() else np.nan,
                        "P_kosulsuz": mboot(diff_all[sim], month[sim]) if sim.any() else np.nan}
                if per == "gelistirme":
                    for nm, hm in (("yari1", first_half), ("yari2", ~first_half)):
                        s2 = sim & hm
                        cell[f"fark_trend_{nm}_bp"] = 1e4 * float(np.nanmean(diff_tr[s2])) if s2.any() else np.nan
                cells.append(cell)
    cdf = pd.DataFrame(cells); cdf.to_csv(OUT / "merdiven_hucreler.csv", index=False)
    # bugünkü durum
    last = len(Q) - 1
    now = {"son_sorgu": str(ts.iloc[Q[last]]), "kapanis": float(d.close.iloc[Q[last]])}
    for f in FS:
        D = rows[f]; pr = float(100 * (D[dev & ~tpl_bad] <= D[last]).mean())
        now[f"f={f:.2f}"] = {"D": float(D[last]), "yuzdelik_%": pr, "benzer_mi(%2)": bool(pr <= 2), "benzer_mi(%5)": bool(pr <= 5)}
    hist = {}
    for f in FS:
        D = rows[f]; thr2 = np.percentile(D[dev & ~tpl_bad], 2)
        recent = [(str(ts.iloc[Q[i]].date()), round(float(D[i]), 2)) for i in range(max(0, last - 60), last + 1) if D[i] <= thr2]
        hist[f"f={f:.2f}"] = recent[-10:]
    res["bugun"] = now; res["son_60_gunde_benzer_gunler"] = hist
    (OUT / "merdiven_sonuc.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30)
    print(json.dumps({k: v for k, v in res.items() if k.startswith("f=")}, ensure_ascii=False, indent=1))
    print(cdf.round(3).to_string(index=False))
    print(json.dumps(now, ensure_ascii=False, indent=1)); print(json.dumps(hist, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
