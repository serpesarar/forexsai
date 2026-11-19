"""tur4.py — PROTOCOL EK-1: büyük eğitim kümesi (tüm K1+XP KEŞİF + Duka), sürekli hedef, ayarlı L1, yol şekli kNN, çapraz varlık.
python tur4.py kur   # ek özellikler → results/tur4_ozellik.parquet
python tur4.py kos   # modeller → results/tur4.json
"""
from __future__ import annotations

import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression

import motor as Mo
import ortak as K

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES = HERE / "results"
FEEDS = K.MT5 + ["DUKA_NDX"]
CROSS = ["GER40", "XAUUSD", "SpotCrude"]


def all_trades() -> pd.DataFrame:
    I = pd.read_parquet(ROOT / "research/xp_gelistir_20261119/results/islemler.parquet")
    I = I[I.d <= Mo.CUT].copy()
    I["paket"] = ~I.opex_k.isin([0, 1, 2])
    return I[["besleme", "d", "net", "donem", "paket"]].reset_index(drop=True)


def session_path(b30: pd.DataFrame) -> pd.DataFrame:
    """Gün başına 09:30–16:00 13 yarım saatlik log getiri (açılıştan itibaren)."""
    import ozellik as O
    x = O.G._local(b30, Mo.NY)
    z = b30.assign(day=pd.to_datetime(x.day.values), mn=x.mn.values)
    z = z[(z.mn >= 570) & (z.mn < 960)]
    piv = z.pivot_table(index="day", columns="mn", values="c", aggfunc="last")
    op = z.groupby("day").o.first()
    cols = list(range(570, 960, 30))
    piv = piv.reindex(columns=cols)
    lv = np.log(piv.values)
    prev = np.column_stack([np.log(op.reindex(piv.index).values), lv[:, :-1]])
    return pd.DataFrame((lv - prev) * 1e4, index=piv.index, columns=[f"p{i}" for i in range(13)])


def cross_feats() -> pd.DataFrame:
    sys.path.insert(0, str(ROOT / "research/son_rapor_20261118/src"))
    import rapor as R
    out = []
    for s in CROSS:
        b = R.KD.mt5_m30(s)
        b["t"] = (b.t // 1800) * 1800
        x = R.G._local(b, Mo.NY)
        z = b.assign(day=pd.to_datetime(x.day.values), mn=x.mn.values)
        c16 = z[z.mn == 930].groupby("day").c.last()          # 15:30 mumu 16:00'da kapanır
        o930 = z[z.mn == 570].groupby("day").o.first()
        o15 = z[z.mn == 900].groupby("day").o.first()
        df = pd.DataFrame({f"C_{s}_gun": (c16 / c16.shift(1) - 1) * 1e4, f"C_{s}_seans": (c16 / o930 - 1) * 1e4,
                           f"C_{s}_sonsaat": (c16 / o15 - 1) * 1e4})
        out.append(df)
    return pd.concat(out, axis=1)


def _extra_job(name: str) -> pd.DataFrame:
    A = all_trades()
    A = A[(A.besleme == name) & ~A.paket]
    b, hv = Mo.load_feed(name)
    daily = Mo.rth_daily(b)
    rows = [{"besleme": name, "d": t.d, **Mo.feed_trade_feats(b, daily, pd.Timestamp(t.d), hv)} for _, t in A.iterrows()]
    sp = session_path(b)
    pth = []
    for d in all_trades().query("besleme == @name").d:
        d = pd.Timestamp(d)
        if d in sp.index:
            i = sp.index.get_loc(d)
            prev = sp.iloc[i - 1].values if i > 0 else np.full(13, np.nan)
            atr = daily.loc[:d].pipe(lambda q: (q.h - q.l).iloc[-20:].mean() / q.c.iloc[-1] * 1e4 if len(q) >= 20 else np.nan)
            v = np.r_[prev, sp.iloc[i].values] / atr
            pth.append({"besleme": name, "d": d, **{f"Y_{j}": v[j] for j in range(26)}})
    return pd.concat([pd.DataFrame(rows), pd.DataFrame(pth)], ignore_index=True) if rows else pd.DataFrame(pth)


def kur() -> None:
    with ProcessPoolExecutor(max_workers=5) as ex:
        parts = list(ex.map(_extra_job, FEEDS))
    E = pd.concat(parts, ignore_index=True)
    feat_rows = E[E.filter(like="m30_").notna().any(axis=1)].drop(columns=[c for c in E.columns if c.startswith("Y_")])
    path_rows = E[E.filter(like="Y_").notna().any(axis=1)][["besleme", "d"] + [f"Y_{j}" for j in range(26)]]
    P = pd.read_parquet(RES / "paket_ozellik.parquet").drop(columns=["net", "donem", "cikis", "tutus_gun"])
    F = pd.concat([P, feat_rows], ignore_index=True).drop_duplicates(["besleme", "d"])
    A = all_trades().merge(F, on=["besleme", "d"], how="left").merge(path_rows, on=["besleme", "d"], how="left")
    A = A.merge(cross_feats(), left_on="d", right_index=True, how="left")
    XK = pd.read_parquet(ROOT / "research/xp_kaybeden_20261119/results/ozellikler_kanal.parquet")
    old = [c for c in XK.columns if c not in ("net", "donem", "cikis", "tutus_gun", "giris", "mae", "mfe", "mae_saat", "y", "y2", "z40",
                                              "z80", "z120", "z200", "K1", "ay_blok") and not c.startswith(("c0", "c1", "c2", "g"))]
    old = [c for c in old if c not in ("besleme", "d") and pd.api.types.is_numeric_dtype(XK[c])]
    A = A.merge(XK[["besleme", "d"] + old].rename(columns={c: "XK_" + c for c in old}), on=["besleme", "d"], how="left")
    A.to_parquet(RES / "tur4_ozellik.parquet")
    print("tur4 tablo", A.shape, "paket", int(A.paket.sum()), "yol dolu %", round(float(A.Y_0.notna().mean() * 100), 1),
          "çapraz dolu %", round(float(A.C_GER40_gun.notna().mean() * 100), 1))


# ---------------- modeller ----------------
def knn_score(A: pd.DataFrame, k: int = 25) -> np.ndarray:
    Y = A[[f"Y_{j}" for j in range(26)]].astype(float)
    ok = Y.notna().all(axis=1).values
    Yv = Y.values
    ref = np.flatnonzero(ok & (A.donem == "KESIF").values)
    out = np.full(len(A), np.nan)
    dates = pd.to_datetime(A.d).values
    for i in np.flatnonzero(ok):
        cand = ref[dates[ref] != dates[i]]                       # aynı gün (öbür beslemeler) hariç
        dd = np.sqrt(((Yv[cand] - Yv[i]) ** 2).sum(1))
        out[i] = A.net.values[cand[np.argsort(dd)[:k]]].mean()
    return out


def kos() -> None:
    A = pd.read_parquet(RES / "tur4_ozellik.parquet")
    A["y"] = (A.net < 0).astype(int)
    A["Y_knn"] = knn_score(A)
    pre = ("m30_", "h1_", "h2_", "h4_", "D_", "W_", "H_", "XK_", "C_", "Y_")
    tr_mask = (A.donem == "KESIF").values
    feats = [c for c in A.columns if c.startswith(pre) and A[tr_mask][c].notna().mean() > 0.7 and A[tr_mask][c].nunique() > 2]
    # ölçekleme: her besleme kendi KEŞİF özellik dağılımıyla
    X = np.zeros((len(A), len(feats)))
    for f in FEEDS:
        ix = (A.besleme == f).values
        X[ix] = K.standardize(A[ix], A[ix & tr_mask], feats)
    lo, hi = np.quantile(A.net[tr_mask], [0.025, 0.975])
    yk, nk = A.y.values[tr_mask], A.net.clip(lo, hi).values[tr_mask]
    XK_, dk = X[tr_mask], A.d[tr_mask]
    tm = ((A.donem == "TEST") & A.paket).values
    ZT, XT = A[tm], X[tm]
    res = {"veri": {"egitim": int(tr_mask.sum()), "egitim_kaybeden": int(yk.sum()), "test_paket": int(tm.sum()), "ozellik": len(feats)}}
    print(res["veri"], flush=True)
    # tek başına yeni aileler (bilgi): kNN ve çapraz varlık, TEST paket AUC
    tek = {}
    for c in ["Y_knn"] + [c for c in feats if c.startswith("C_")]:
        z = ZT[ZT[c].notna()]
        kp = A[tr_mask & A[c].notna().values]
        tek[c] = {"kesif_auc": K.safe_auc(kp.y.values, kp[c].values), "test_auc": K.safe_auc(z.y.values, z[c].values)}
    res["yeni_aile_tek"] = tek
    print("yeni aileler:", tek, flush=True)
    # L1: C seçimi
    best, cs = None, {}
    for C in (0.005, 0.01, 0.02, 0.05, 0.1, 0.3, 1.0):
        oof = K.oof_scores(lambda: LogisticRegression(penalty="l1", C=C, solver="liblinear", class_weight="balanced"), XK_, yk, dk)
        ok = np.isfinite(oof)
        cs[C] = K.safe_auc(yk[ok], oof[ok]) or 0
        if best is None or cs[C] > cs[best]:
            best = C
    res["l1_C_oof"] = cs
    clf = {"l1_lojistik": lambda: LogisticRegression(penalty="l1", C=best, solver="liblinear", class_weight="balanced"),
           "gbm": lambda: GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0),
           "lgbm": lambda: lgb.LGBMClassifier(n_estimators=300, learning_rate=0.02, num_leaves=4, min_child_samples=20, subsample=0.7,
                                              subsample_freq=1, colsample_bytree=0.3, reg_lambda=5.0, random_state=0, verbose=-1)}
    reg = {"gbm_reg": lambda: GradientBoostingRegressor(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, loss="huber", random_state=0),
           "lgbm_reg": lambda: lgb.LGBMRegressor(n_estimators=300, learning_rate=0.02, num_leaves=4, min_child_samples=20, subsample=0.7,
                                                 subsample_freq=1, colsample_bytree=0.3, reg_lambda=5.0, random_state=0, verbose=-1)}
    for nm, ctor in clf.items():
        oof = K.oof_scores(ctor, XK_, yk, dk)
        ok = np.isfinite(oof)
        thr = float(np.quantile(oof[ok], 0.85))
        m = ctor().fit(XK_, yk)
        p = m.predict_proba(XT)[:, 1]
        res[nm] = {"kesif_oof_auc": K.safe_auc(yk[ok], oof[ok]), "TEST": K.blind_report(ZT, p, thr)}
        if hasattr(m, "feature_importances_"):
            res[nm]["onem"] = pd.Series(m.feature_importances_, index=feats).sort_values(ascending=False).head(15).round(4).to_dict()
        else:
            co = pd.Series(m.coef_[0], index=feats)
            res[nm]["katsayi"] = co[co != 0].sort_values(key=np.abs, ascending=False).head(15).round(3).to_dict()
    for nm, ctor in reg.items():
        folds = K.time_folds(dk)
        oof = np.full(len(nk), np.nan)
        for i, te in enumerate(folds):
            tr = np.concatenate([folds[j] for j in range(len(folds)) if j != i])
            oof[te] = ctor().fit(XK_[tr], nk[tr]).predict(XK_[te])
        thr = float(np.quantile(oof, 0.15))
        m = ctor().fit(XK_, nk)
        p = -m.predict(XT)                       # yüksek puan = kötü beklenti
        res[nm] = {"kesif_oof_auc": K.safe_auc(yk, -oof), "kesif_oof_spearman": round(float(pd.Series(oof).corr(pd.Series(nk), method="spearman")), 3),
                   "TEST": K.blind_report(ZT, p, -thr),
                   "onem": pd.Series(m.feature_importances_, index=feats).sort_values(ascending=False).head(15).round(4).to_dict()}
    for nm in list(clf) + list(reg):
        t = res[nm]["TEST"]
        print(f"{nm}: KEŞİF OOF AUC {res[nm]['kesif_oof_auc']} | TEST MT5 {t['MT5_HAVUZ']['auc']} Duka {t['DUKA_NDX']['auc']} "
              f">0,55 {t['auc_ust_055']}/4 | veto {t['MT5_HAVUZ']['veto_ort']} vs {t['MT5_HAVUZ']['kalan_ort']} kâr× {t['MT5_HAVUZ']['kar_x']} "
              f"zarar× {t['MT5_HAVUZ']['zarar_x']} P {t['MT5_HAVUZ']['P_veto_ort_eksi']} yön {t['yon_tutan']}/4 → {t['hukum']}", flush=True)
    print("L1 C OOF:", cs, "seçilen", best)
    (RES / "tur4.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    kur() if sys.argv[1] == "kur" else kos()
