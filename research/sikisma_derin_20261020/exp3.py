"""Sıkışma — üçüncü tur: veri kaynağı kontrolü, aylık işaret, uyarlanabilir filtre, rejim koşulları → results/rapor3.md

Ön-kayıt eki (exp2 sonrası, S9'da etki TERSİNE döndü; sonuçlara bakmadan):
- K1 veri kaynağı: S3 (06-15 → 09-30) aynı olaylar uzun 1m tablosuyla (bars_1m_all) yeniden simüle + özellik;
  Δ işareti korunuyorsa fark kaynak değil dönem.
- K2 aylık Δ = ortR(sıkışık) − ortR(diğer), atr_14_100<1: panel (S9+S3), bot NDX, S6M, S8.
- K3 UYARLANABİLİR filtre (yeni algoritma): olay anında, çözümü kesin bilinen (t − 6 s öncesi) son W gün olaylarında
  Δ_geçmiş hesaplanır (her grupta ≥30); Δ_geçmiş < −θ ise sıkışık olay engellenir. W ∈ {10, 20, 40} gün,
  θ ∈ {0, 0,05}. Değerlendirme: kurt_R, çeyrekler, saat-eşli plasebo. Kaynaklar: panel S9+S3, bot NDX, S6M, S6R, S8.
- K4 rejim (KEŞİF, kanıt değil): Δ'nın VIX(önceki gün) ≥/< 18,4, NDX günlük kapanış ≷ SMA20, seans ve yön kırılımı.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C
import events as E

OUT = C.HERE / "results"
WS, THS = (10, 20, 40), (0.0, 0.05)
MIN_GRP = 30
RESOLVE_LAG = pd.Timedelta(hours=6)
VIX_T = 18.4


def dlt(g: pd.DataFrame) -> float:
    m = g.atr_14_100 < 1.0
    return float(g.R[m].mean() - g.R[~m].mean()) if m.sum() >= 5 and (~m).sum() >= 5 else np.nan


def monthly(d: pd.DataFrame, lab: str) -> dict:
    d = d[np.isfinite(d.R) & d.atr_14_100.notna()]
    mon = pd.to_datetime(d.t, utc=True).dt.strftime("%Y-%m")
    return {"kaynak": lab, **{m: dlt(g) for m, g in d.groupby(mon)}}


def adaptive(d: pd.DataFrame, W: int, th: float) -> np.ndarray:
    d = d.reset_index(drop=True)
    t = pd.to_datetime(d.t, utc=True).to_numpy()
    sq = (d.atr_14_100 < 1.0).to_numpy()
    R = d.R.to_numpy(float)
    blk = np.zeros(len(d), bool)
    lo = 0
    for i in range(len(d)):
        if not sq[i]:
            continue
        hi = np.searchsorted(t, t[i] - RESOLVE_LAG.to_timedelta64(), side="right")
        lo = np.searchsorted(t, t[i] - np.timedelta64(W, "D"), side="left")
        s, r = sq[lo:hi], R[lo:hi]
        if s.sum() >= MIN_GRP and (~s).sum() >= MIN_GRP and r[s].mean() - r[~s].mean() < -th:
            blk[i] = True
    return blk


def eval_mask(d: pd.DataFrame, blk: np.ndarray, lab: str) -> dict:
    R = d.R.to_numpy(float)
    hours = pd.to_datetime(d.t, utc=True).dt.hour.to_numpy()
    nb = int(blk.sum())
    if nb < 5:
        return {"kaynak": lab, "engel": nb}
    qs = C.quarters(R, blk)
    return {"kaynak": lab, "n": len(d), "engel": nb, "ortR_engel": R[blk].mean(), "ortR_kalan": R[~blk].mean(),
            "kurt_R": -R[blk].sum(), "P(kurt>0)": C.boot_saved(R, blk, C.day_ids(d.t)),
            "saat_plasebo": C.hour_placebo(R, blk, hours), "Ç+": sum(x >= 0 for x in qs),
            "çeyrekler": "/".join(f"{x:+.1f}" for x in qs)}


def vix_series() -> pd.Series:
    v = C.data.load_vix(pd.Timestamp("2024-12-01", tz="UTC"), C.data.utc_now())
    return v.sort_index()


def regimes(d: pd.DataFrame, vix: pd.Series, daily: pd.Series) -> pd.DataFrame:
    t = pd.to_datetime(d.t, utc=True)
    day = pd.to_datetime(t.dt.tz_convert("America/New_York").dt.date)
    vi = vix.reindex(vix.index.union(day.unique())).sort_index().ffill().shift(1)
    out = d.copy()
    out["vix_hi"] = vi.reindex(day).to_numpy() >= VIX_T
    sma = daily.rolling(20).mean()
    up = (daily > sma).shift(1)
    out["trend_up"] = up.reindex(day, method="ffill").to_numpy().astype(float)
    h = t.dt.hour
    out["seans"] = np.where(h < 7, "ASYA", np.where(h < 13, "AVRUPA", np.where(h < 20, "ABD", "GECE")))
    return out


def main() -> None:
    L = ["# Sıkışma — üçüncü tur (exp3.py; ön-kayıt eki dosya başında)"]
    long = C.bars_ndx_long()
    FL = C.compute_feats(long)
    sbl = C.SymbolBars("NDX.INDX", long)

    # K1
    s3 = pd.read_parquet(OUT / "ev_S3_panel.parquet")
    s3o = s3[s3.t < pd.Timestamp("2026-09-30", tz="UTC")][["t", "s", "fam"]].copy()
    s3o["R"] = C.sim_events(sbl, s3o, C.NDX_RISK_FRAC, C.SPREAD["NDX.INDX"])
    s3o = E.add(s3o, FL)
    s3s = s3[s3.t < pd.Timestamp("2026-09-30", tz="UTC")]
    L.append("\n## K1 veri kaynağı kontrolü — S3 olayları (06-15 → 09-30) iki farklı 1m tablosuyla")
    L.append(f"- snapshot (broker) tablosu: Δ = {dlt(s3s[np.isfinite(s3s.R) & s3s.atr_14_100.notna()]):+.3f} (n={len(s3s)})")
    L.append(f"- uzun tablo (bars_1m_all):  Δ = {dlt(s3o[np.isfinite(s3o.R) & s3o.atr_14_100.notna()]):+.3f} (n={len(s3o)})")
    agree = (s3s.atr_14_100.lt(1).to_numpy() == s3o.atr_14_100.lt(1).to_numpy()).mean()
    L.append(f"- sıkışık etiketinin iki tabloda aynı olma oranı: %{100 * agree:.0f}")

    # K2
    s9 = pd.read_parquet(OUT / "ev_S9_panel_old.parquet")
    panel = pd.concat([s9[["t", "s", "fam", "R"] + list(C.ALL_FEATS)], s3[["t", "s", "fam", "R"] + list(C.ALL_FEATS)]],
                      ignore_index=True).sort_values("t").reset_index(drop=True)
    bot = pd.read_parquet(OUT / "ev_S1_bot.parquet")
    bot = bot[(bot.sym == "NDX.INDX") & (~bot.fam.isin(["DECIDER", "MANUEL"]))].sort_values("t").reset_index(drop=True)
    s6m = pd.read_parquet(OUT / "ev_S6M_ndx.parquet").sort_values("t").reset_index(drop=True)
    s6r = pd.read_parquet(OUT / "ev_S6R_ndx.parquet").sort_values("t").reset_index(drop=True)
    s8 = pd.read_parquet(OUT / "ev_S8_placebo.parquet").sort_values("t").reset_index(drop=True)
    mt = pd.DataFrame([monthly(x, n) for n, x in (("panel S9+S3", panel), ("bot NDX", bot), ("S6M devam", s6m),
                                                  ("S6R dönüş", s6r), ("S8 plasebo", s8))])
    mt = mt[["kaynak"] + sorted(c for c in mt.columns if c != "kaynak")]
    L.append("\n## K2 aylık Δ (sıkışık − diğer, R) — işaret dönemden döneme değişiyor mu?")
    L.append(C.md(mt, "{:+.2f}"))

    # K3
    L.append("\n## K3 uyarlanabilir filtre (geçmiş W günde sıkışık kötüyse engelle)")
    rows = []
    for lab, d in (("panel S9+S3", panel), ("bot NDX", bot), ("S6M devam", s6m), ("S6R dönüş", s6r), ("S8 plasebo", s8)):
        d = d[np.isfinite(d.R) & d.atr_14_100.notna()].sort_values("t").reset_index(drop=True)
        rows.append({**eval_mask(d, (d.atr_14_100 < 1.0).to_numpy(), lab), "kural": "statik <1"})
        for W in WS:
            for th in THS:
                rows.append({**eval_mask(d, adaptive(d, W, th), lab), "kural": f"uyarlanır W{W} θ{th:g}"})
    at = pd.DataFrame(rows)
    at.to_csv(OUT / "uyarlanir.csv", index=False)
    L.append(C.md(at[["kaynak", "kural", "engel", "ortR_engel", "ortR_kalan", "kurt_R", "P(kurt>0)", "saat_plasebo", "Ç+", "çeyrekler"]]))

    # K4
    vix = vix_series()
    daily = long.close.resample("1D").last().dropna()
    daily.index = daily.index.tz_convert(None).normalize()
    L.append("\n## K4 rejim kırılımı (KEŞİF) — Δ ve n")
    rows = []
    for lab, d in (("panel S9+S3", panel), ("bot NDX", bot), ("S6M devam", s6m), ("S8 plasebo", s8)):
        r = regimes(d[np.isfinite(d.R) & d.atr_14_100.notna()], vix, daily)
        for col in ("vix_hi", "trend_up", "seans", "s"):
            for k, g in r.groupby(col):
                rows.append({"kaynak": lab, "koşul": f"{col}={k}", "n": len(g), "Δ": dlt(g),
                             "sıkışık%": float((g.atr_14_100 < 1).mean())})
    L.append(C.md(pd.DataFrame(rows)))
    txt = "\n".join(L)
    (OUT / "rapor3.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
