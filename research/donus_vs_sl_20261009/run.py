"""Ön-kayıt: PROTOCOL.md. python3 research/donus_vs_sl_20261009/run.py [--esik 0.5]

Karar anı D = barın aleyhte ucu ilk kez −eşik·R'ye değdiği 1m bar. D kapanışında bilinenlerle A (sonra TP) /
B (SL) ayrımı. Çıktı: results/olaylar_<eşik>.csv, profil_<eşik>.csv, grafikler.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "limit_kilit_20261007"))
from scripts.islem_otopsi.features import vol_dir  # noqa: E402
from scripts.islem_otopsi.stats import auc, auc_perm, bh_q, boot_mean_ci  # noqa: E402

PROFILE = (-20, 10)
MIN_LEG = 2


def _load():
    spec = importlib.util.spec_from_file_location("lk_run", ROOT / "research" / "limit_kilit_20261007" / "run.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["lk_run"] = m
    spec.loader.exec_module(m)
    return m.load()


def _fav_adv(c, j0: int, j1: int) -> tuple[np.ndarray, np.ndarray]:
    a, s = c.sb.a, c.s
    hi, lo = a["high"][j0:j1], a["low"][j0:j1]
    adj = 0.0 if s > 0 else c.spread
    return s * ((hi if s > 0 else lo) + adj - c.entry) / c.risk, s * ((lo if s > 0 else hi) + adj - c.entry) / c.risk


def _mean(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    return float(x.mean()) if x.size else np.nan


def event(c, r, thr: float) -> tuple[dict | None, str]:
    """(özellikler, dışlama sebebi)."""
    if c.i_exit <= c.i_in0 + 1:
        return None, "giriş dakikasında çıktı"
    fav, adv = _fav_adv(c, c.i_in0, c.i_exit)        # çıkış barı hariç
    hit = np.flatnonzero(adv <= -thr)
    if not hit.size:
        return None, "çıkıştan önce eşiğe değmedi (aynı dakikada SL ya da hiç)"
    k = int(hit[0])
    D = c.i_in0 + k
    if D < 15:
        return None, "geçmiş bar yok"
    a, s, rr = c.sb.a, c.s, c.reward / c.risk
    k_mfe = int(np.argmax(fav[:k + 1]))
    i_mfe = c.i_in0 + k_mfe
    cl, op, hi, lo, v, vs = (a[x] for x in ("close", "open", "high", "low", "volume", "vol_seas"))
    body = s * (cl - op)
    rng = np.maximum(hi - lo, 1e-12)
    atr1 = a["atr"][D]
    f = {"pid": r["pid"], "ts": c.sb.m1.index[D], "side": r["side"], "family": r["family"], "half": None,
         "sonuc": r["outcome"], "R_sonuc": r["r_exit"], "R_D": float(c.r(cl[D])), "rr": rr}
    f.update(_volume(v, vs, body, c.i_pre, c.i_in0, i_mfe, D))
    f.update({
        "once_tp_kesri": float(fav[:k + 1].max() / rr),
        "dk_giris_D": float(k + 1), "dk_enIyi_D": float(k - k_mfe),
        "dusus_hizi_R_dk": float((fav[k_mfe] - adv[k]) / max(1, k - k_mfe)),
        "aleyhte_bar_10": float((body[D - 9:D + 1] < 0).sum()),
        "en_buyuk_aleyhte_govde_atr": float(np.max(np.maximum(-body[D - 9:D + 1], 0)) / atr1),
        "alt_fitil_3": _wick(a, s, D),
        "D_kapanis_konumu": float(((cl[D] - lo[D]) if s > 0 else (hi[D] - cl[D])) / rng[D]),
        "atr_genisleme": float(atr1 / a["atr"][c.i_pre]),
        "sl_mesafe_atr": float(s * (cl[D] - c.sl0) / atr1),
        "yapi_kirildi": float(s * (cl[D] - _struct(a, s, c.i_pre)) < 0),
        "rsi1_yon": float(a["rsi"][D] if s > 0 else 100 - a["rsi"][D]),
        "ema20_1m_atr": float(s * (cl[D] - a["ema20"][D]) / atr1),
    })
    t_close = c.sb.m1.index[D] + pd.Timedelta(minutes=1)
    j5 = c.sb.last_closed(5, t_close)
    t5 = c.sb.ta[5]
    f["rsi5_yon"] = float(t5["rsi"][j5] if s > 0 else 100 - t5["rsi"][j5])
    f["5m_ema20_alti"] = float(s * (t5["close"][j5] - t5["ema20"][j5]) < 0)
    f["_prof_v"] = v[D + PROFILE[0]:D + PROFILE[1] + 1].astype(float)
    f["_prof_vs"] = vs[D + PROFILE[0]:D + PROFILE[1] + 1].astype(float)
    return f, ""


def _volume(v, vs, body, i_pre, i_in0, i_mfe, D) -> dict:
    fav_leg, adv_leg = slice(i_in0, i_mfe + 1), slice(i_mfe + 1, D + 1)
    y = v[D - 9:D + 1].astype(float)
    slope = np.polyfit(np.arange(10), y, 1)[0] / y.mean() * 10 if y.mean() > 0 else np.nan
    ok = (i_mfe + 1 - i_in0) >= MIN_LEG and (D - i_mfe) >= MIN_LEG
    return {
        "hacim_giris_oncesi60": _mean(v[i_pre - 59:i_pre + 1].astype(float)),
        "hacim_son5": _mean(v[D - 4:D + 1].astype(float)),
        "hacim_onceki10": _mean(v[D - 14:D - 4].astype(float)),
        "hacim_son5_onceki10": _mean(v[D - 4:D + 1].astype(float)) / max(_mean(v[D - 14:D - 4].astype(float)), 1e-9),
        "hacim_D": float(v[D]),
        "hacim_D_saatine_gore": float(vs[D]),
        "hacim_son5_saatine_gore": _mean(vs[D - 4:D + 1]),
        "hacim_egim10": float(slope),
        "hacim_max10_saatine_gore": float(np.nanmax(vs[D - 9:D + 1])),
        "aleyhte_bacak_lehte_bacak_hacim": (_mean(v[adv_leg].astype(float)) / _mean(v[fav_leg].astype(float))) if ok else np.nan,
        "aleyhte_bacak_hacim_yonu": vol_dir(vs[adv_leg], body[adv_leg]) if ok else np.nan,
    }


def _wick(a, s, D) -> float:
    o, c, h, l = (a[x][D - 2:D + 1] for x in ("open", "close", "high", "low"))
    rng = np.maximum(h - l, 1e-12)
    w = (np.minimum(o, c) - l) if s > 0 else (h - np.maximum(o, c))
    return float(np.mean(w / rng))


def _struct(a, s, i_pre) -> float:
    w = slice(i_pre - 29, i_pre + 1)
    return float(a["low"][w].min() if s > 0 else a["high"][w].max())


# ── değerlendirme ────────────────────────────────────────────────────────────

def feat_cols(d: pd.DataFrame) -> list[str]:
    skip = {"pid", "ts", "side", "family", "half", "sonuc", "R_sonuc", "R_D", "rr", "B"}
    return [c for c in d.columns if c not in skip and not c.startswith("_") and d[c].notna().mean() > 0.7]


def compare(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in feat_cols(d):
        A, B = d.loc[d.B == 0, col].to_numpy(float), d.loc[d.B == 1, col].to_numpy(float)
        a_all, p = auc_perm(B, A)
        h = [auc(g.loc[g.B == 1, col].to_numpy(float), g.loc[g.B == 0, col].to_numpy(float)) for _, g in d.groupby("half")]
        rows.append({"ozellik": col, "A_dondu_TP_medyan": np.nanmedian(A), "B_SL_medyan": np.nanmedian(B),
                     "AUC(B>A)": a_all, "p": p, "AUC_H1": h[0], "AUC_H2": h[1]})
    out = pd.DataFrame(rows)
    out["q"] = bh_q(out["p"].to_numpy())
    out["tutarli"] = np.where(np.sign(out.AUC_H1 - 0.5) == np.sign(out.AUC_H2 - 0.5), "evet", "hayır")
    out["guc"] = (out["AUC(B>A)"] - 0.5).abs()
    return out.sort_values("guc", ascending=False).drop(columns="guc")


def _standardize(tr: pd.DataFrame, te: pd.DataFrame, cols: list[str]):
    med, sd = tr[cols].median(), tr[cols].std().replace(0, 1)
    return ((tr[cols].fillna(med) - med) / sd).to_numpy(float), ((te[cols].fillna(med) - med) / sd).to_numpy(float)


def logit_fit(X: np.ndarray, y: np.ndarray, lam: float = 1.0, it: int = 2000, lr: float = 0.1) -> np.ndarray:
    Xb = np.c_[np.ones(len(X)), X]
    w = np.zeros(Xb.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-Xb @ w))
        g = Xb.T @ (p - y) / len(y) + lam * np.r_[0, w[1:]] / len(y)
        w -= lr * g
    return w


def logit_pred(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.c_[np.ones(len(X)), X] @ w))


def multivariate(d: pd.DataFrame, rng: np.random.Generator) -> list[str]:
    cols = feat_cols(d)
    lines = []
    for a_lab, b_lab in (("H1", "H2"), ("H2", "H1")):
        tr, te = d[d.half == a_lab], d[d.half == b_lab]
        Xtr, Xte = _standardize(tr, te, cols)
        w = logit_fit(Xtr, tr.B.to_numpy(float))
        pr = logit_pred(w, Xte)
        a_te = auc(pr[te.B.to_numpy() == 1], pr[te.B.to_numpy() == 0])
        null = []
        for _ in range(200):
            ws = logit_fit(Xtr, rng.permutation(tr.B.to_numpy(float)), it=400)
            ps = logit_pred(ws, Xte)
            null.append(auc(ps[te.B.to_numpy() == 1], ps[te.B.to_numpy() == 0]))
        null = np.array(null)
        # karar: eğitimde net R'yi en çok artıran olasılık eşiği → sınamada uygula
        p_tr = logit_pred(w, Xtr)
        thr = max(np.quantile(p_tr, q) for q in (0.5,)) if False else _best_thr(p_tr, tr)
        flag = pr >= thr
        net = float((te.R_D - te.R_sonuc)[flag].sum())
        lines.append(f"  {a_lab}'de eğit → {b_lab}'de sına: AUC {a_te:.3f} (plasebo medyan {np.median(null):.3f}, %95 üst "
                     f"{np.quantile(null, 0.95):.3f}) · kural 'P(SL) ≥ {thr:.2f} ise D'de çık': {int(flag.sum())} işlem, "
                     f"net {net:+.2f}R")
    return lines


def _best_thr(p: np.ndarray, d: pd.DataFrame) -> float:
    gain = (d.R_D - d.R_sonuc).to_numpy(float)
    cands = np.quantile(p, np.linspace(0.3, 0.95, 14))
    return float(max(cands, key=lambda t: gain[p >= t].sum()))


def single_rules(d: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    """Her yarıda seç → diğerinde sına: tek özellik × tertil eşik."""
    rows = []
    for a_lab, b_lab in (("H1", "H2"), ("H2", "H1")):
        tr, te = d[d.half == a_lab], d[d.half == b_lab]
        best = None
        for col in comp.ozellik:
            x = tr[col]
            for q in (1 / 3, 2 / 3):
                thr = x.quantile(q)
                for op in (">=", "<="):
                    m = (x >= thr) if op == ">=" else (x <= thr)
                    g = float((tr.R_D - tr.R_sonuc)[m.fillna(False)].sum())
                    if m.sum() >= 10 and (best is None or g > best[0]):
                        best = (g, col, op, thr)
        g, col, op, thr = best
        m = (te[col] >= thr) if op == ">=" else (te[col] <= thr)
        rows.append({"seçim": a_lab, "kural": f"{col} {op} {thr:.3g} → D'de çık", "seçimde_net_R": round(g, 2),
                     "sınama": b_lab, "sınamada_işlem": int(m.fillna(False).sum()),
                     "sınamada_net_R": round(float((te.R_D - te.R_sonuc)[m.fillna(False)].sum()), 2)})
    return pd.DataFrame(rows)


def profile(d: pd.DataFrame, key: str) -> pd.DataFrame:
    xs = np.arange(PROFILE[0], PROFILE[1] + 1)
    out = {}
    for lab, g in (("A_dondu_TP", d[d.B == 0]), ("B_SL", d[d.B == 1])):
        arr = np.vstack([p for p in g[key] if len(p) == len(xs)])
        out[f"{lab}_medyan"] = np.nanmedian(arr, axis=0)
        out[f"{lab}_n"] = np.isfinite(arr).sum(axis=0)
    return pd.DataFrame(out, index=xs)


def chart(prof: pd.DataFrame, path: Path, title: str, ylab: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=130)
    fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
    ax.plot(prof.index, prof["A_dondu_TP_medyan"], color="#2a78d6", lw=2, label=f"A: döndü → TP (n={prof['A_dondu_TP_n'].max()})")
    ax.plot(prof.index, prof["B_SL_medyan"], color="#eb6834", lw=2, label=f"B: SL'ye gitti (n={prof['B_SL_n'].max()})")
    ax.axvline(0, color="#52514e", lw=1, ls="--")
    ax.axvspan(0.5, prof.index.max(), color="#e4e3df", alpha=0.5)
    ax.annotate("karar anı D (−0,5R)", (0, ax.get_ylim()[1]), xytext=(4, -12), textcoords="offset points", fontsize=8)
    ax.annotate("sonrası: karar anında BİLİNMEZ", (1, ax.get_ylim()[0]), xytext=(4, 4), textcoords="offset points",
                fontsize=7, color="#52514e")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(True, color="#e4e3df", lw=0.6)
    ax.set_xlabel("karar anına göre dakika", fontsize=9); ax.set_ylabel(ylab, fontsize=9)
    ax.set_title(title, fontsize=10, loc="left"); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--esik", type=float, default=0.5)
    a = ap.parse_args()
    out = HERE / "results"; out.mkdir(exist_ok=True)
    items = _load()
    rows, excl = [], {}
    for x in items:
        if x["r"]["outcome"] not in ("TP", "SL"):
            continue
        f, why = event(x["c"], x["r"], a.esik)
        if f is None:
            excl[why] = excl.get(why, 0) + 1
            continue
        f["half"] = x["half"]
        rows.append(f)
    d = pd.DataFrame(rows)
    d["B"] = (d.sonuc == "SL").astype(int)
    tag = f"{a.esik:g}"
    d.drop(columns=["_prof_v", "_prof_vs"]).to_csv(out / f"olaylar_{tag}.csv", index=False)
    pd.set_option("display.width", 230)
    print(f"Eşik −{a.esik}R | olay {len(d)}: A (döndü→TP) {int((d.B == 0).sum())}, B (SL) {int(d.B.sum())} | dışlanan {excl}")
    print(f"Taban P(TP | eşiğe geldi) = %{100 * (d.B == 0).mean():.0f} · 'her zaman D'de çık' net "
          f"{(d.R_D - d.R_sonuc).sum():+.1f}R (işlem başı {(d.R_D - d.R_sonuc).mean():+.3f})")
    comp = compare(d)
    comp.to_csv(out / f"karsilastirma_{tag}.csv", index=False)
    print("\n== Özellik karşılaştırması (AUC = rastgele bir B'nin değerinin A'dan büyük olma olasılığı; 0,5 = ayrım yok)")
    print(comp.round(3).to_string(index=False))
    print("\n== Tek özellikli kural: bir yarıda seç → diğerinde sına")
    print(single_rules(d, comp).to_string(index=False))
    print("\n== Çok değişkenli (lojistik, tüm özellikler)")
    print("\n".join(multivariate(d, np.random.default_rng(7))))
    for key, ylab, nm in (("_prof_v", "ham tick hacmi (medyan)", "ham"), ("_prof_vs", "hacim / saatine göre normal", "mevsimsel")):
        prof = profile(d, key)
        prof.round(1).to_csv(out / f"profil_{nm}_{tag}.csv")
        chart(prof, out / f"profil_{nm}_{tag}.png", f"Karar anı çevresinde dakika dakika hacim ({nm}) — A vs B", ylab)
    print("\n== Ham hacim profili (medyan, dakika): D−10 … D+3")
    print(profile(d, "_prof_v").loc[-10:3].round(0).T.to_string())
    ex = d[d.side.str.startswith("NDX")].sort_values("ts").groupby("B").tail(3)
    print("\n== Örnek NDX işlemleri — D'ye kadar son 10 dakikanın ham hacmi (sağdaki = D dakikası)")
    for _, r in ex.iterrows():
        seq = rows[d.index.get_loc(r.name)]["_prof_v"][-PROFILE[1] - 11:-PROFILE[1]]
        print(f"  {r.ts:%m-%d %H:%M} {r.side} {'B→SL' if r.B else 'A→TP'}: {', '.join(str(int(x)) for x in seq)}")


if __name__ == "__main__":
    main()
