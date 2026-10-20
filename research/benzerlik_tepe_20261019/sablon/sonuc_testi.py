"""ME-09 adım 3 — ön-kayıtlı sonuç testi (PROTOCOL.md; değiştirmeden uygular). BİR KEZ çalıştırılır.
Çalıştır: nice python3.13 research/benzerlik_tepe_20261019/sablon/sonuc_testi.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import (DEV_END, FS, HO_START, OUT, QUERY_HOUR, SPLIT, TEMPL, load_dax, load_ndx, r_from_d,  # noqa: E402
                   shapes, tpl_index, tpl_shape, window_lengths)

B = 10_000
N_PLACEBO = 500
EP_GAP = 10
MIN_BASE = 10
BONF = 1 - 0.025 / 15
BONF2 = 1 - 0.025 / 30
DAX_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
rng = np.random.default_rng(91019)


# ───────────────────────── yardımcılar ─────────────────────────
def mboot(diff: np.ndarray, month: np.ndarray) -> tuple[float, float]:
    """Takvim ayı blok bootstrap → (P(ort>0), P(ort<0))."""
    ok = np.isfinite(diff); diff, month = diff[ok], month[ok]
    if len(diff) < 5:
        return np.nan, np.nan
    u, inv = np.unique(month, return_inverse=True)
    S = np.bincount(inv, diff); N = np.bincount(inv)
    i = rng.integers(0, len(u), size=(B, len(u)))
    m = S[i].sum(1) / N[i].sum(1)
    return float((m > 0).mean()), float((m < 0).mean())


def dist_argmin(S_by_L: dict[int, tuple[np.ndarray, np.ndarray]], tvecs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """S_by_L[L] = (şekiller, geçerli maske). Dönüş: D, en yakın şablon indeksi, en yakın L."""
    n = next(iter(S_by_L.values()))[0].shape[0]
    D = np.full(n, np.inf); arg_t = np.full(n, -1); arg_L = np.full(n, -1)
    for L, (S, ok) in S_by_L.items():
        for j, tv in enumerate(tvecs):
            dist = np.sqrt(((S - tv) ** 2).sum(1))
            dist[~ok | ~np.isfinite(dist)] = np.inf
            better = dist < D
            D[better] = dist[better]; arg_t[better] = j; arg_L[better] = L
    return D, arg_t, arg_L


def qbin(x: np.ndarray, edges: np.ndarray) -> np.ndarray:
    b = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)
    return np.where(np.isfinite(x), b, -1)


def matched_base(y: np.ndarray, non: np.ndarray, keys: list[np.ndarray], need: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """need günleri için benzer-olmayan (non) günlerin aynı hücre ortalaması; hücre < MIN_BASE ise bir kaba düzeye düş."""
    base = np.full(len(y), np.nan); lev = np.full(len(y), -1)
    for li, key in enumerate(keys):
        g = pd.DataFrame({"k": key[non], "y": y[non]}).groupby("k").y.agg(["mean", "size"])
        todo = need & np.isnan(base)
        if not todo.any():
            break
        m = g.reindex(key[todo])
        good = (m["size"].fillna(0) >= MIN_BASE).to_numpy()
        idx = np.flatnonzero(todo)
        base[idx[good]] = m["mean"].to_numpy()[good]; lev[idx[good]] = li
    todo = need & np.isnan(base)
    base[todo] = np.nanmean(y[non]); lev[todo] = len(keys)
    return base, lev


def episodes(k: np.ndarray, diff: np.ndarray) -> dict:
    if len(k) == 0:
        return {"olay": 0}
    o = np.argsort(k); k, diff = k[o], diff[o]
    eid = np.concatenate([[0], np.cumsum(np.diff(k) > EP_GAP)])
    s = pd.Series(diff).groupby(eid)
    em = s.mean().to_numpy(); ef = s.first().to_numpy()
    n = len(em)
    out = {"olay": int(n), "olay_medyan_bp": 1e4 * float(np.median(em)), "olay_ort_bp": 1e4 * float(em.mean()),
           "olay_negatif_%": 100 * float((em < 0).mean()),
           "olay_ilk_gun_medyan_bp": 1e4 * float(np.median(ef)),
           "en_negatif_olay_haric_ort_bp": 1e4 * float(np.delete(em, np.argmin(em)).mean()) if n > 1 else np.nan,
           "en_pozitif_olay_haric_ort_bp": 1e4 * float(np.delete(em, np.argmax(em)).mean()) if n > 1 else np.nan,
           "en_negatif_olay_bp": 1e4 * float(em.min()), "en_pozitif_olay_bp": 1e4 * float(em.max())}
    from math import comb
    kneg = int((em < 0).sum()); kpos = int((em > 0).sum())
    out["isaret_p_asagi"] = float(sum(comb(n, j) for j in range(kneg, n + 1)) / 2 ** n)
    out["isaret_p_yukari"] = float(sum(comb(n, j) for j in range(kpos, n + 1)) / 2 ** n)
    return out


# ───────────────────────── piyasa kurulumu ─────────────────────────
class Market:
    def __init__(self, name: str, d: pd.DataFrame, tpl_ndx_ts: dict[str, tuple[pd.Timestamp, pd.Timestamp]],
                 LS: tuple[int, ...], tvec: dict[float, list[np.ndarray]], split: pd.Timestamp) -> None:
        self.name = name; self.d = d; self.ts = d.ts.reset_index(drop=True); self.c = np.log(d.close.to_numpy())
        self.n = len(self.c); self.LS = LS; self.split = split
        ts = self.ts
        if name == "NDX":
            Q = np.flatnonzero((ts.dt.hour == QUERY_HOUR).to_numpy())
        else:
            h = ts.dt.hour.to_numpy(); wd = ts.dt.weekday.to_numpy()
            df = pd.DataFrame({"i": np.arange(self.n), "date": ts.dt.date})[(h <= 20) & (wd < 5)]
            last = df.groupby("date").i.max().to_numpy()
            Q = last[h[last] >= 19]
        self.Q = Q[Q >= max(LS)]
        self.tq = ts.iloc[self.Q].reset_index(drop=True)
        self.month = self.tq.dt.strftime("%Y-%m").to_numpy()
        self.first_half = (self.tq < split).to_numpy()
        self.dev_q = (self.tq <= DEV_END).to_numpy()
        # şablon aralıkları bu piyasanın bar indekslerinde (DAX'ta aynı tarih aralığı)
        self.tpl = {k: (int(ts.searchsorted(a)), int(ts.searchsorted(b, side="right")) - 1) for k, (a, b) in tpl_ndx_ts.items()}
        self.r1 = pd.Series(np.diff(self.c, prepend=np.nan))
        # şekil matrisleri (şablondan bağımsız)
        self.S = {}
        for f in FS:
            self.S[f] = {}
            for L in LS:
                Lf = int(round(f * L)); st = self.Q - Lf + 1; ok = st >= 0
                self.S[f][L] = (shapes(self.c, np.clip(st, 0, None), Lf), ok)
        self.tvec = tvec
        self.D = {}; self.argt = {}; self.argL = {}
        for f in FS:
            self.D[f], self.argt[f], self.argL[f] = dist_argmin(self.S[f], tvec[f])

    def horizons(self, f: float) -> dict[str, np.ndarray]:
        Q = self.Q; n = self.n
        rem = int(round((1 - f) * 207))
        if self.name == "NDX":
            hs = {"1s": Q + 1, "1g": Q + 24, "5g": Q + 120}
        else:
            nxt = np.full(len(Q), -1); nxt[:-1] = Q[1:]
            n5 = np.full(len(Q), -1); n5[:-5] = Q[5:]
            hs = {"1s": Q + 1, "1g": nxt, "5g": n5}
        if f < 1:
            hs["kalan"] = Q + rem
        return {k: np.where((v >= 0) & (v < n), v, -1) for k, v in hs.items()}

    def trailing(self, f: float) -> tuple[np.ndarray, np.ndarray]:
        Lt = int(round(f * 207)); Q = self.Q
        ret = np.full(len(Q), np.nan); ok = Q - Lt >= 0
        ret[ok] = self.c[Q[ok]] - self.c[Q[ok] - Lt]
        vol = self.r1.rolling(Lt).std().to_numpy()[Q]
        return ret, vol

    def overlap(self, f: float, T: np.ndarray, spans: list[tuple[int, int]]) -> np.ndarray:
        W = int(round(f * max(self.LS)))
        lo = self.Q - W + 1; hi = np.where(T >= 0, T, self.Q)
        bad = np.zeros(len(self.Q), bool)
        for a, b in spans:
            bad |= (lo <= b) & (hi >= a)
        return bad


def run_cells(M: Market, D: dict[float, np.ndarray], spans: list[tuple[int, int]], periods: tuple[str, ...],
              boot: bool = True, keep_detail: bool = False, pct_sim: float = 2, pct_non: float = 5) -> tuple[list[dict], dict]:
    """Bir piyasa + bir mesafe dizisi için tüm hücreler. (pct_sim/pct_non: koşumdan SONRA eklendi, varsayılan = ön-kayıt 2/5;
    yalnız ek_tanilama.py'deki tanımlayıcı %5 eşik için.)"""
    cells = []; detail = {}
    for f in FS:
        Df = D[f]
        thr_ok = M.dev_q & np.isfinite(Df) & ~M.overlap(f, np.full(len(M.Q), -1), spans)
        thr2, thr5 = np.percentile(Df[thr_ok], pct_sim), np.percentile(Df[thr_ok], pct_non)
        ret, vol = M.trailing(f)
        devmask = M.dev_q & np.isfinite(ret) & np.isfinite(vol)
        e10r = np.nanpercentile(ret[devmask], np.linspace(0, 100, 11)); e10v = np.nanpercentile(vol[devmask], np.linspace(0, 100, 11))
        e5r = np.nanpercentile(ret[devmask], np.linspace(0, 100, 6)); e5v = np.nanpercentile(vol[devmask], np.linspace(0, 100, 6))
        rd, vd, rq, vq = qbin(ret, e10r), qbin(vol, e10v), qbin(ret, e5r), qbin(vol, e5v)
        keys = [rd * 10 + vd, rq * 5 + vq, rq]
        for hn, T in M.horizons(f).items():
            valid = T >= 0
            r = np.full(len(M.Q), np.nan); r[valid] = M.c[T[valid]] - M.c[M.Q[valid]]
            tend = pd.Series(pd.NaT, index=range(len(M.Q)), dtype="datetime64[ns, UTC]")
            tend[valid] = M.ts.iloc[T[valid]].to_numpy()
            bad = M.overlap(f, T, spans)
            for per in periods:
                if per == "gelistirme":
                    pm = (tend <= DEV_END).to_numpy() & valid
                else:
                    pm = (M.tq >= HO_START).to_numpy() & valid
                m = pm & ~bad & np.isfinite(ret) & np.isfinite(vol) & np.isfinite(Df) & np.isfinite(r)
                sim = m & (Df <= thr2); non = m & (Df > thr5)
                base, lev = matched_base(r, non, keys, sim)
                ubase, _ = matched_base((r > 0).astype(float), non, keys, sim)
                diff_m = r - base; diff_all = r - np.nanmean(r[m])
                ks = np.flatnonzero(sim)
                cell = {"piyasa": M.name, "f": round(f, 2), "ufuk": hn, "donem": per,
                        "esik_%2": float(thr2), "esik_%2_r": float(r_from_d(thr2)),
                        "uygun_gun": int(m.sum()), "benzer_gun": int(sim.sum()),
                        "ort_bp_benzer": 1e4 * float(np.mean(r[sim])) if sim.any() else np.nan,
                        "yukari_%_benzer": 100 * float(np.mean(r[sim] > 0)) if sim.any() else np.nan,
                        "ort_bp_tum": 1e4 * float(np.mean(r[m])) if m.any() else np.nan,
                        "yukari_%_tum": 100 * float(np.mean(r[m] > 0)) if m.any() else np.nan,
                        "ort_bp_esli_taban": 1e4 * float(np.mean(base[sim])) if sim.any() else np.nan,
                        "yukari_%_esli_taban": 100 * float(np.mean(ubase[sim])) if sim.any() else np.nan,
                        "fark_tum_bp": 1e4 * float(np.mean(diff_all[sim])) if sim.any() else np.nan,
                        "fark_esli_bp": 1e4 * float(np.mean(diff_m[sim])) if sim.any() else np.nan,
                        "taban_geri_dusus_dagilimi": {int(k): int(v) for k, v in zip(*np.unique(lev[sim], return_counts=True))}}
                if boot and sim.any():
                    pp, pn = mboot(diff_m[sim], M.month[sim]); cell["P_esli_yukari"] = pp; cell["P_esli_asagi"] = pn
                    pp2, pn2 = mboot(diff_all[sim], M.month[sim]); cell["P_tum_yukari"] = pp2; cell["P_tum_asagi"] = pn2
                if per == "gelistirme":
                    for nm, hm in (("yari1", M.first_half), ("yari2", ~M.first_half)):
                        s2 = sim & hm
                        cell[f"fark_esli_{nm}_bp"] = 1e4 * float(np.mean(diff_m[s2])) if s2.any() else np.nan
                        cell[f"benzer_gun_{nm}"] = int(s2.sum())
                cell.update(episodes(ks, diff_m[ks]))
                cells.append(cell)
                if keep_detail:
                    detail[(round(f, 2), hn, per)] = {"k": ks, "diff": diff_m[ks], "r": r[ks], "base": base[ks]}
    return cells, detail


def judge(c: dict, sign: int) -> bool:
    """sign = -1 ön-kayıtlı (aşağı); +1 karşı yön."""
    P = c.get("P_esli_asagi" if sign < 0 else "P_esli_yukari", np.nan)
    wo = c.get("en_negatif_olay_haric_ort_bp" if sign < 0 else "en_pozitif_olay_haric_ort_bp", np.nan)
    neg_share = c.get("olay_negatif_%", np.nan) if sign < 0 else 100 - c.get("olay_negatif_%", np.nan)
    return bool(sign * c.get("fark_esli_bp", np.nan) > 0 and P >= 0.975
                and sign * c.get("fark_esli_yari1_bp", np.nan) > 0 and sign * c.get("fark_esli_yari2_bp", np.nan) > 0
                and c.get("olay", 0) >= 20 and sign * c.get("olay_medyan_bp", np.nan) > 0 and neg_share >= 50
                and sign * wo > 0)


def main() -> None:
    d = load_ndx(); ts = d.ts; c = np.log(d.close.to_numpy())
    tpl = tpl_index(ts); LS = window_lengths(tpl)
    assert LS == (166, 207, 248), LS
    tvec = {f: [tpl_shape(c, a, b, f) for a, b in tpl.values()] for f in FS}
    tpl_ts = {k: (ts.iloc[a], ts.iloc[b]) for k, (a, b) in tpl.items()}
    res: dict = {"pencere_uzunluklari": LS, "sablonlar": {k: [str(a), str(b), tpl[k][1] - tpl[k][0] + 1] for k, (a, b) in tpl_ts.items()}}

    # ── NDX ana test
    M = Market("NDX", d, tpl_ts, LS, tvec, SPLIT)
    spans = list(M.tpl.values())
    cells, detail = run_cells(M, M.D, spans, ("gelistirme", "dogrulama"), keep_detail=True)
    cdf = pd.DataFrame(cells)

    # ── plasebo (yalnız NDX geliştirme)
    lens = [b - a + 1 for a, b in tpl.values()]
    lo_start = int(ts.searchsorted(pd.Timestamp("2016-06-01", tz="UTC")))
    t_lo, t_hi = min(a for a, _ in spans), max(b for _, b in spans)
    hi_start = int(ts.searchsorted(pd.Timestamp("2026-09-30", tz="UTC"))) - max(lens)
    plac = []
    for p in range(N_PLACEBO):
        pspans = []
        while len(pspans) < 3:
            Lp = lens[len(pspans)]
            a = int(rng.integers(lo_start, hi_start))
            b = a + Lp - 1
            if b >= t_lo - 0 and a <= t_hi:
                continue
            pspans.append((a, b))
        ptv = {f: [tpl_shape(c, a, b, f) for a, b in pspans] for f in FS}
        Dp = {f: dist_argmin(M.S[f], ptv[f])[0] for f in FS}
        # konservatif dışlama: pencere (≤248) ∪ ufuk (≤138) plasebo şablonuyla çakışan sorgular
        exc = [(a - 0, b) for a, b in pspans]
        for f in FS:
            badp = np.zeros(len(M.Q), bool)
            for a, b in exc:
                badp |= (M.Q >= a - 138) & (M.Q <= b + 247)
            Dp[f] = np.where(badp, np.nan, Dp[f])
        pc, _ = run_cells(M, Dp, spans, ("gelistirme",), boot=False)
        for x in pc:
            plac.append({"p": p, "f": x["f"], "ufuk": x["ufuk"], "fark_esli_bp": x["fark_esli_bp"],
                         "olay_medyan_bp": x.get("olay_medyan_bp", np.nan), "olay": x.get("olay", 0)})
    pdf = pd.DataFrame(plac); pdf.to_csv(OUT / "plasebo_hucreler.csv", index=False)
    pct = []
    for i, row in cdf.iterrows():
        if row.donem != "gelistirme":
            pct.append((np.nan, np.nan)); continue
        q = pdf[(pdf.f == row.f) & (pdf.ufuk == row.ufuk)]
        pct.append((100 * float((q.fark_esli_bp <= row.fark_esli_bp).mean()),
                    100 * float((q.olay_medyan_bp <= row.olay_medyan_bp).mean())))
    cdf["plasebo_yuzdelik_fark"] = [x[0] for x in pct]
    cdf["plasebo_yuzdelik_olay_medyan"] = [x[1] for x in pct]
    cdf["GECER_asagi"] = [judge(r, -1) if r["donem"] == "gelistirme" else np.nan for r in cdf.to_dict("records")]
    cdf["GUCLU_asagi"] = [bool(r["GECER_asagi"] == True and r.get("P_esli_asagi", 0) >= BONF and r["plasebo_yuzdelik_fark"] <= 5)
                          if r["donem"] == "gelistirme" else np.nan for r in cdf.to_dict("records")]
    cdf["karsi_yon_olcutleri"] = [judge(r, +1) if r["donem"] == "gelistirme" else np.nan for r in cdf.to_dict("records")]
    cdf["karsi_yon_guclu"] = [bool(r["karsi_yon_olcutleri"] == True and r.get("P_esli_yukari", 0) >= BONF2 and r["plasebo_yuzdelik_fark"] >= 95)
                              if r["donem"] == "gelistirme" else np.nan for r in cdf.to_dict("records")]
    cdf.to_csv(OUT / "hucreler_ndx.csv", index=False)

    # olay listesi (geliştirme, %2) — şeffaflık
    ev = []
    for (f, hn, per), v in detail.items():
        if per != "gelistirme" or len(v["k"]) == 0:
            continue
        k = v["k"]; eid = np.concatenate([[0], np.cumsum(np.diff(k) > EP_GAP)])
        for e in np.unique(eid):
            s = eid == e
            ev.append({"f": f, "ufuk": hn, "olay": int(e), "ilk_gun": str(M.tq.iloc[k[s][0]].date()),
                       "son_gun": str(M.tq.iloc[k[s][-1]].date()), "gun": int(s.sum()),
                       "ort_getiri_bp": 1e4 * float(v["r"][s].mean()), "ort_fark_esli_bp": 1e4 * float(v["diff"][s].mean())})
    pd.DataFrame(ev).to_csv(OUT / "olaylar_ndx_gelistirme.csv", index=False)

    # ── tanımlayıcı: şablon-başına dedektör (geliştirme)
    per_t = []
    for j, k in enumerate(tpl):
        Dk = {f: dist_argmin(M.S[f], [tvec[f][j]])[0] for f in FS}
        pc, _ = run_cells(M, Dk, spans, ("gelistirme",))
        for x in pc:
            x["sablon"] = k
        per_t += pc
    pd.DataFrame(per_t).to_csv(OUT / "hucreler_ndx_sablon_basina.csv", index=False)

    # ── tanımlayıcı: eşleşen pencerelerin içi (f=1, geliştirme, %2)
    f = 1.0; Df = M.D[f]
    thr2 = np.percentile(Df[M.dev_q & np.isfinite(Df)], 2)
    sim = M.dev_q & (Df <= thr2)
    Lb = M.argL[f][sim]; Qs = M.Q[sim]
    inside = [(M.c[q] - M.c[q - L + 1], np.log(d.high.iloc[q - L + 1:q + 1].max() / d.low.iloc[q - L + 1:q + 1].min())) for q, L in zip(Qs, Lb)]
    ret_t, vol_t = M.trailing(1.0)
    e10v = np.nanpercentile(vol_t[M.dev_q], np.linspace(0, 100, 11))
    res["esleseni_ici_f1"] = {"benzer_gun": int(sim.sum()),
                              "pencere_ici_net_%_medyan": 100 * float(np.median([x[0] for x in inside])),
                              "pencere_ici_net_%_ceyrekler": [100 * float(np.percentile([x[0] for x in inside], q)) for q in (25, 75)],
                              "pencere_ici_aralik_%_medyan": 100 * float(np.median([x[1] for x in inside])),
                              "oynaklik_ondaligi_dagilimi": np.bincount(np.clip(qbin(vol_t[sim], e10v), 0, 9), minlength=10).tolist(),
                              "en_yakin_sablon_payi": {k: int((M.argt[f][sim] == j).sum()) for j, k in enumerate(tpl)}}
    res["sablon_ici_oynaklik_ondaligi"] = {}
    for k, (a, b) in tpl.items():
        v = M.r1.iloc[b - 207 + 1:b + 1].std()
        res["sablon_ici_oynaklik_ondaligi"][k] = int(qbin(np.array([v]), e10v)[0])

    # ── bugün
    now = {}
    last_q = len(M.Q) - 1
    for f in FS:
        Df = M.D[f]; ok = M.dev_q & np.isfinite(Df)
        D_last_bar, at, aL = dist_argmin({L: (shapes(c, np.array([len(c) - int(round(f * L))]), int(round(f * L))), np.array([True])) for L in LS}, tvec[f])
        now[f"f={f:.2f}"] = {
            "son_bar": str(ts.iloc[-1]), "D_son_bar": float(D_last_bar[0]), "r_son_bar": float(r_from_d(D_last_bar[0])),
            "yuzdelik_son_bar_%": 100 * float((Df[ok] <= D_last_bar[0]).mean()), "en_yakin_sablon": list(tpl)[int(at[0])],
            "son_sorgu": str(M.tq.iloc[last_q]), "D_son_sorgu": float(Df[last_q]),
            "yuzdelik_son_sorgu_%": 100 * float((Df[ok] <= Df[last_q]).mean()),
            "son_60_sorguda_%2_benzer": [str(M.tq.iloc[i].date()) for i in range(last_q - 59, last_q + 1) if Df[i] <= np.percentile(Df[ok], 2)],
            "son_60_sorguda_%5_benzer": [str(M.tq.iloc[i].date()) for i in range(last_q - 59, last_q + 1) if Df[i] <= np.percentile(Df[ok], 5)],
        }
    res["bugun"] = now

    # ── DAX
    dax = load_dax()
    MD = Market("DAX", dax, tpl_ts, LS, tvec, DAX_SPLIT)
    dcells, _ = run_cells(MD, MD.D, list(MD.tpl.values()), ("gelistirme", "dogrulama"))
    ddf = pd.DataFrame(dcells)
    ddf["ayni_yon_teyit_asagi"] = [bool(r["fark_esli_bp"] < 0 and r.get("P_esli_asagi", 0) >= 0.95 and r.get("olay", 0) >= 10)
                                   if r["donem"] == "gelistirme" else np.nan for r in ddf.to_dict("records")]
    ddf.to_csv(OUT / "hucreler_dax.csv", index=False)

    (OUT / "sonuc.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 60); pd.set_option("display.max_rows", 200)
    show = ["piyasa", "f", "ufuk", "donem", "benzer_gun", "olay", "ort_bp_benzer", "yukari_%_benzer", "ort_bp_tum", "ort_bp_esli_taban",
            "yukari_%_esli_taban", "fark_tum_bp", "fark_esli_bp", "P_esli_asagi", "P_esli_yukari", "fark_esli_yari1_bp", "fark_esli_yari2_bp",
            "olay_medyan_bp", "olay_negatif_%", "en_negatif_olay_haric_ort_bp", "en_pozitif_olay_haric_ort_bp"]
    print(cdf[show + ["plasebo_yuzdelik_fark", "plasebo_yuzdelik_olay_medyan", "GECER_asagi", "GUCLU_asagi", "karsi_yon_olcutleri", "karsi_yon_guclu"]].round(3).to_string(index=False))
    print(ddf[show + ["ayni_yon_teyit_asagi"]].round(3).to_string(index=False))
    pt = pd.DataFrame(per_t)
    print(pt[["sablon", "f", "ufuk", "benzer_gun", "olay", "fark_esli_bp", "P_esli_asagi", "olay_medyan_bp", "olay_negatif_%"]].round(3).to_string(index=False))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
