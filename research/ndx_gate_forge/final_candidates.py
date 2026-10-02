"""Beş aday kapının son değerlendirmesi (tanımlar bu dosyada donduruldu).

K1 Pazartesi SELL yok            (NY takvim günü = Pazartesi)
K2 FOMC öncesi 24s SELL yok      (FOMC'den önceki gün 14:00 ET → FOMC günü 14:00 ET)
K3 Ay sonu dengeleme             (ayın son 2 işlem günü; ay-içi NDX ≥ +%4 → BUY yok, ≤ −%4 → SELL yok)
K4 Pürüzlülük                    (VR15 son 240 dk (1m) > 1.2 → TP<SL braketi açma, iki yön)
K5 Stres-dönüş SELL yok          (dün NDX ≤ −%1.5 veya son 5 gün ≤ −%4)
K6 Aşırı uzama BUY yok           (NDX, 200 günlük ortalamanın %10+ üstünde) — K5'in aynası

Katmanlar: (a) genel 1m 5 dönem, (b) 30m 2021-26 / 15m 2023-26 yıl-yıl,
(c) botun kapı evreni içinde ARTIMSAL (VIX yönü + trend + konum + TQ),
(d) botun gerçek işlemleri (07-01→09-30), (e) VIXREG-vekil portföy simülasyonu.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, DATA, ROOT, load_1m, simulate, atr, block_boot
from evaluate import load, PER
from features import _last_complete, map_asof
import daylevel_trades as dt
from macro10y import FOMC

FOMC_ALL = pd.to_datetime(FOMC + ["2026-07-29", "2026-09-16"])


def conds(nyd: pd.Series, ny_min: np.ndarray, wd: np.ndarray, vr: np.ndarray | None,
          tr60: np.ndarray | None = None) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    x = dt.day_conditions(nyd, pd.Series(ny_min // 60, index=nyd.index), pd.Series(wd, index=nyd.index))
    z = np.zeros(len(nyd), bool)
    fomc_day = nyd.isin(FOMC_ALL).to_numpy()
    fomc_eve = nyd.isin(FOMC_ALL - pd.Timedelta(days=1)).to_numpy()
    k2 = (fomc_eve & (ny_min >= 14 * 60)) | (fomc_day & (ny_min < 14 * 60))
    me = x.month_end2.to_numpy()
    out = {
        "K1 Pazartesi SELL yok": (z, np.asarray(wd) == 0),
        "(elendi) K2 FOMC öncesi 24s SELL yok": (z, k2),
        "K3 Ay sonu dengeleme": (me & (x.mtd.to_numpy() >= .04), me & (x.mtd.to_numpy() <= -.04)),
        "K5 Stres-dönüş SELL yok": (z, ((x.ndx_ret1 <= -.015) | (x.ndx_ret5 <= -.04)).to_numpy()),
        "K6 Aşırı uzama BUY yok": ((x.ndx_d200 > .10).to_numpy(), z),
    }
    if vr is not None:
        out["K4a Pürüzlülük VR>1.2 (iki yön)"] = (vr > 1.2, vr > 1.2)
    if vr is not None and tr60 is not None:
        # sonradan kurulan hipotez: kalıcı yolda son 60 dk hareketine KARŞI girme
        out["K4b VR>1.2 iken fade yok (post-hoc)"] = ((vr > 1.2) & (tr60 < 0), (vr > 1.2) & (tr60 > 0))
    return out


def lift(y: dict, masks: tuple, days: np.ndarray, grp: np.ndarray) -> dict:
    vals, dd, gg = [], [], []
    for s, m in zip("BS", masks):
        v = y[s][m]
        ok = ~np.isnan(v)
        vals.append(v[ok]); dd.append(days[m][ok]); gg.append(grp[m][ok])
    v, dd, gg = np.concatenate(vals), np.concatenate(dd), np.concatenate(gg)
    if len(v) == 0:
        return {"n_gün": 0}
    bs = block_boot(v, dd, 3000)
    per = pd.Series(v).groupby(gg).mean()
    return {"fark_R": round(float(v.mean()), 4), "P(<0)": round(float(np.mean(bs < 0)), 3), "n_gün": int(len(np.unique(dd))),
            "doğru/grup": f"{int((per < 0).sum())}/{len(per)}", "gruplar": {k: round(float(val), 3) for k, val in per.items()}}


def generic_1m(universe: str) -> dict:
    d = load(1)
    nyd = pd.to_datetime(d.ny_date)
    C = conds(nyd, d.ny_min.to_numpy(), d.wd.to_numpy(), d.vr15.to_numpy(), d.tr60.to_numpy())
    feat2 = pd.read_parquet(DATA / "feat2.parquet", columns=["vix"]).iloc[d.i.to_numpy()].reset_index(drop=True)
    if universe == "bot":
        vix = feat2.vix.to_numpy()
        tq = d.utc_h.between(15, 17).to_numpy()
        ub = (vix >= 18.4) & (d.h1_trend.to_numpy() > 0) & (d.pos4.to_numpy() <= .6) & ~tq
        us = (vix < 18.4) & (d.h1_trend.to_numpy() < 0) & (d.pos4.to_numpy() >= .4) & ~tq
    else:
        ub = us = np.ones(len(d), bool)
    y = {}
    for s, u in [("B", ub), ("S", us)]:
        v = d[f"R_G80_{s}"].where(u)
        y[s] = (v - v.groupby([d.period, d.utc_h]).transform("mean")).to_numpy()
    out = {}
    for k, (mb, ms) in C.items():
        out[k] = lift(y, (mb & ub, ms & us), d.ny_date.to_numpy(), d.period.to_numpy())
    return out


def generic_long(tf: str) -> dict:
    T = dt.long_trades(tf)
    T = T[T.nyd.dt.year >= 2021].reset_index(drop=True)
    ny_min = (T.ts + pd.Timedelta(minutes=int(tf[:-1]))).dt.tz_convert("America/New_York")
    ny_min = (ny_min.dt.hour * 60 + ny_min.dt.minute).to_numpy()
    C = conds(T.nyd, ny_min, T.wd.to_numpy(), None)
    y = {s: (T[f"R_{s}"] - T.groupby(["grp", "utc_h"])[f"R_{s}"].transform("mean")).to_numpy() for s in "BS"}
    return {k: lift(y, m, T.nyd.astype(str).to_numpy(), T.grp.to_numpy()) for k, m in C.items()}


def bot_trades() -> dict:
    t = pd.read_csv(ROOT / "nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv")
    b = pd.read_csv(DATA / "box_trades_40d.csv")
    b = b[b.symbol == "NAS100"]
    t = pd.concat([t, b[~b.position_id.isin(t.position_id)]], ignore_index=True)
    t["ot"] = pd.to_datetime(t.open_time_utc, utc=True)
    t["pts"] = t.profit / t.volume
    t["dec"] = t.ot.dt.floor("min").astype(str) + t.direction
    g = t.groupby("dec").agg(ot=("ot", "first"), side=("direction", "first"), pts=("pts", "mean"), usd=("profit", "sum"),
                             magic=("magic", "first")).reset_index()
    bars = load_1m()
    f1 = pd.read_parquet(DATA / "feat_tf1.parquet", columns=["vr15", "tr60"])
    k = np.searchsorted(bars.t.to_numpy() + 60, g.ot.astype("int64").to_numpy() // 10**9, side="right") - 1
    vr = np.where(k >= 0, f1.vr15.to_numpy()[np.maximum(k, 0)], np.nan)
    tr60 = np.where(k >= 0, f1.tr60.to_numpy()[np.maximum(k, 0)], np.nan)
    ny = g.ot.dt.tz_convert("America/New_York")
    nyd = pd.to_datetime(ny.dt.date)
    C = conds(nyd, (ny.dt.hour * 60 + ny.dt.minute).to_numpy(), ny.dt.weekday.to_numpy(), vr, tr60)
    out = {"_toplam": {"karar": len(g), "puan/karar": round(g.pts.mean(), 2), "usd": round(g.usd.sum(), 0)}}
    for name, (mb, ms) in C.items():
        blk = ((g.side == "BUY").to_numpy() & mb) | ((g.side == "SELL").to_numpy() & ms)
        x, r = g[blk], g[~blk]
        chrev = (g.magic == 52890970).to_numpy()
        out[name + " | CHREV"] = {"bloklanır_n": int((blk & chrev).sum()),
                                  "bloklanan_puan": round(g.pts[blk & chrev].mean(), 2) if (blk & chrev).any() else None,
                                  "kalan_puan": round(g.pts[~blk & chrev].mean(), 2)}
        out[name] = {"bloklanır_n": int(blk.sum()), "bloklanan_puan/karar": round(x.pts.mean(), 2) if len(x) else None,
                     "bloklanan_usd": round(x.usd.sum(), 0), "kalan_puan/karar": round(r.pts.mean(), 2)}
    allb = np.zeros(len(g), bool)
    for name in ["K1 Pazartesi SELL yok", "K3 Ay sonu dengeleme", "K5 Stres-dönüş SELL yok", "K6 Aşırı uzama BUY yok"]:
        mb, ms = C[name]
        allb |= ((g.side == "BUY").to_numpy() & mb) | ((g.side == "SELL").to_numpy() & ms)
    out["K1+K3+K5+K6"] = {"bloklanır_n": int(allb.sum()), "bloklanan_puan/karar": round(g.pts[allb].mean(), 2),
                          "bloklanan_usd": round(g.usd[allb].sum(), 0), "kalan_puan/karar": round(g.pts[~allb].mean(), 2),
                          "kalan_usd": round(g.usd[~allb].sum(), 0)}
    return out


def proxy_portfolio() -> dict:
    """VIXREG vekili: VIX yönü + trend + konum + TQ, tek pozisyon, 30 dk ara, TP80/SL clip(2·ATR5m,60,200)."""
    b = load_1m()
    d = load(1)
    feat2 = pd.read_parquet(DATA / "feat2.parquet", columns=["vix"]).iloc[d.i.to_numpy()].reset_index(drop=True)
    m5 = _last_complete(b[["ts", "t", "open", "high", "low", "close", "volume"]], 5)
    a5 = atr(m5.high.to_numpy(), m5.low.to_numpy(), m5.close.to_numpy(), 14)
    a5m = map_asof(b.t.to_numpy() + 60, m5.avail.to_numpy(), a5, 900)
    vix = feat2.vix.to_numpy()
    side = np.where(vix >= 18.4, 1, -1)
    ok = ((side == 1) & (d.h1_trend.to_numpy() > 0) & (d.pos4.to_numpy() <= .6)) | \
         ((side == -1) & (d.h1_trend.to_numpy() < 0) & (d.pos4.to_numpy() >= .4))
    ok &= ~d.utc_h.between(15, 17).to_numpy()
    nyd = pd.to_datetime(d.ny_date)
    C = conds(nyd, d.ny_min.to_numpy(), d.wd.to_numpy(), d.vr15.to_numpy(), d.tr60.to_numpy())
    idx_all = d.i.to_numpy()
    sl_all = np.clip(2 * a5m[idx_all], 60, 200)
    # tüm aday girişleri önce simüle et, sonra sıralı tek-pozisyon seçimi
    R, dur, why = simulate(b, idx_all, side, np.full(len(d), 80.0), sl_all)
    tt = b.t.to_numpy()[idx_all]

    def run(block: np.ndarray) -> pd.DataFrame:
        take, free_at = [], -1
        cand = np.flatnonzero(ok & ~block & ~np.isnan(R))
        for j in cand:
            if tt[j] < free_at:
                continue
            take.append(j)
            free_at = tt[j] + 60 + dur[j] * 60 + 30 * 60
        return pd.DataFrame({"R": R[take], "period": d.period.to_numpy()[take], "side": side[take]})

    base = run(np.zeros(len(d), bool))
    out = {"KAPISIZ (vekil)": base.groupby("period").R.agg(["size", "mean", "sum"]).round(3).to_dict("index")}
    allblk = np.zeros(len(d), bool)
    for k, (mb, ms) in C.items():
        blk = ((side == 1) & mb) | ((side == -1) & ms)
        allblk |= blk
        r = run(blk)
        out[k] = r.groupby("period").R.agg(["size", "mean", "sum"]).round(3).to_dict("index")
    combo = np.zeros(len(d), bool)
    for k in ["K1 Pazartesi SELL yok", "K3 Ay sonu dengeleme", "K5 Stres-dönüş SELL yok", "K6 Aşırı uzama BUY yok"]:
        mb, ms = C[k]
        combo |= ((side == 1) & mb) | ((side == -1) & ms)
    r = run(combo)
    out["K1+K3+K5+K6"] = r.groupby("period").R.agg(["size", "mean", "sum"]).round(3).to_dict("index")
    out["K1+K3+K5+K6 toplam"] = {"n": len(r), "ΣR": round(float(r.R.sum()), 2), "ort": round(float(r.R.mean()), 4),
                                 "kapısız_n": len(base), "kapısız_ΣR": round(float(base.R.sum()), 2)}
    r = run(allblk)
    out["TÜM ADAYLAR (elenenler dahil)"] = r.groupby("period").R.agg(["size", "mean", "sum"]).round(3).to_dict("index")
    return out


if __name__ == "__main__":
    res = {"a_genel_1m": generic_1m("all"), "c_bot_evreni_1m": generic_1m("bot"),
           "b_30m_2021+": generic_long("30m"), "b_15m_2023+": generic_long("15m"),
           "d_bot_islemleri": bot_trades(), "e_vekil_portfoy": proxy_portfolio()}
    (OUT / "final_candidates.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for sec, v in res.items():
        print(f"\n=== {sec} ===")
        for k, val in v.items():
            print(f"  {k}: {val}")
