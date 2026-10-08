"""SL ↔ TP kıyas motoru: her özellik, her kategori, her ikili — dönemler arası tutarlılıkla.

Dönem kurgusu: ``disc`` (keşif = odak penceresinden ÖNCEKİ işlemler) ve ``focus``
(son N gün). Aday önlemler YALNIZ keşifte seçilir, odakta sınanır — odakta seçip
odakta övmek (E12) yapılmaz. Kıyas birimi BAĞIMSIZ KARAR (E9): aynı karardan
bölünmüş bacakların yalnız ilki sayılır.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings as S
from .stats import auc_perm, bh_q, boot_mean_ci, wilson

LOSS, WIN = "SL", "TP"
FAMILY_PREFIX = {"pre_": "karar anı", "geo_": "geometri", "ctx_": "bağlam",
                 "e5_": "erken 5dk", "e15_": "erken 15dk", "path_": "yol (teşhis)"}
BINARY_FEATURES = [
    "pre_trend_align_1h", "pre_div_rsi_against", "pre_div_rsi_for", "pre_voldiv_against", "pre_voldiv_for",
    "pre_sl_beyond_struct", "pre_vix_favors", "path_went_green", "path_struct_break", "path_vol_shock_adv",
    "path_vol_shock_fav", "path_overnight", "path_us_open_cross", "ctx_prev_win", "ctx_prev_same_dir",
]
DECISION_TIME_PREFIXES = ("pre_", "geo_", "ctx_")
# Sonucu TANIM GEREĞİ içeren ölçüler — SL/TP ayrımı otomatik çıkar, kıyas tablosuna girmez
# (anatomi bölümünde betimlenir). geo_be_wr = 1/(1+RR) → geo_rr ile aynı bilgi.
TAUTOLOGICAL = {"path_mae_r", "path_mfe_r", "path_mfe_frac_tp", "path_went_green", "path_t_mfe_min",
                "path_t_mae_min", "path_exit_slip_r", "path_spike_stop", "path_dur_min", "geo_be_wr",
                "pre_stale_min"}
MIN_COVERAGE = 0.8               # etkileşimde yalnız işlemlerin ≥%80'inde tanımlı özellikler
CAND_MIN_N = 15                  # aday: keşifte SL ve TP gruplarının her biri en az
CAND_MAX_P = 0.10                # aday: keşif permütasyon p üst sınırı


def first_legs(t: pd.DataFrame) -> pd.DataFrame:
    return t.sort_values("entry_utc").drop_duplicates("decision_id", keep="first")


def family_of_feature(col: str) -> str:
    return next((v for k, v in FAMILY_PREFIX.items() if col.startswith(k)), "diğer")


def numeric_features(t: pd.DataFrame) -> list[str]:
    cols = []
    for c in t.columns:
        if c in TAUTOLOGICAL:
            continue
        if c.startswith(tuple(FAMILY_PREFIX)) and not c.endswith("_open") and pd.api.types.is_numeric_dtype(t[c]):
            if t[c].notna().sum() >= 2 * S.MIN_GROUP_N and t[c].nunique(dropna=True) > 1:
                cols.append(c)
    return cols


def survival_masked(t: pd.DataFrame) -> pd.DataFrame:
    """Erken özellikler yalnız o dakikada hâlâ açık işlemlerde anlamlı (hayatta-kalma)."""
    t = t.copy()
    for k in S.EARLY_MARKS_MIN:
        flag = f"e{k}_open"
        if flag in t:
            cols = [c for c in t.columns if c.startswith(f"e{k}_") and c != flag]
            t.loc[t[flag] != 1.0, cols] = np.nan
    return t


def _auc_cols(d: pd.DataFrame, col: str, perm: bool) -> tuple:
    L = d.loc[d["outcome"] == LOSS, col].to_numpy(float)
    W = d.loc[d["outcome"] == WIN, col].to_numpy(float)
    nL, nW = np.isfinite(L).sum(), np.isfinite(W).sum()
    if nL < S.MIN_GROUP_N or nW < S.MIN_GROUP_N:
        return np.nan, np.nan, nL, nW
    if perm:
        a, p = auc_perm(L, W)
        return a, p, nL, nW
    from .stats import auc
    return auc(L, W), np.nan, nL, nW


def feature_compare(t: pd.DataFrame) -> pd.DataFrame:
    """Her sayısal özellik: SL ve TP medyanı, AUC=P(SL değeri > TP değeri), p, q, dönem tutarlılığı."""
    d = survival_masked(first_legs(t))
    rows = []
    for col in numeric_features(d):
        a, p, nL, nW = _auc_cols(d, col, perm=True)
        if not np.isfinite(a):
            continue
        a_d, _, _, _ = _auc_cols(d[d["period"] == "disc"], col, perm=False)
        a_f, _, _, _ = _auc_cols(d[d["period"] == "focus"], col, perm=False)
        rows.append({"feature": col, "aile": family_of_feature(col), "n_sl": nL, "n_tp": nW,
                     "med_sl": d.loc[d["outcome"] == LOSS, col].median(),
                     "med_tp": d.loc[d["outcome"] == WIN, col].median(),
                     "auc": a, "p": p, "auc_disc": a_d, "auc_focus": a_f,
                     "registry": S.REGISTRY_HINTS.get(col, "")})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["q"] = np.nan
    for fam, idx in df.groupby("aile").groups.items():
        df.loc[idx, "q"] = bh_q(df.loc[idx, "p"].to_numpy())
    df["guc"] = (df["auc"] - 0.5).abs()
    same = np.sign(df["auc_disc"] - 0.5) == np.sign(df["auc_focus"] - 0.5)
    big = ((df["auc_disc"] - 0.5).abs() >= 0.05) & ((df["auc_focus"] - 0.5).abs() >= 0.05)
    df["tutarli"] = np.where(df["auc_disc"].isna() | df["auc_focus"].isna(), "—", np.where(same & big, "evet", "hayır"))
    return df.sort_values("guc", ascending=False).reset_index(drop=True)


def group_table(t: pd.DataFrame, by: str | list) -> pd.DataFrame:
    """Kategori kırılımı: n, karar, WR + Wilson, başabaş WR, ort/top R, net $."""
    rows = []
    for key, g in t.groupby(by, dropna=False):
        dec = g["decision_id"].nunique()
        k = int((g["net"] > 0).sum())
        lo, hi = wilson(k, len(g))
        rows.append({"grup": key if not isinstance(key, tuple) else " · ".join(map(str, key)),
                     "n": len(g), "karar": dec, "wr": k / len(g), "wr_lo": lo, "wr_hi": hi,
                     "basabas_wr": g["geo_be_wr"].mean(), "ort_r": g["r_exit"].mean(),
                     "top_r": g["r_exit"].sum(), "net_usd": g["net"].sum(),
                     "sl": int((g["outcome"] == LOSS).sum()), "tp": int((g["outcome"] == WIN).sum())})
    return pd.DataFrame(rows).sort_values("net_usd").reset_index(drop=True)


def binary_conditionals(t: pd.DataFrame) -> pd.DataFrame:
    """İkili olay var/yok → SL oranı, ort R, net $. Yol olayları teşhistir, kapı değil."""
    d = first_legs(t)
    d = d[d["outcome"].isin([LOSS, WIN])]
    rows = []
    for col in BINARY_FEATURES:
        if col not in d or d[col].notna().sum() < 2 * S.MIN_GROUP_N:
            continue
        for val, lab in ((1.0, "var"), (0.0, "yok")):
            g = d[d[col] == val]
            if len(g):
                rows.append({"olay": col, "durum": lab, "n": len(g), "sl_orani": (g["outcome"] == LOSS).mean(),
                             "ort_r": g["r_exit"].mean(), "net_usd": g["net"].sum(),
                             "aile": family_of_feature(col)})
    return pd.DataFrame(rows)


def outcome_mix(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby("outcome")
    return pd.DataFrame({"n": g.size(), "net_usd": g["net"].sum(), "ort_r": g["r_exit"].mean(),
                         "medyan_sure_dk": g["path_dur_min"].median()}).sort_values("n", ascending=False)


def period_summary(t: pd.DataFrame) -> dict:
    d = first_legs(t)
    lo, hi, p_pos = boot_mean_ci(d["r_exit"].to_numpy(float))
    wins = int((t["net"] > 0).sum())
    return {"n": len(t), "karar": int(t["decision_id"].nunique()), "net_usd": float(t["net"].sum()),
            "top_r": float(t["r_exit"].sum(skipna=True)), "ort_r": float(t["r_exit"].mean()),
            "ort_r_ci": (lo, hi), "p_ev_pos": p_pos, "wr": wins / len(t) if len(t) else np.nan,
            "wr_ci": wilson(wins, len(t)), "basabas_wr": float(t["geo_be_wr"].mean()),
            "tp": int((t["outcome"] == WIN).sum()), "sl": int((t["outcome"] == LOSS).sum())}


def veto_candidates(t: pd.DataFrame, fc: pd.DataFrame) -> pd.DataFrame:
    """Keşifte seçilen karar-anı özelliği × tertil eşik → odakta ne olurdu?

    Seçim: keşif AUC'sinden (|AUC−0,5| en büyük ``CANDIDATE_MAX``); eşik keşif tertili.
    Odak sonucu OOS-benzeridir AMA aynı veriye tekrar tekrar bakılırsa kirlenir.
    """
    d = first_legs(t)
    disc, focus = d[d["period"] == "disc"], d[d["period"] == "focus"]
    if fc.empty or len(disc) < 2 * CAND_MIN_N:
        return pd.DataFrame()
    pool = fc[fc["feature"].str.startswith(DECISION_TIME_PREFIXES) & fc["auc_disc"].notna()].copy()
    pool["guc_disc"] = (pool["auc_disc"] - 0.5).abs()
    rows, seen = [], []
    for _, f in pool.sort_values("guc_disc", ascending=False).iterrows():
        col, hi_bad = f["feature"], f["auc_disc"] > 0.5
        L = disc.loc[disc["outcome"] == LOSS, col].to_numpy(float)
        W = disc.loc[disc["outcome"] == WIN, col].to_numpy(float)
        if np.isfinite(L).sum() < CAND_MIN_N or np.isfinite(W).sum() < CAND_MIN_N or auc_perm(L, W)[1] > CAND_MAX_P:
            continue
        thr = _threshold(disc[col], hi_bad)
        mask = _blocked(disc[col], hi_bad, thr)
        if mask.sum() < CAND_MIN_N or any(mask.equals(m) for m in seen):
            continue                               # çok seyrek ya da başka adayla aynı işlemler
        seen.append(mask)
        for name, g in (("keşif", disc), ("odak", focus)):
            rows.append(_veto_eval(col, hi_bad, thr, name, g))
        if len(seen) >= S.CANDIDATE_MAX:
            break
    return pd.DataFrame(rows)


def _threshold(x: pd.Series, hi_bad: bool) -> float:
    if set(x.dropna().unique()) <= {0.0, 1.0}:
        return 1.0 if hi_bad else 0.0              # ikili özellik: değerin kendisi
    return float(x.quantile(2 / 3 if hi_bad else 1 / 3))


def _blocked(x: pd.Series, hi_bad: bool, thr: float) -> pd.Series:
    return ((x >= thr) if hi_bad else (x <= thr)).fillna(False)


def _veto_eval(col: str, hi_bad: bool, thr: float, period: str, g: pd.DataFrame) -> dict:
    b = g[_blocked(g[col], hi_bad, thr)]
    mean_r = g["r_exit"].mean()
    saved_r = -b["r_exit"].sum()
    return {"ozellik": col, "kural": f"{col} {'≥' if hi_bad else '≤'} {thr:.3g} → açma", "donem": period,
            "n_donem": len(g), "engellenen": len(b), "engellenen_tp": int((b["outcome"] == WIN).sum()),
            "engellenen_sl": int((b["outcome"] == LOSS).sum()), "kurtarilan_r": saved_r,
            "rastgele_beklenen_r": -len(b) * mean_r if np.isfinite(mean_r) else np.nan,
            "kurtarilan_usd": -b["net"].sum(), "registry": S.REGISTRY_HINTS.get(col, "")}


def interactions(t: pd.DataFrame, fc: pd.DataFrame) -> pd.DataFrame:
    """En güçlü karar-anı özelliklerinin ikili medyan bölmeleri (keşif amaçlı)."""
    d = first_legs(t)
    d = d[d["outcome"].isin([LOSS, WIN])]
    cover = [f for f in fc["feature"] if f.startswith(DECISION_TIME_PREFIXES) and d[f].notna().mean() >= MIN_COVERAGE]
    top = cover[:S.INTERACTION_TOP]
    base = (d["outcome"] == LOSS).mean()
    rows = []
    for i, a in enumerate(top):
        for b in top[i + 1:]:
            ma, mb = d[a].median(), d[b].median()
            for sa, la in ((d[a] > ma, "yüksek"), (d[a] <= ma, "düşük")):
                for sb_, lb in ((d[b] > mb, "yüksek"), (d[b] <= mb, "düşük")):
                    g = d[sa & sb_]
                    if len(g) >= S.MIN_GROUP_N:
                        rows.append({"hucre": f"{a} {la} · {b} {lb}", "n": len(g),
                                     "sl_orani": (g["outcome"] == LOSS).mean(), "taban_sl": base,
                                     "ort_r": g["r_exit"].mean()})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["fark_pp"] = (out["sl_orani"] - out["taban_sl"]) * 100
    return out.reindex(out["fark_pp"].abs().sort_values(ascending=False).index).head(12)


def anatomy(t: pd.DataFrame) -> dict:
    """SL ve TP mekanizma payları (sayım + pay)."""
    sl, tp = t[t["outcome"] == LOSS], t[t["outcome"] == WIN]

    def share(mask: pd.Series) -> tuple[int, float]:
        m = mask.fillna(False)
        return int(m.sum()), float(m.mean()) if len(m) else np.nan

    a = {"sl_n": len(sl), "tp_n": len(tp)}
    if len(sl):
        a.update({
            "sl_yon_dogru": share(sl["sl_verdict"] == "YON_DOGRU"),
            "sl_yon_yanlis": share(sl["sl_verdict"] == "YON_YANLIS"),
            "sl_kararsiz": share(sl["sl_verdict"] == "KARARSIZ"),
            "sl_hizli": share(sl["path_dur_min"] <= S.FAST_SL_MIN),
            "sl_hic_calismadi": share(sl["path_mfe_r"] < S.NEVER_WORKED_MFE_R),
            "sl_once_yesil": share(sl["path_mfe_r"] >= S.WENT_GREEN_R),
            "sl_neredeyse_tp": share(sl["path_mfe_frac_tp"] >= S.NEAR_TP_FRAC),
            "sl_yapi_kirildi": share(sl["path_struct_break"] == 1.0),
            "sl_ters_hacim_soku": share(sl["path_vol_shock_adv"] == 1.0),
            "sl_gece": share(sl["path_overnight"] == 1.0),
            "sl_igne": share(sl["path_spike_stop"] == 1.0),
            "sl_kayma": share(sl.get("path_exit_slip_r", pd.Series(dtype=float)) < -S.SLIP_R),
            "sl_hacim_sondu": share(sl["path_vol_last_vs_first"] < S.VOL_FADE_RATIO),
            "sl_medyan_sure": float(sl["path_dur_min"].median()),
            "sl_medyan_mfe": float(sl["path_mfe_r"].median()),
            "sl_medyan_needed_sl": float(sl.get("post240_needed_sl_r", pd.Series(dtype=float)).median()),
        })
    if len(tp):
        a.update({
            "tp_temiz": share(tp["path_mae_r"] > -S.CLEAN_TP_MAE_R),
            "tp_aci_cektiren": share(tp["path_mae_r"] <= -S.PAINFUL_TP_MAE_R),
            "tp_erken": share(tp.get("post240_run_beyond_tp_r", pd.Series(dtype=float)) >= S.EARLY_TP_RUN_R),
            "tp_sonra_sl_vurdu": share(tp.get("post240_hit_sl0", pd.Series(dtype=float)) == 1.0),
            "tp_hacim_sondu": share(tp["path_vol_last_vs_first"] < S.VOL_FADE_RATIO),
            "tp_medyan_sure": float(tp["path_dur_min"].median()),
            "tp_medyan_mae": float(tp["path_mae_r"].median()),
        })
    return a


def tag_frequency(t: pd.DataFrame) -> pd.DataFrame:
    """Her etiket SL'lerde mi TP'lerde mi daha sık? Bir bayrak TP'lerde de aynı sıklıkta
    varsa "SL nedeni" DEĞİLDİR — anlatıyı istatistikle sınar."""
    d = first_legs(t)
    d = d[d["outcome"].isin([LOSS, WIN])]
    nL, nW = int((d["outcome"] == LOSS).sum()), int((d["outcome"] == WIN).sum())
    if not nL or not nW:
        return pd.DataFrame()
    base = nL / (nL + nW)
    rows = []
    for col, phase in (("etiket_giris", "giriş (karar anı)"), ("etiket_yol", "yol (teşhis)")):
        tags = sorted({x for s in d[col].fillna("") for x in s.split() if x})
        for tag in tags:
            has = d[col].fillna("").str.split().map(lambda xs: tag in xs)
            g = d[has]
            if len(g) < 5:
                continue
            rows.append({"etiket": tag, "evre": phase, "SL'lerde": (g["outcome"] == LOSS).sum() / nL,
                         "TP'lerde": (g["outcome"] == WIN).sum() / nW, "n": len(g),
                         "SL oranı (varken)": (g["outcome"] == LOSS).mean(), "taban SL oranı": base,
                         "ort R (varken)": g["r_exit"].mean()})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["fark_pp"] = (out["SL oranı (varken)"] - base) * 100
    return out.sort_values(["evre", "fark_pp"], ascending=[True, False]).reset_index(drop=True)


def verdict_table(t: pd.DataFrame) -> pd.DataFrame:
    """Tam SL'ler: strateji × sembol-yön başına çıkış-sonrası hüküm dağılımı."""
    sl = t[(t["outcome"] == LOSS) & (t["sl_verdict"] != "")]
    if sl.empty:
        return pd.DataFrame()
    ct = pd.crosstab(sl["family"] + " · " + sl["side"], sl["sl_verdict"])
    ct["toplam"] = ct.sum(axis=1)
    return ct.sort_values("toplam", ascending=False).reset_index().rename(columns={"row_0": "grup"})
