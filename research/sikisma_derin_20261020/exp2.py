"""Sıkışma — ikinci tur: (1) bot öncesi panel örneklemi S9, (2) geometri mekanizması (RR taraması + sonraki
oynaklık genişlemesi), (3) A10 yürüyen ML. → results/rapor2.md

Ön-kayıt eki (sonuçlara bakmadan, 2026-10-20):
- S9 = prediction_logs NDX 7 model, 2026-02-18 → 06-12, model×yön başına 30 dk'da bir; aynı simülasyon.
  E4 notu: NDX 1m 02-10 → 03-08 arası şüpheli (60 dk kayma geçmişi) → duyarlılık: 03-09 sonrası ayrıca.
- Mekanizma: SL aynı (fiyat×%0,373), RR ∈ {0,73, 1,0, 1,5, 2,0}. Hipotez G: etki geometrikse (sıkışma → genişleme →
  yakın TP'nin bant avantajı kaybolur) Δ = ortR(engel) − ortR(kalan) RR büyüdükçe sıfıra/pozitife gider.
  Ek ölçü: sonraki 60 dk yüksek−düşük / ATR100 (genişleme) sıkışmada büyük mü.
- A10: özellikler A1–A9 + saat sin/cos + yön; aylık genişleyen pencere; lojistik ve LightGBM (P(SL)); test ayında eğitim
  tahminlerinin %60 kantili üstü engellenir. Aynı aylarda atr_14_100<1 kuralıyla kıyas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb

import core as C

OUT = C.HERE / "results"
RRS = (0.73, 1.0, 1.5, 2.0)
SUSPECT_END = pd.Timestamp("2026-03-09", tz="UTC")
RULE = ("atr_14_100<1", "atr_14_100", 1.0, "lt")
ML_BLOCK_Q = 0.60
FEATS = list(C.ALL_FEATS)


def sim_rr(sb, ev: pd.DataFrame, rr: float) -> np.ndarray:
    old = C.RR
    C.RR = rr
    try:
        return C.sim_events(sb, ev, C.NDX_RISK_FRAC, C.SPREAD["NDX.INDX"])
    finally:
        C.RR = old


def expansion(sb, ev: pd.DataFrame, F: pd.DataFrame) -> np.ndarray:
    idx, h, l = sb.m1.index, sb.a["high"], sb.a["low"]
    j0 = idx.searchsorted(pd.to_datetime(ev.t, utc=True), side="left")
    out = np.full(len(ev), np.nan)
    pc = np.r_[np.nan, sb.a["close"][:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    cs = np.r_[0, np.nancumsum(tr)]
    for k, j in enumerate(j0):
        if j < 101 or j + 60 >= idx.size:
            continue
        atr100 = (cs[j] - cs[j - 100]) / 100
        out[k] = (h[j:j + 60].max() - l[j:j + 60].min()) / atr100
    return out


def delta(d: pd.DataFrame, col: str) -> tuple[float, float, float]:
    m = d.atr_14_100 < 1.0
    x = d[col]
    return float(x[m].mean()), float(x[~m].mean()), float(x[m].mean() - x[~m].mean())


def walk_forward(d: pd.DataFrame, label: str) -> list[str]:
    d = d[np.isfinite(d.R)].dropna(subset=["atr_14_100"]).sort_values("t").reset_index(drop=True)
    hr = pd.to_datetime(d.t, utc=True).dt.hour + pd.to_datetime(d.t, utc=True).dt.minute / 60
    X = d[FEATS].copy()
    X["hs"], X["hc"], X["s"] = np.sin(2 * np.pi * hr / 24), np.cos(2 * np.pi * hr / 24), d.s
    X = X.fillna(X.median())
    y = (d.R < 0).astype(int).to_numpy()
    mon = pd.to_datetime(d.t, utc=True).dt.strftime("%Y-%m").to_numpy()
    months = sorted(set(mon))
    res = {"lojistik": [], "lgbm": [], "kural": []}
    for k, m in enumerate(months):
        tr, te = mon < m, mon == m
        if tr.sum() < 200 or k < 2 or te.sum() < 10:
            continue
        sc = StandardScaler().fit(X[tr])
        lr = LogisticRegression(max_iter=500, C=0.5).fit(sc.transform(X[tr]), y[tr])
        gb = lgb.LGBMClassifier(n_estimators=150, num_leaves=7, learning_rate=0.05, min_child_samples=30,
                                subsample=0.8, colsample_bytree=0.8, verbose=-1, random_state=1).fit(X[tr], y[tr])
        for nm, mdl, Z in (("lojistik", lr, sc.transform), ("lgbm", gb, lambda a: a)):
            p_tr, p_te = mdl.predict_proba(Z(X[tr]))[:, 1], mdl.predict_proba(Z(X[te]))[:, 1]
            blk = p_te > np.quantile(p_tr, ML_BLOCK_Q)
            res[nm].append((m, d.R[te][blk].to_numpy(), d.R[te][~blk].to_numpy()))
        rb = (d.atr_14_100[te] < 1.0).to_numpy()
        res["kural"].append((m, d.R[te][rb].to_numpy(), d.R[te][~rb].to_numpy()))
    L = [f"\n### A10 yürüyen ML — {label} (test ayları: {len(res['kural'])})",
         "| yöntem | engel | ortR engel | ortR kalan | kurt_R | ay + / toplam |", "|---|---|---|---|---|---|"]
    for nm, rows in res.items():
        if not rows:
            continue
        b = np.concatenate([r[1] for r in rows])
        kp = np.concatenate([r[2] for r in rows])
        pos = sum(-r[1].sum() > 0 for r in rows)
        L.append(f"| {nm} | {b.size} | {b.mean():+.3f} | {kp.mean():+.3f} | {-b.sum():+.1f} | {pos}/{len(rows)} |")
    return L


def main() -> None:
    long = C.bars_ndx_long()
    FL = C.compute_feats(long)
    sbl = C.SymbolBars("NDX.INDX", long)
    L = ["# Sıkışma — ikinci tur (exp2.py; ön-kayıt eki dosya başında)"]

    # (1) S9 bot öncesi panel
    p = pd.read_parquet(OUT / "panel_old.parquet")
    ev = pd.DataFrame({"t": p.ts, "s": np.where(p.ml_direction == "BUY", 1, -1), "fam": p.model_type})
    import events as E
    ev = E.dedup(ev, ["fam", "s"])
    for rr in RRS:
        ev[f"R_{rr:g}"] = sim_rr(sbl, ev, rr)
    ev["R"] = ev["R_0.73"]
    ev = E.add(ev, FL)
    ev["genis60"] = expansion(sbl, ev, FL)
    ev.to_parquet(OUT / "ev_S9_panel_old.parquet")
    q = {f: {qq: float(pd.read_parquet(OUT / "ev_S8_placebo.parquet")[f].quantile(qq)) for qq in C.QUANT_TH}
         for f in C.QUANT_FEATS}
    t9 = C.evaluate(ev, q, "S9 panel bot-öncesi")
    t9b = C.evaluate(ev[ev.t >= SUSPECT_END], q, "S9 panel bot-öncesi (03-09→)")
    t9.to_csv(OUT / "s9_kurallar.csv", index=False)
    L.append(f"\n## 1. S9 — bot ÖNCESİ panel sinyalleri (n={len(ev)}; 02-18 → 06-12)")
    cols = ["kaynak", "kural", "engel", "ortR_engel", "ortR_kalan", "kurt_R", "P(kurt>0)", "saat_plasebo", "Ç+", "çeyrekler"]
    keep = ["atr_14_100<0.9", "atr_14_100<1", "atr_14_100<1.1", "atr14_seas<1", "atr_5_60<1", "atr_30_240<1",
            "rv_14_100<1", "bbw5_pct<q20", "ttm_sqz=1", "vol_14_100<1"]
    L.append(C.md(pd.concat([t9, t9b])[lambda x: x.kural.isin(keep)][cols]))
    L.append("\nModel başına (atr_14_100<1):")
    rows = []
    for mdl, g in ev.groupby("fam"):
        g = g[np.isfinite(g.R) & g.atr_14_100.notna()]
        a, b, dd = delta(g, "R")
        rows.append({"model": mdl, "n": len(g), "ortR sıkışık": a, "ortR diğer": b, "Δ": dd})
    L.append(C.md(pd.DataFrame(rows)))

    # (2) mekanizma: RR taraması — S9 + S3 panel + S8 plasebo + S6M
    L.append("\n## 2. Mekanizma — aynı SL, farklı RR: Δ = ortR(sıkışık) − ortR(diğer) (atr_14_100<1)")
    srcs = {"S9 panel bot-öncesi": ev}
    for f, lab in (("ev_S3_panel", "S3 panel"), ("ev_S8_placebo", "S8 plasebo"), ("ev_S6M_ndx", "S6M kırılım-devam"),
                   ("ev_S6R_ndx", "S6R kırılım-dönüş")):
        d = pd.read_parquet(OUT / f"{f}.parquet")
        if f == "ev_S3_panel":
            nd = C.SymbolBars("NDX.INDX", C.bars_snapshots("NDX.INDX", "2026-05-20"))
            for rr in RRS:
                d[f"R_{rr:g}"] = sim_rr(nd, d, rr)
        else:
            for rr in RRS:
                d[f"R_{rr:g}"] = sim_rr(sbl, d, rr)
            d["genis60"] = expansion(sbl, d, FL)
        srcs[lab] = d
    rows = []
    for lab, d in srcs.items():
        d = d[d.atr_14_100.notna()]
        row = {"kaynak": lab, "n": len(d)}
        for rr in RRS:
            row[f"Δ RR{rr:g}"] = delta(d[np.isfinite(d[f"R_{rr:g}"])], f"R_{rr:g}")[2]
        if "genis60" in d:
            a, b, _ = delta(d[np.isfinite(d.genis60)], "genis60")
            row["sonraki60 aralık/ATR100 sıkışık"], row["diğer"] = a, b
        rows.append(row)
    L.append(C.md(pd.DataFrame(rows)))

    # (3) A10 yürüyen ML
    L.append("\n## 3. A10 yürüyen ML (P(SL) modeli; test ayında eğitim tahminlerinin %60 üstü engel)")
    pan = pd.concat([ev.assign(src="S9"), srcs["S3 panel"].assign(src="S3")], ignore_index=True)
    L += walk_forward(pan, "panel S9+S3 (02 → 10)")
    bot = pd.read_parquet(OUT / "ev_S1_bot.parquet")
    L += walk_forward(bot[(bot.sym == "NDX.INDX") & (~bot.fam.isin(["DECIDER", "MANUEL"]))], "bot NDX")
    L += walk_forward(pd.read_parquet(OUT / "ev_S6M_ndx.parquet"), "S6M kırılım-devam 2025-26")
    txt = "\n".join(L)
    (OUT / "rapor2.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
