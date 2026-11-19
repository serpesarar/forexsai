"""analiz.py — kaybeden vs kazanan: tek tek tarama + permütasyon sıfırı, kümeleme, ikili kesişim, modeller; TEST + Duka NDX sınaması.
python analiz.py
"""
from __future__ import annotations

import json
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, silhouette_score
from sklearn.tree import DecisionTreeClassifier, export_text

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
M = pd.read_parquet(RES / "ozellikler.parquet")
PRIM = ["MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]
OLD = ["gun_ret", "seans_ret", "son_saat", "son_yarim", "ilk_yarim_saat", "twap_uz", "bosluk", "aralik", "kapanis_konum", "dip_saati",
       "r5", "r20", "rsi2", "sma20_uz", "sma50_uz", "sma200_uz", "rv20", "aralik_oran", "zirve_uz", "vix", "vix_deg", "vix_vix3m",
       "qqq_hacim_oran", "mt5_hacim_oran", "gun", "ay", "opex_k", "opex_a", "olay", "sess_dun", "K1_dun", "K1_son10"]
NEW = [c for c in M.columns if c[:2] in ("m3", "h1", "U_", "F_", "D_", "S_", "T_", "H_", "X_")]
FEATS = [f for f in NEW + OLD if f in M.columns and M[f].notna().mean() > 0.7 and M[f].nunique() > 1]
NPERM = 1000
RNG = np.random.default_rng(11)
M["y"] = (M.net < 0).astype(int)
M["y2"] = (M.net <= -150).astype(int)
M["ay_blok"] = pd.to_datetime(M.d).dt.to_period("M").astype(str)


def imputed(z: pd.DataFrame, ref: pd.DataFrame) -> np.ndarray:
    """Piyasa içi KEŞİF medyanıyla doldur, KEŞİF ort/std ile standartlaştır."""
    med, mu, sd = ref[FEATS].median(), ref[FEATS].mean(), ref[FEATS].std().replace(0, 1)
    return ((z[FEATS].fillna(med) - mu) / sd).fillna(0).values


def auc_matrix(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Her sütun için AUC = P(kaybeden değeri > kazanan değeri), sıra tabanlı (bağlar ortalama sıra)."""
    R = pd.DataFrame(X).rank().values
    n1, n0 = y.sum(), len(y) - y.sum()
    return (R[y == 1].sum(0) - n1 * (n1 + 1) / 2) / (n1 * n0)


def pooled_auc(parts: list[tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    w = np.array([p[1].sum() * (len(p[1]) - p[1].sum()) for p in parts], float)
    A = np.array([auc_matrix(X, y) for X, y in parts])
    return (A * w[:, None]).sum(0) / w.sum()


def blocks(z: pd.DataFrame, era: str) -> list[tuple[np.ndarray, np.ndarray, pd.DataFrame]]:
    out = []
    for f in PRIM:
        a = z[(z.besleme == f) & (z.donem == era)]
        if a.y.sum() >= 5:
            ref = z[(z.besleme == f) & (z.donem == "KESIF")]
            out.append((imputed(a, ref), a.y.values, a))
    return out


def veto_eval(z: pd.DataFrame, mask: np.ndarray) -> dict:
    net = z.net.values
    keep = ~mask
    base_tot, base_loss = net.sum(), net[net < 0].sum()
    v = net[mask]
    boot = []
    if mask.sum() >= 3:
        bl = z.ay_blok.values[mask]
        ub = np.unique(bl)
        for _ in range(1000):
            pick = RNG.choice(ub, len(ub))
            boot.append(np.concatenate([v[bl == u] for u in pick]).mean())
    return {"n": int(len(z)), "veto_n": int(mask.sum()), "veto_ort": round(float(v.mean()), 1) if mask.any() else None,
            "kalan_ort": round(float(net[keep].mean()), 1), "taban_ort": round(float(net.mean()), 1),
            "kar_orani": round(float(net[keep].sum() / base_tot), 3), "zarar_orani": round(float(net[keep][net[keep] < 0].sum() / base_loss), 3),
            "veto_kaybeden_%": round(float((v < 0).mean() * 100), 1) if mask.any() else None,
            "P_veto_ort_eksi": round(float((np.array(boot) < 0).mean()), 3) if boot else None}


def quint_rule(z_all: pd.DataFrame, feed: str, f: str, sign: int, q: float = 0.2) -> tuple[float, int]:
    ref = z_all[(z_all.besleme == feed) & (z_all.donem == "KESIF")][f].dropna()
    return (float(ref.quantile(1 - q)), 1) if sign > 0 else (float(ref.quantile(q)), -1)


def apply_q(z: pd.DataFrame, f: str, thr: float, side: int) -> np.ndarray:
    x = z[f].values
    return np.where(np.isfinite(x), (x >= thr) if side > 0 else (x <= thr), False)


def rule_test(f_or_pair, signs, q: float, label: str = "y") -> dict:
    """Donmuş KEŞİF eşikleriyle TEST'te veto: piyasa başına + havuz + Duka NDX."""
    feats = f_or_pair if isinstance(f_or_pair, (list, tuple)) else [f_or_pair]
    out, pool_mask, pool_z = {}, [], []
    for feed in PRIM + ["DUKA_NDX"]:
        z = M[(M.besleme == feed) & (M.donem == "TEST")]
        m = np.ones(len(z), bool)
        for f, s in zip(feeds_iter(feats), signs):
            thr, side = quint_rule(M, feed, f, s, q)
            m &= apply_q(z, f, thr, side)
        out[feed] = veto_eval(z, m)
        if feed in PRIM:
            pool_mask.append(m)
            pool_z.append(z)
    out["HAVUZ_MT5"] = veto_eval(pd.concat(pool_z), np.concatenate(pool_mask))
    yon = sum(1 for f in PRIM if out[f]["veto_ort"] is not None and out[f]["veto_ort"] < out[f]["kalan_ort"])
    out["yon_tutan_piyasa"] = yon
    return out


def feeds_iter(x):
    return list(x)


def verdict(r: dict) -> str:
    p, d = r["HAVUZ_MT5"], r["DUKA_NDX"]
    if p["veto_n"] < 5:
        return "yetersiz"
    duka_ok = d["veto_ort"] is not None and d["veto_ort"] < d["kalan_ort"]
    if (p["veto_ort"] < 0 and (p["P_veto_ort_eksi"] or 0) >= 0.9 and p["kar_orani"] >= 0.95 and p["zarar_orani"] <= 0.80
            and r["yon_tutan_piyasa"] >= 3 and duka_ok):
        return "B"
    if p["veto_ort"] < p["taban_ort"] - 30 and r["yon_tutan_piyasa"] >= 3:
        return "C"
    return "X"


# ---------------- 1. tek tek ----------------
def step_univariate(label: str = "y") -> dict:
    yk = M[label]
    parts = []
    for X, y, a in blocks(M.assign(y=yk), "KESIF"):
        parts.append((X, a[label].values))
    real = pooled_auc(parts)
    mx = []
    for _ in range(NPERM):
        mx.append(np.abs(pooled_auc([(X, RNG.permutation(y)) for X, y in parts]) - 0.5).max())
    thr = float(np.quantile(mx, 0.95))
    test_parts = [(X, a[label].values) for X, y, a in blocks(M.assign(y=yk), "TEST")]
    tauc = pooled_auc(test_parts)
    df = pd.DataFrame({"ozellik": FEATS, "kesif_auc": real, "test_auc": tauc, "aile": [f.split("_")[0] if f in NEW else "eski" for f in FEATS]})
    df["sapma"] = (df.kesif_auc - 0.5).abs()
    df["test_ayni_yon"] = np.sign(df.kesif_auc - 0.5) == np.sign(df.test_auc - 0.5)
    df = df.sort_values("sapma", ascending=False)
    sel = df[(df.sapma >= thr)].ozellik.tolist() or []
    top = df.head(10).ozellik.tolist()
    rules = {}
    for f in dict.fromkeys(sel + top):
        s = 1 if df.set_index("ozellik").kesif_auc[f] > 0.5 else -1
        r = rule_test([f], [s], 0.2)
        r["hukum"] = verdict(r)
        rules[f] = r
    corr = float(np.corrcoef(df.kesif_auc, df.test_auc)[0, 1])
    return {"ozellik_say": len(FEATS), "aile_hatasi_esik_sapma": round(thr, 4), "esigi_gecen": sel,
            "kesif_test_auc_korelasyon": round(corr, 3), "test_ayni_yon_orani_ilk20": round(float(df.head(20).test_ayni_yon.mean()), 2),
            "tablo": df.round(4).to_dict("records"), "kurallar": rules}


# ---------------- 2. kümeleme ----------------
def step_cluster() -> dict:
    K = M[M.besleme.isin(PRIM) & (M.donem == "KESIF")]
    T = M[M.besleme.isin(PRIM) & (M.donem == "TEST")]
    def mat(z):
        return np.vstack([imputed(z[z.besleme == f], M[(M.besleme == f) & (M.donem == "KESIF")]) for f in PRIM if (z.besleme == f).any()]), \
            pd.concat([z[z.besleme == f] for f in PRIM if (z.besleme == f).any()])
    XK, zk = mat(K)
    XT, zt = mat(T)
    pca = PCA(n_components=10, random_state=0).fit(XK)
    PK, PT = pca.transform(XK), pca.transform(XT)
    sil = {k: float(silhouette_score(PK, KMeans(k, n_init=20, random_state=0).fit_predict(PK))) for k in range(2, 7)}
    kbest = max(sil, key=sil.get)
    km = KMeans(kbest, n_init=20, random_state=0).fit(PK)
    lk, lt = km.labels_, km.predict(PT)
    rows = []
    for c in range(kbest):
        a, b = zk[lk == c], zt[lt == c]
        rows.append({"kume": c, "kesif_n": len(a), "kesif_kaybeden_%": round(a.y.mean() * 100, 1), "kesif_ort": round(a.net.mean(), 1),
                     "test_n": len(b), "test_kaybeden_%": round(b.y.mean() * 100, 1) if len(b) else None, "test_ort": round(b.net.mean(), 1) if len(b) else None})
    # her küme için en ayırt edici 5 özellik (KEŞİF z ortalaması)
    prof = {}
    for c in range(kbest):
        mu = XK[lk == c].mean(0)
        idx = np.argsort(-np.abs(mu))[:6]
        prof[c] = {FEATS[i]: round(float(mu[i]), 2) for i in idx}
    # kaybeden yol tipleri (betimleyici) + giriş anında tanınma
    L = M[M.besleme.isin(PRIM) & (M.y == 1)].copy()
    pth = ["c17", "c20", "c00", "c04", "c0930", "g1", "mae", "tutus_gun"]
    Lp = L[pth].fillna(L[pth].median())
    Z = ((Lp - Lp.mean()) / Lp.std()).values
    silp = {k: float(silhouette_score(Z, KMeans(k, n_init=20, random_state=0).fit_predict(Z))) for k in range(2, 5)}
    kp = max(silp, key=silp.get)
    L["tip"] = KMeans(kp, n_init=20, random_state=0).fit_predict(Z)
    types = []
    for t in range(kp):
        g = L[L.tip == t]
        rec = {"tip": t, "n": len(g), "ort_net": round(g.net.mean(), 1), **{c: round(float(g[c].median()), 1) for c in pth}}
        # tanınma: KEŞİF'te tip-t kaybedenleri vs kazananlar (L1 lojistik), TEST AUC
        W = M[M.besleme.isin(PRIM) & (M.y == 0)]
        tr = pd.concat([g[g.donem == "KESIF"], W[W.donem == "KESIF"]])
        te = pd.concat([g[g.donem == "TEST"], W[W.donem == "TEST"]])
        if (tr.y == 1).sum() >= 8 and (te.y == 1).sum() >= 8:
            Xtr = np.vstack([imputed(tr[tr.besleme == f], M[(M.besleme == f) & (M.donem == "KESIF")]) for f in PRIM])
            ytr = np.concatenate([tr[tr.besleme == f].y.values for f in PRIM])
            Xte = np.vstack([imputed(te[te.besleme == f], M[(M.besleme == f) & (M.donem == "KESIF")]) for f in PRIM])
            yte = np.concatenate([te[te.besleme == f].y.values for f in PRIM])
            lr = LogisticRegression(penalty="l1", C=0.1, solver="liblinear", class_weight="balanced").fit(Xtr, ytr)
            rec["giriste_taninma_test_auc"] = round(float(roc_auc_score(yte, lr.predict_proba(Xte)[:, 1])), 3)
            rec["kesif_auc_icsel"] = round(float(roc_auc_score(ytr, lr.predict_proba(Xtr)[:, 1])), 3)
        types.append(rec)
    return {"siluet": {k: round(v, 3) for k, v in sil.items()}, "k": kbest, "kumeler": rows, "kume_profili": prof,
            "kaybeden_tipleri_siluet": {k: round(v, 3) for k, v in silp.items()}, "kaybeden_tipleri": types}


# ---------------- 3a. ikili kesişim ----------------
def pair_scan(top: list[str], signs: dict, label: str = "y") -> dict:
    K = M[M.besleme.isin(PRIM) & (M.donem == "KESIF")].reset_index(drop=True)
    masks = {}
    for f in top:
        m = np.zeros(len(K), bool)
        for feed in PRIM:
            idx = (K.besleme == feed).values
            thr, side = quint_rule(M, feed, f, signs[f], 1 / 3)
            m[idx] = apply_q(K[idx], f, thr, side)
        masks[f] = m
    net = K.net.values
    pairs = list(combinations(top, 2))
    def best(netv):
        bv, bp = np.inf, None
        for a, b in pairs:
            m = masks[a] & masks[b]
            if m.sum() >= 12:
                v = netv[m].mean()
                if v < bv:
                    bv, bp = v, (a, b)
        return bv, bp
    real_v, real_p = best(net)
    feeds = K.besleme.values
    null = []
    for _ in range(300):
        perm = net.copy()
        for feed in PRIM:
            ix = np.flatnonzero(feeds == feed)
            perm[ix] = net[RNG.permutation(ix)]
        null.append(best(perm)[0])
    p = float((np.array(null) <= real_v).mean())
    allp = []
    for a, b in pairs:
        m = masks[a] & masks[b]
        if m.sum() >= 12:
            allp.append({"cift": f"{a} & {b}", "kesif_n": int(m.sum()), "kesif_ort": round(float(net[m].mean()), 1),
                         "kesif_kaybeden_%": round(float((net[m] < 0).mean() * 100), 1)})
    allp = sorted(allp, key=lambda r: r["kesif_ort"])[:10]
    tests = {}
    for r in allp[:5]:
        a, b = r["cift"].split(" & ")
        t = rule_test([a, b], [signs[a], signs[b]], 1 / 3)
        t["hukum"] = verdict(t)
        tests[r["cift"]] = t
    return {"cift_say": len(pairs), "en_iyi": real_p, "en_iyi_kesif_ort": round(float(real_v), 1), "permutasyon_P_sans": round(p, 3),
            "ilk10": allp, "ilk5_test": tests}


# ---------------- 3b. modeller ----------------
def models(label: str = "y") -> dict:
    def stack(era, feeds=PRIM):
        Xs, zs = [], []
        for f in feeds:
            z = M[(M.besleme == f) & (M.donem == era)]
            Xs.append(imputed(z, M[(M.besleme == f) & (M.donem == "KESIF")]))
            zs.append(z)
        return np.vstack(Xs), pd.concat(zs)
    XK, zk = stack("KESIF")
    XT, zt = stack("TEST")
    XD, zd = stack("TEST", ["DUKA_NDX"])
    yk = zk[label].values
    # zaman bloklu OOF (KEŞİF içi 5 kat, yıl sırasına göre) → eşik %85'lik
    order = np.argsort(pd.to_datetime(zk.d).values)
    folds = np.array_split(order, 5)
    out = {}
    mk = {"agac_d2": lambda: DecisionTreeClassifier(max_depth=2, min_samples_leaf=15, class_weight="balanced", random_state=0),
          "agac_d3": lambda: DecisionTreeClassifier(max_depth=3, min_samples_leaf=15, class_weight="balanced", random_state=0),
          "l1_lojistik": lambda: LogisticRegression(penalty="l1", C=0.05, solver="liblinear", class_weight="balanced"),
          "gbm": lambda: GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)}
    for nm, ctor in mk.items():
        oof = np.full(len(yk), np.nan)
        for i, te in enumerate(folds):
            tr = np.concatenate([folds[j] for j in range(5) if j != i])
            if yk[tr].sum() < 5:
                continue
            oof[te] = ctor().fit(XK[tr], yk[tr]).predict_proba(XK[te])[:, 1]
        ok = np.isfinite(oof)
        thr = float(np.quantile(oof[ok], 0.85))
        mdl = ctor().fit(XK, yk)
        pt, pdk = mdl.predict_proba(XT)[:, 1], mdl.predict_proba(XD)[:, 1]
        rec = {"kesif_oof_auc": round(float(roc_auc_score(yk[ok], oof[ok])), 3),
               "test_auc": round(float(roc_auc_score(zt[label].values, pt)), 3),
               "duka_test_auc": round(float(roc_auc_score(zd[label].values, pdk)), 3)}
        per = {}
        for f in PRIM:
            ix = (zt.besleme == f).values
            if zt[label].values[ix].sum() >= 3:
                per[f] = {"auc": round(float(roc_auc_score(zt[label].values[ix], pt[ix])), 3), **veto_eval(zt[ix], pt[ix] >= thr)}
        rec["piyasa"] = per
        rec["HAVUZ_MT5"] = veto_eval(zt, pt >= thr)
        rec["DUKA_NDX"] = veto_eval(zd, pdk >= thr)
        rec["yon_tutan_piyasa"] = sum(1 for f in per if per[f]["veto_ort"] is not None and per[f]["veto_ort"] < per[f]["kalan_ort"])
        rec["hukum"] = verdict(rec)
        if nm.startswith("agac"):
            rec["agac"] = export_text(mdl, feature_names=FEATS, max_depth=3)
        if nm == "l1_lojistik":
            co = pd.Series(mdl.coef_[0], index=FEATS)
            rec["katsayilar"] = co[co != 0].sort_values(key=np.abs, ascending=False).head(15).round(3).to_dict()
        if nm == "gbm":
            rec["onem"] = pd.Series(mdl.feature_importances_, index=FEATS).sort_values(ascending=False).head(15).round(3).to_dict()
        out[nm] = rec
    return out


def main() -> None:
    res = {"veri": {"ozellik": len(FEATS), "yeni": len([f for f in FEATS if f in NEW]), "eski": len([f for f in FEATS if f in OLD]),
                    "kesif_islem": int((M.besleme.isin(PRIM) & (M.donem == "KESIF")).sum()), "kesif_kaybeden": int((M.besleme.isin(PRIM) & (M.donem == "KESIF") & (M.y == 1)).sum()),
                    "test_islem": int((M.besleme.isin(PRIM) & (M.donem == "TEST")).sum()), "test_kaybeden": int((M.besleme.isin(PRIM) & (M.donem == "TEST") & (M.y == 1)).sum())}}
    print(res["veri"], flush=True)
    for lab in ("y", "y2"):
        u = step_univariate(lab)
        res[f"tek_{lab}"] = u
        print(f"[{lab}] tek: eşik {u['aile_hatasi_esik_sapma']} geçen {u['esigi_gecen']} KEŞİF↔TEST AUC korelasyonu {u['kesif_test_auc_korelasyon']}", flush=True)
        df = pd.DataFrame(u["tablo"])
        top20 = df.head(20).ozellik.tolist()
        signs = {f: (1 if a > 0.5 else -1) for f, a in zip(df.ozellik, df.kesif_auc)}
        res[f"cift_{lab}"] = pair_scan(top20, signs, lab)
        res[f"model_{lab}"] = models(lab)
        (RES / "analiz.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    res["kume"] = step_cluster()
    (RES / "analiz.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print("bitti")


if __name__ == "__main__":
    main()
