"""SC-21 — NDX E2X3+BE1 derin dallanma (PROTOCOL SC-21). Gövde = SC-20 F2_be1.

Kullanım:
  python src/sc21_derin.py PARITE                 → yol simülatörü ↔ C çekirdeği (be1, taban) eşitliği
  python src/sc21_derin.py KESIF                  → results/sc21_kesif.csv/json (aile adayları)
  python src/sc21_derin.py DOGRULAMA a,b,...      → results/sc21_dogrulama.json (tek atış)
  python src/sc21_derin.py TASIMA                 → results/sc21_tasima.json (DAX/JPN225 be1, betimleyici)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SC08_AN", "son")
import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc13_strateji as S13  # noqa: E402
import sc14_bakis as B  # noqa: E402
import sc20_ndx_dal as P  # noqa: E402
import sc_degerlendir as D  # noqa: E402

R = S13.R
INF = np.inf
GOVDE = dict(yon=1, q=0.998, sl=1.0, T=480, be=1.0)
META_KAT = 5
META_ARINMA_S = 2 * 86400
NEDEN = {0: "STOP", 1: "TP", 2: "IZ", 3: "ZAMAN", 4: "SON", 5: "ERKEN", 6: "IVMESIZ"}


# ───────────────────────── yol simülatörü ─────────────────────────
@njit(cache=True)
def _yol(t, o, h, l, c, s, i0, sld, sk, T, be, tp, tpf, iz_a, iz_d, add_a, e_T2, e_min, e_lock, f_N, f_x, m_N1, m_v1, m_N2, m_v2):
    n_t, n = len(i0), len(t)
    pnl = np.empty(n_t)
    jx = np.empty(n_t, np.int64)
    ned = np.empty(n_t, np.int64)
    mfe_o = np.empty(n_t)
    risk = np.empty(n_t)
    ekl = np.zeros(n_t, np.int64)
    for k in range(n_t):
        i = i0[k]
        sl = sld[k]
        E = o[i] + sk * s[i]
        S = E - sl
        Tp = E + tp * sl
        w, real, mfe, tas = 1.0, 0.0, 0.0, False
        tcik = t[i] + T * 60
        uzadi, f_ok, m1_ok, m2_ok = False, False, False, False
        ek, E2, rmax = 0, 0.0, 1.0
        px, r, j_son = c[n - 1], 4, n - 1
        for j in range(i, n):
            if j > i:
                el = t[j] - t[i]
                if t[j] >= tcik:
                    if np.isfinite(e_T2) and (not uzadi) and (c[j - 1] - E) >= e_min * sl:
                        uzadi = True
                        tcik = t[i] + e_T2 * 60
                        S = max(S, E + e_lock * sl)
                    else:
                        px, r, j_son = o[j], 3, j
                        break
                if np.isfinite(f_N) and (not f_ok) and el >= f_N * 60:
                    f_ok = True
                    if c[j - 1] <= E - f_x * sl:
                        px, r, j_son = o[j], 5, j
                        break
                if np.isfinite(m_N1) and (not m1_ok) and el >= m_N1 * 60:
                    m1_ok = True
                    if mfe < m_v1 * sl:
                        px, r, j_son = o[j], 6, j
                        break
                if np.isfinite(m_N2) and (not m2_ok) and el >= m_N2 * 60:
                    m2_ok = True
                    if mfe < m_v2 * sl:
                        px, r, j_son = o[j], 6, j
                        break
                if ek == 1:
                    if o[j] <= S:
                        ek = 3
                    else:
                        E2 = o[j] + sk * s[j]
                        ek = 2
                        rmax = max(rmax, (E2 - S) / sl + w * max(E - S, 0.0) / sl)
            if o[j] <= S:
                px, r, j_son = o[j], (2 if tas else 0), j
                break
            if o[j] >= Tp:
                real += tpf * (o[j] - E)
                w -= tpf
                Tp = INF
                if w <= 1e-9:
                    px, r, j_son = o[j], 1, j
                    break
            if l[j] <= S:
                px, r, j_son = S, (2 if tas else 0), j
                break
            if h[j] >= Tp:
                real += tpf * (Tp - E)
                w -= tpf
                Tp = INF
                if w <= 1e-9:
                    px, r, j_son = E + tp * sl, 1, j
                    break
            fav = h[j] - E
            mfe = max(mfe, fav)
            if np.isfinite(add_a) and ek == 0 and fav >= add_a * sl:
                ek = 1
            if fav >= iz_a * sl:
                ns = h[j] - iz_d * sl
                if ns > S:
                    S, tas = ns, True
            if fav >= be * sl:
                ns = E
                if ns > S:
                    S, tas = ns, True
        p = real + w * (px - E)
        if ek == 2:
            p += px - E2
        pnl[k], jx[k], ned[k], mfe_o[k], risk[k], ekl[k] = p, j_son, r, mfe / sl, rmax, int(ek == 2)
    return pnl, jx, ned, mfe_o, risk, ekl


def _f(c: dict, ad: str, vars_: float = INF) -> float:
    v = c.get(ad)
    return float(vars_ if v is None else v)


def sim(M, k: np.ndarray, c: dict, sk: float = 1.0) -> pd.DataFrame:
    bar = M.bar
    i0 = k + 1
    a = S13.atr_h1(M, k)
    m = (i0 < len(bar) - 2) & np.isfinite(a) & (a > 0)
    sl = c["sl"] * a[m]
    iz = c.get("iz") or (INF, 0.0)
    m1 = c.get("ivme1") or (INF, 0.0)
    m2 = c.get("ivme2") or (INF, 0.0)
    ex = c.get("uzat") or (INF, 0.0, 0.0)
    fl = c.get("erken") or (INF, 0.0)
    tp = c.get("tp") or (INF, 1.0)
    pnl, jx, ned, mfe, risk, ekl = _yol(bar.t.astype(np.int64), bar.o, bar.h, bar.l, bar.c, bar.s, i0[m].astype(np.int64), sl,
                                        float(sk), float(c["T"]), _f(c, "be"), float(tp[0]), float(tp[1]),
                                        float(iz[0]), float(iz[1]), _f(c, "ekle"), float(ex[0]), float(ex[1]), float(ex[2]),
                                        float(fl[0]), float(fl[1]), float(m1[0]), float(m1[1]), float(m2[0]), float(m2[1]))
    ref = bar.o[i0[m]]
    bp = pnl / ref * 1e4
    return pd.DataFrame({"i0": i0[m], "t0": bar.t[i0[m]], "j": jx, "t1": bar.t[jx], "neden": [NEDEN[x] for x in ned], "bp": bp,
                         "R": bp / (sl / ref * 1e4), "puan": pnl, "mfe_R": mfe, "risk_R": risk, "ekleme": ekl, "sl_bp": sl / ref * 1e4, "k": k[m]})


# ───────────────────────── sıra-bağımlı süzgeçler (C3/C4) ─────────────────────────
def sira_suz(r: pd.DataFrame, tur: str) -> pd.DataFrame:
    """Tek pozisyon yürüyüşü üzerinde: C3 NY gününde tam stop sonrası o gün giriş yok; C4 art arda 3 tam stop → gölge, gölge kazanınca dön."""
    d = r.sort_values("t0").reset_index(drop=True)
    gun = pd.to_datetime(d.t0, unit="s", utc=True).dt.tz_convert("America/New_York").dt.date.to_numpy()
    tut, son, kilit_gun, seri, golge = [], -1, None, 0, False
    for i in range(len(d)):
        if d.t0[i] < son:
            continue
        tam_stop = d.neden[i] == "STOP"
        if tur == "gunluk":
            if kilit_gun == gun[i]:
                continue
            tut.append(i)
            son = d.t1[i]
            if tam_stop:
                kilit_gun = gun[i]
        else:
            son = d.t1[i]
            if golge:
                if d.R[i] > 0:
                    golge, seri = False, 0
                continue
            tut.append(i)
            seri = seri + 1 if tam_stop else 0
            if seri >= 3:
                golge = True
    return d.iloc[tut].reset_index(drop=True)


# ───────────────────────── meta-etiket (A2) ─────────────────────────
def _meta_X(M, A: pd.DataFrame) -> pd.DataFrame:
    j = A.j.to_numpy()
    ozl = M.ozellik(j, M.bar.c[j], np.ones(len(j), int), M.bar.t[j] + 60)
    ek = A[["skor", "vix", "vix_oran", "ny_dk", "gun"]].assign(h4=A.h4_trend.astype(float), d1=A.d1_trend.astype(float),
                                                               ara=np.log1p(np.minimum(A.ara_s, 30 * 86400)))
    return pd.concat([ozl.reset_index(drop=True), ek.reset_index(drop=True)], axis=1).astype(np.float32)


def _regresor():
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.05, min_samples_leaf=50, random_state=0)


def meta_tahmin(ctx: dict, q: float) -> dict:
    """KEŞİF OOF tahmin+eşik bilgisi ve DOĞRULAMA tahmini; önbellekli."""
    yol = R / f"sc21_meta_q{q}.parquet"
    if yol.exists():
        return {"df": pd.read_parquet(yol)}
    M, G = ctx["M"], ctx["G"]
    A = P.ates(G, ctx["esik"][q], 1)
    A = A[(M.bar.t[A.j.to_numpy()] >= D.ts(P.TUM[0])) & (M.bar.t[A.j.to_numpy()] < D.ts(P.TUM[1]))].reset_index(drop=True)
    A = P.ozellik_ek(M, A)
    r = sim(M, A.j.to_numpy(), GOVDE)
    A = A[A.j.isin(r.k)].reset_index(drop=True)
    y = np.clip(r.set_index("k").loc[A.j, "R"].to_numpy(), -5, 5)
    X = _meta_X(M, A)
    t = M.bar.t[A.j.to_numpy()]
    kes = (t < D.ts(P.DONEM["KESIF"][1]))
    idx_k = np.flatnonzero(kes)
    sinir = np.quantile(t[idx_k], np.linspace(0, 1, META_KAT + 1))
    kat = np.clip(np.searchsorted(sinir, t, side="right") - 1, 0, META_KAT - 1)
    oof = np.full(len(A), np.nan)
    for f in range(1, META_KAT):
        tr = kes & (kat < f) & (t < sinir[f] - META_ARINMA_S)
        te = kes & (kat == f)
        oof[te] = _regresor().fit(X[tr], y[tr]).predict(X[te])
    ic0 = kes & (kat == 0)
    oof[ic0] = _regresor().fit(X[ic0], y[ic0]).predict(X[ic0])       # 1. kat: yalnız eşik kaynağı, ölçüme girmez
    son = _regresor().fit(X[kes], y[kes])
    dog = ~kes
    tah = np.where(kes, oof, np.nan)
    tah[dog] = son.predict(X[dog])
    df = pd.DataFrame({"j": A.j, "t": t, "kat": np.where(kes, kat, -1), "tahmin": tah, "y": y})
    df.to_parquet(yol)
    return {"df": df}


def meta_sec(df: pd.DataFrame, ust: float) -> pd.Series:
    """Nedensel eşik: k. kat için önceki katların tahminlerinin (1−ust) kantili; DOĞRULAMA için tüm KEŞİF OOF kantili."""
    sec = pd.Series(False, index=df.index)
    for f in range(1, META_KAT):
        es = np.quantile(df.loc[df.kat.between(0, f - 1), "tahmin"], 1 - ust)
        sec |= (df.kat == f) & (df.tahmin >= es)
    es = np.quantile(df.loc[df.kat >= 0, "tahmin"], 1 - ust)
    sec |= (df.kat == -1) & (df.tahmin >= es)
    return sec


def meta_bas(ctx: dict) -> str:
    df = meta_tahmin(ctx, 0.99)["df"]
    return str(pd.to_datetime(df.loc[df.kat == 1, "t"].min(), unit="s").date())


# ───────────────────────── hücreler ─────────────────────────
def hucreler() -> list[dict]:
    H = [{"ad": "GOVDE", "aile": "-", **GOVDE}]
    for q in (0.99, 0.995, 0.997):
        H.append({"ad": f"A1_q{q}", "aile": "A", **GOVDE, "q": q})
    for q, u in ((0.99, 0.3), (0.99, 0.5), (0.995, 0.5)):
        H.append({"ad": f"A2_meta_q{q}_ust{int(u * 100)}", "aile": "A", **GOVDE, "q": q, "meta": u})
    for a in (1.0, 1.5):
        H.append({"ad": f"B1_ekle{a}", "aile": "B", **GOVDE, "ekle": a})
    for T2 in (960, 1440):
        H.append({"ad": f"B2_uzat{T2}", "aile": "B", **GOVDE, "uzat": (T2, 1.0, 0.5)})
    for tp in (1.5, 2.0):
        H.append({"ad": f"B3_kismi{tp}", "aile": "B", **GOVDE, "tp": (tp, 0.5)})
    H.append({"ad": "B4_genis_iz", "aile": "B", **GOVDE, "T": 960, "iz": (2.0, 1.5)})
    for N in (60, 120):
        H.append({"ad": f"C1_erken{N}", "aile": "C", **GOVDE, "erken": (N, 0.5)})
    H.append({"ad": "C2_ivme120", "aile": "C", **GOVDE, "ivme1": (120, 0.25)})
    H.append({"ad": "C2_ivme240", "aile": "C", **GOVDE, "ivme1": (240, 0.5)})
    H.append({"ad": "C3_gunluk", "aile": "C", **GOVDE, "sira": "gunluk"})
    H.append({"ad": "C4_seri", "aile": "C", **GOVDE, "sira": "seri"})
    return H


def ates_k(ctx: dict, c: dict, a: str, b: str) -> np.ndarray:
    M, G = ctx["M"], ctx["G"]
    if c.get("meta"):
        df = meta_tahmin(ctx, c["q"])["df"]
        df = df[meta_sec(df, c["meta"]) & (df.t >= D.ts(a)) & (df.t < D.ts(b))]
        return df.j.to_numpy()
    A = P.ates(G, ctx["esik"][c["q"]], c["yon"])
    jj = A.j.to_numpy()
    return jj[(M.bar.t[jj] >= D.ts(a)) & (M.bar.t[jj] < D.ts(b))]


def kos_hucre(ctx: dict, c: dict, a: str, b: str) -> dict:
    M = ctx["M"]
    k = ates_k(ctx, c, a, b)
    r, rs = sim(M, k, c), sim(M, k, c, 1.5)
    mod = "tek"
    if c.get("sira"):
        r = sira_suz(r, c["sira"])
        rs = rs[rs.k.isin(r.k)]
        mod = "eszamanli"
    kk = r.k.to_numpy()
    rng = np.random.default_rng(D.TOHUM)
    kt = B.rastgele(M, kk, a, b, rng) if len(kk) else []
    tbl = [sim(M, z, c)["bp"].to_numpy() for z in kt]
    h = P.olc(M, r, rs, tbl, a, b, mod)
    tek = r if mod == "eszamanli" else D.tek_pozisyon(r)
    h["tek_kayip_orani"] = round(float((tek.R <= 0).mean()), 3)
    h["tek_tam_stop"] = round(float((tek.neden == "STOP").mean()), 3)
    h["azami_risk_R"] = round(float(tek.risk_R.max()), 3)
    h["ekleme_orani"] = round(float(tek.ekleme.mean()), 3)
    h["en_kotu5_gun_puan"] = round(float(tek.groupby(tek.t0 // 86400).puan.sum().nsmallest(5).sum()), 1)
    return h


# ───────────────────────── koşucular ─────────────────────────
def parite() -> None:
    ctx = P.hazirla()
    a, b = P.DONEM["KESIF"]
    out = {}
    for ad, c in (("taban", dict(P.TABAN)), ("be1", dict(GOVDE))):
        k = ates_k(ctx, {**c, "yon": 1}, a, b)
        r0 = P.sim(ctx["M"], k, c)
        r1 = sim(ctx["M"], k, c)
        fark = np.abs(r0.bp.to_numpy() - r1.bp.to_numpy())
        out[ad] = {"n": len(k), "maks_fark_bp": float(fark.max()), "ayni_cikis": float((r0.j.to_numpy() == r1.j.to_numpy()).mean())}
    print(out)
    (R / "sc21_parite.json").write_text(json.dumps(out, indent=1))


def gecer(h: dict, t: dict) -> bool:
    return P.gecer_kesif(h, t)


def kesif() -> None:
    ctx = P.hazirla()
    a, b = P.DONEM["KESIF"]
    mb = meta_bas(ctx)
    out = {"meta_olcum_bas": mb}
    tab = {"tam": kos_hucre(ctx, {"ad": "GOVDE", **GOVDE}, a, b), "meta": kos_hucre(ctx, {"ad": "GOVDE", **GOVDE}, mb, b)}
    for c in hucreler():
        aa = mb if c.get("meta") else a
        h = tab["meta" if c.get("meta") else "tam"] if c["ad"] == "GOVDE" else kos_hucre(ctx, c, aa, b)
        out[c["ad"]] = {"tanim": {k: v for k, v in c.items() if k != "ad"}, "donem": [aa, b], **h}
        D.kaydet("SC-21", "KESIF", {"hucre": c["ad"]}, {k: v for k, v in h.items() if k != "yillik_R"})
        print(c["ad"], {x: h.get(x) for x in ("n", "ort_R", "isabet", "fark", "fark_P", "tek_n", "puan_yil", "sharpe",
                                               "maks_dusus_puan", "tek_kayip_orani", "azami_risk_R")}, flush=True)
    out["GOVDE_META_DONEMI"] = tab["meta"]
    aday, gecen = {}, {}
    for aile, anahtar in (("A", "puan_yil"), ("B", "puan_yil"), ("C", "sharpe")):
        g = []
        for c in hucreler():
            if c["aile"] != aile:
                continue
            h = out[c["ad"]]
            t = tab["meta" if c.get("meta") else "tam"]
            ok = gecer(h, t)
            if aile == "A":
                ok = ok and h["tek_n"] > t["tek_n"]
            if aile == "C":
                ok = ok and h["maks_dusus_puan"] < t["maks_dusus_puan"]
            if c.get("ekle"):
                ok = ok and h["sharpe"] > t["sharpe"] and h["azami_risk_R"] <= 1.1
            if ok:
                g.append(c["ad"])
        g.sort(key=lambda x: -out[x][anahtar])
        gecen[aile], aday[aile] = g, g[:1]
    out["gecen"], out["aday"] = gecen, aday
    print("GEÇEN", gecen, "→ ADAY", aday)
    (R / "sc21_kesif.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    kol = ("n", "ort_R", "isabet", "basabas_isabet", "fark", "fark_P", "yari1", "yari2", "stres", "tek_n", "tek_R", "tek_isabet",
           "tek_kayip_orani", "tek_tam_stop", "puan_yil", "sharpe", "maks_dusus_puan", "en_kotu5_gun_puan", "azami_risk_R", "ekleme_orani")
    pd.DataFrame([{"ad": k, **{x: v.get(x) for x in kol}} for k, v in out.items() if isinstance(v, dict) and "n" in v]).to_csv(
        R / "sc21_kesif.csv", index=False)


def birlesik(adlar: list[str]) -> dict:
    tanim = {c["ad"]: c for c in hucreler()}
    c = {"ad": "BIRLESIK", "aile": "+", **GOVDE}
    for ad in adlar:
        c.update({k: v for k, v in tanim[ad].items() if k not in ("ad", "aile")})
    return c


def dogrulama(adlar: list[str]) -> None:
    ctx = P.hazirla()
    a, b = P.DONEM["DOGRULAMA"]
    tanim = {c["ad"]: c for c in hucreler()}
    if "BIRLESIK" in adlar:
        tanim["BIRLESIK"] = birlesik([x for x in adlar if x != "BIRLESIK"])
    t = kos_hucre(ctx, tanim["GOVDE"], a, b)
    out = {"GOVDE": t}
    for ad in adlar:
        c = tanim[ad]
        h = kos_hucre(ctx, c, a, b)
        yr = h.get("yillik_R", {})
        s_up, p_up = h["sharpe"] > t["sharpe"], h["puan_yil"] > t["puan_yil"]
        diger = (h["puan_yil"] >= 0.9 * t["puan_yil"]) if s_up else (h["sharpe"] >= 0.9 * t["sharpe"])
        kart = (h["n"] >= 150 and h["ort_R"] > 0 and h["P_EV"] >= 0.90 and h["yari1"] >= 0 and h["yari2"] >= 0 and h["stres"] > 0
                and h["tek_R"] > 0)
        yil_ok = all(yr.get(y, -1) > 0 for y in (2023, 2024, 2025, 2026))
        ek_ok = (not c.get("ekle")) or (s_up and h["azami_risk_R"] <= 1.1)
        h["kontrol"] = {"kart_5olcut": kart, "son4_yil": yil_ok, "fark_P": h["fark_P"] >= 0.95, "tabandan_iyi": (s_up or p_up) and diger,
                        "ekleme_sarti": ek_ok}
        h["hukum"] = "B" if all(h["kontrol"].values()) else "X"
        h["tanim"] = {k: v for k, v in c.items() if k != "ad"}
        out[ad] = h
        D.kaydet("SC-21", "DOGRULAMA", {"hucre": ad}, {k: v for k, v in h.items() if k not in ("yillik_R", "kontrol", "tanim")})
        print(ad, h["hukum"], h["kontrol"], {x: h.get(x) for x in ("n", "ort_R", "isabet", "tek_n", "puan_yil", "sharpe",
                                                                   "maks_dusus_puan", "tek_kayip_orani", "yillik_R")}, flush=True)
    print("GOVDE", {x: t.get(x) for x in ("n", "ort_R", "tek_n", "puan_yil", "sharpe", "maks_dusus_puan", "tek_kayip_orani", "yillik_R")})
    (R / "sc21_dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def tasima() -> None:
    """D ailesi (betimleyici): GOVDE (be1) vs SC-19 tabanı DAX ve JPN225'te, SC-19 penceresi 2022-11-14 → 2026-11-14."""
    import sc08_ozellik as F
    import sc10_klon_kar as C10
    import sc15_tasima as S15
    import sc19_canli_kart as K19
    model, oz, q = B.model_ve_esik()
    a, b = K19.KART_A, K19.Bt
    out = {}
    for ad in ("DAX", "JPN225"):
        bar, vol = S15.bar_yukle(ad) if ad in S15.PIYASA else K19.chunk_bar(ad)
        M = F.Motor(bar, vol)
        yol = R / f"sc21_skor_{ad}.parquet"
        G = pd.read_parquet(yol) if yol.exists() else C10.skorla(M, model, oz, K19.A, K19.Bt)
        G.to_parquet(yol)
        ctx = {"M": M, "G": G, "esik": {0.998: q[0.998]}}
        out[ad] = {}
        for ad_h, c in (("TABAN", dict(P.TABAN)), ("GOVDE_be1", dict(GOVDE))):
            h = kos_hucre(ctx, {"ad": ad_h, **c}, a, b)
            out[ad][ad_h] = h
            print(ad, ad_h, {x: h.get(x) for x in ("n", "ort_R", "P_EV", "fark_P", "tek_n", "puan_yil", "sharpe", "maks_dusus_puan",
                                                   "tek_kayip_orani", "yillik_R")}, flush=True)
    (R / "sc21_tasima.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def _boy_olc(tek: pd.DataFrame, lot: np.ndarray, a: str, b: str) -> dict:
    yil = (D.ts(b) - D.ts(a)) / 86400 / 365.25
    bd = pd.bdate_range(pd.to_datetime(D.ts(a), unit="s"), pd.to_datetime(D.ts(b), unit="s"))
    def sh(l):
        g = pd.Series(tek.puan.to_numpy() * l).groupby(tek.t0.to_numpy() // 86400).sum()
        g = g.reindex(bd.asi8 // 10**9 // 86400, fill_value=0.0)
        return float(g.mean() / g.std() * np.sqrt(252))
    x = tek.puan.to_numpy() * lot
    egri = np.cumsum(x)
    rng = np.random.default_rng(D.TOHUM)
    s0 = sh(lot)
    kar = np.array([sh(rng.permutation(lot)) for _ in range(500)])
    yr = pd.to_datetime(tek.t0, unit="s").dt.year.to_numpy()
    return {"tek_n": len(tek), "puan_yil": round(float(x.sum() / yil), 1), "sharpe": round(s0, 3),
            "maks_dusus_puan": round(float((np.maximum.accumulate(egri) - egri).max()), 1),
            "karistirma_P": round(float((s0 > kar).mean()), 4), "lot_min_maks": [round(float(lot.min()), 2), round(float(lot.max()), 2)],
            "yillik_R": {int(y): round(float((tek.R.to_numpy() * lot)[yr == y].mean()), 3) for y in np.unique(yr)}}


def boyut(donem: str) -> dict:
    ctx = P.hazirla()
    M = ctx["M"]
    a, b = P.DONEM[donem]
    k_tum = ates_k(ctx, GOVDE, P.TUM[0], P.TUM[1])
    r_tum = sim(M, k_tum, GOVDE).sort_values("t0").reset_index(drop=True)
    atr_bp = r_tum.sl_bp.to_numpy()
    ref = pd.Series(atr_bp).shift(1).rolling(250, min_periods=20).median().to_numpy()
    r_tum["l_risk"] = np.where(np.isfinite(ref), ref / atr_bp, 1.0)
    A = P.ozellik_ek(M, pd.DataFrame({"j": r_tum.k, "t": M.bar.t[r_tum.k] + 60, "skor": 0.0}))
    r_tum["vix_hi"] = (A.vix >= P.VIX_ESIK).to_numpy()
    r = r_tum[(r_tum.t0 >= D.ts(a)) & (r_tum.t0 < D.ts(b))]
    tek = D.tek_pozisyon(r).reset_index(drop=True)
    l1 = tek.l_risk.to_numpy()
    l1 = l1 / l1.mean()
    l2 = np.where(tek.vix_hi, 2.0, 1.0)
    l2 = l2 / l2.mean()
    l3 = l1 * l2
    l3 = l3 / l3.mean()
    out = {"GOVDE": _boy_olc(tek, np.ones(len(tek)), a, b)}
    for ad, l in (("S1_esit_risk", l1), ("S2_vix", l2), ("S3_ikisi", l3)):
        out[ad] = _boy_olc(tek, l, a, b)
    t = out["GOVDE"]
    for ad in ("S1_esit_risk", "S2_vix", "S3_ikisi"):
        h = out[ad]
        h["gecer"] = bool(h["sharpe"] > t["sharpe"] and h["karistirma_P"] >= 0.95 and h["maks_dusus_puan"] <= 1.1 * t["maks_dusus_puan"])
        if donem == "DOGRULAMA":
            h["son4_yil"] = all(h["yillik_R"].get(y, -1) > 0 for y in (2023, 2024, 2025, 2026))
        print(donem, ad, h, flush=True)
    print(donem, "GOVDE", t)
    (R / f"sc21_ek1_{donem.lower()}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    return out


if __name__ == "__main__":
    {"PARITE": parite, "KESIF": kesif, "TASIMA": tasima, "EK1": lambda: boyut(sys.argv[2])}.get(sys.argv[1], lambda: dogrulama(sys.argv[2].split(",")))()
