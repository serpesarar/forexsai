"""Tur 2 — PROTOCOL_2.md'deki T1–T6 hipotezleri."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, DATA, ROOT, load_1m, block_boot, simulate
from evaluate import load
from features import _last_complete, map_asof
from final_candidates import lift, conds
from long_data import load_long, macro
import daylevel_trades as dt

CH_N = 50


def chan_z(y: np.ndarray, n: int = CH_N) -> np.ndarray:
    """Kayan n-bar linreg kanalında son kapanışın z'si (decider channel_zscore ile aynı)."""
    out = np.full(len(y), np.nan)
    if len(y) < n:
        return out
    x = np.arange(n, dtype=float)
    xm, xv = x.mean(), x.var()
    sy = np.convolve(y, np.ones(n), "valid")
    sxy = np.convolve(y, np.arange(n - 1, -1, -1, dtype=float), "valid")
    sy2 = np.convolve(y * y, np.ones(n), "valid")
    ym = sy / n
    cov = sxy / n - xm * ym
    a = cov / xv
    var_y = sy2 / n - ym * ym
    res_var = np.maximum(var_y - a * a * xv, 0)
    mid = ym + a * (n - 1 - xm)
    last = y[n - 1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (last - mid) / np.sqrt(res_var)
    out[n - 1:] = np.where(res_var > 1e-12, z, np.nan)
    return out


def tf_feats(b: pd.DataFrame, tf: int, dec_t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    s = _last_complete(b[["ts", "t", "open", "high", "low", "close", "volume"]], tf)
    cz = chan_z(s.close.to_numpy(float))
    v = s.volume.to_numpy(float)
    prev20 = pd.Series(v).shift(1).rolling(20).mean().to_numpy()
    vr = np.where(prev20 > 0, v / prev20, np.nan)
    return (map_asof(dec_t, s.avail.to_numpy(), cz, tf * 60 * 3), map_asof(dec_t, s.avail.to_numpy(), vr, tf * 60 * 3))


def daily_ctx(nyd: pd.Series) -> pd.DataFrame:
    m = macro()
    full = pd.date_range("2014-01-01", "2026-12-31")
    ndx = m.NDXCASH_close.dropna()
    vol = ndx.pct_change().rolling(20).std()
    z5 = ndx.pct_change(5) / (vol * np.sqrt(5))
    prev = nyd - pd.Timedelta(days=1)
    return pd.DataFrame({"z5": z5.reindex(full).ffill().reindex(prev).to_numpy(),
                         "dvol": vol.reindex(full).ffill().reindex(prev).to_numpy()}, index=nyd.index)


def sanity_chan() -> float:
    rng = np.random.default_rng(1)
    y = np.cumsum(rng.normal(size=300))
    z = chan_z(y)
    k = 200
    w = y[k - CH_N + 1:k + 1]
    a, b0 = np.polyfit(np.arange(CH_N), w, 1)
    ref = (w[-1] - (a * (CH_N - 1) + b0)) / (w - (a * np.arange(CH_N) + b0)).std()
    return abs(z[k] - ref)


def generic(universe: str) -> dict:
    b = load_1m()
    d = load(1)
    dec = b.t.to_numpy()[d.i.to_numpy()] + 60
    cz5, vr5 = tf_feats(b, 5, dec)
    nyd = pd.to_datetime(d.ny_date)
    ctx = daily_ctx(nyd)
    vix = pd.read_parquet(DATA / "feat2.parquet", columns=["vix"]).iloc[d.i.to_numpy()].reset_index(drop=True).vix.to_numpy()
    if universe == "bot":
        tq = d.utc_h.between(15, 17).to_numpy()
        ub = (vix >= 18.4) & (d.h1_trend.to_numpy() > 0) & (d.pos4.to_numpy() <= .6) & ~tq
        us = (vix < 18.4) & (d.h1_trend.to_numpy() < 0) & (d.pos4.to_numpy() >= .4) & ~tq
    else:
        ub = us = np.ones(len(d), bool)
    y = {}
    for s, u in [("B", ub), ("S", us)]:
        v = d[f"R_G80_{s}"].where(u)
        y[s] = (v - v.groupby([d.period, d.utc_h]).transform("mean")).to_numpy()
    days, per = d.ny_date.to_numpy(), d.period.to_numpy()
    z5 = ctx.z5.to_numpy()
    H = {
        "T1 gerilme pusulası": (z5 >= 1, z5 <= -1),
        "T2 bıçak (5m kanal karşı ≥2σ)": (cz5 <= -2, cz5 >= 2),      # BUY: fiyat kanal dibinde; SELL: tepede
        "T3 hacim patlaması (5m ≥1.5)": (vr5 >= 1.5, vr5 >= 1.5),
        "T2|T3 birleşik (decider kapısı)": ((cz5 <= -2) | (vr5 >= 1.5), (cz5 >= 2) | (vr5 >= 1.5)),
    }
    out = {k: lift(y, (mb & ub, ms & us), days, per) for k, (mb, ms) in H.items()}
    # T4: günlük vol tertili (dönem içinde)
    C = conds(nyd, d.ny_min.to_numpy(), d.wd.to_numpy(), None)
    C["T1 gerilme pusulası"] = H["T1 gerilme pusulası"]
    terc = pd.Series(ctx.dvol.to_numpy()).groupby(per).transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)).to_numpy()
    t4 = {}
    for k in ["K1 Pazartesi SELL yok", "K5 Stres-dönüş SELL yok", "K6 Aşırı uzama BUY yok", "T1 gerilme pusulası"]:
        mb, ms = C[k]
        t4[k] = {f"tertil{q}": lift(y, (mb & ub & (terc == q), ms & us & (terc == q)), days, per).get("fark_R") for q in range(3)}
    out["T4 vol tertili (0=sakin)"] = t4
    # T5: stres günlerinde teyitli SELL
    ms_k5 = C["K5 Stres-dönüş SELL yok"][1]
    conf = d.price.to_numpy() < d.pdl.to_numpy()
    out["T5 stres günü: teyitli SELL (fiyat<önceki dip)"] = lift(y, (np.zeros(len(d), bool), ms_k5 & conf & us), days, per)
    out["T5 stres günü: teyitsiz SELL"] = lift(y, (np.zeros(len(d), bool), ms_k5 & ~conf & us), days, per)
    return out


def t6_generic() -> dict:
    """16:55 NY'de açık G80 pozisyonlarının kalan P&L'i (tutmak − 16:55'te kapatmak), R."""
    b = load_1m()
    d = load(1)
    t = b.t.to_numpy()
    ny = (b.ts + pd.Timedelta(minutes=1)).dt.tz_convert("America/New_York")
    nym = (ny.dt.hour * 60 + ny.dt.minute).to_numpy()
    nyd = ny.dt.strftime("%Y-%m-%d").to_numpy()
    close_bar = {}                                   # NY günü → 16:55 kararındaki bar indeksi
    k = np.flatnonzero(nym == 16 * 60 + 55)
    for i in k:
        close_bar[nyd[i]] = i
    res = {}
    for s, sgn in [("S", -1), ("B", 1)]:
        dur = d[f"dur_G80_{s}"].to_numpy()
        R = d[f"R_G80_{s}"].to_numpy()
        ent_t = t[np.minimum(d.i.to_numpy() + 1, len(t) - 1)]
        rows = []
        for j in range(len(d)):
            ci = close_bar.get(d.ny_date.iat[j])
            if ci is None or np.isnan(R[j]) or d.ny_min.iat[j] >= 16 * 60 + 55:
                continue
            exit_t = ent_t[j] + dur[j] * 60
            if exit_t <= t[ci] + 60:
                continue                              # 16:55'ten önce çözüldü
            i0 = d.i.iat[j] + 1
            entry = b.ao.iat[i0] + .2 if sgn == 1 else b.open.iat[i0] - .2
            px = b.close.iat[ci] if sgn == 1 else b.ac.iat[ci]
            r_close = (px - entry) * sgn / 110.0
            rows.append((d.period.iat[j], d.ny_date.iat[j], R[j] - r_close))
        x = pd.DataFrame(rows, columns=["p", "day", "delta"]).drop_duplicates(["day"], keep="first") \
            if False else pd.DataFrame(rows, columns=["p", "day", "delta"])
        bs = block_boot(x.delta.to_numpy(), x.day.to_numpy(), 3000)
        res[s] = {"tutmak−kapatmak_R": round(float(x.delta.mean()), 4), "P(<0)": round(float(np.mean(bs < 0)), 3),
                  "gün": int(x.day.nunique()), "dönemler": x.groupby("p").delta.mean().round(3).to_dict()}
    return res


def bot() -> dict:
    t = pd.read_csv(ROOT / "nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv")
    bx = pd.read_csv(DATA / "box_trades_40d.csv")
    bx = bx[bx.symbol == "NAS100"]
    t = pd.concat([t, bx[~bx.position_id.isin(t.position_id)]], ignore_index=True)
    t["ot"] = pd.to_datetime(t.open_time_utc, utc=True)
    t["ct"] = pd.to_datetime(t.close_time_utc, utc=True)
    t["pts"] = t.profit / t.volume
    t["dec"] = t.ot.dt.floor("min").astype(str) + t.direction
    g = t.groupby("dec").agg(ot=("ot", "first"), ct=("ct", "max"), side=("direction", "first"), pts=("pts", "mean"),
                             usd=("profit", "sum"), op=("open_price", "first")).reset_index()
    b = load_1m()
    dec = g.ot.astype("int64").to_numpy() // 10**9
    cz5, vr5 = tf_feats(b, 5, dec)
    ny = g.ot.dt.tz_convert("America/New_York")
    nyd = pd.to_datetime(ny.dt.date)
    ctx = daily_ctx(nyd)
    sell = (g.side == "SELL").to_numpy()
    buy = ~sell
    z5 = ctx.z5.to_numpy()
    H = {
        "T1 gerilme pusulası": (buy & (z5 >= 1)) | (sell & (z5 <= -1)),
        "T2 bıçak": (buy & (cz5 <= -2)) | (sell & (cz5 >= 2)),
        "T3 hacim patlaması": vr5 >= 1.5,
        "T2|T3 birleşik": (buy & (cz5 <= -2)) | (sell & (cz5 >= 2)) | (vr5 >= 1.5),
    }
    out = {"_toplam": {"karar": len(g), "puan/karar": round(g.pts.mean(), 2)}}
    for k, m in H.items():
        m = np.asarray(m, bool)
        days_b = g.ot[m].dt.date.nunique()
        # gün-bloklu bootstrap: bloklanan − kalan
        rng = np.random.default_rng(5)
        db = g[m].groupby(g.ot[m].dt.date).pts.agg(["sum", "size"])
        dk = g[~m].groupby(g.ot[~m].dt.date).pts.agg(["sum", "size"])
        diffs = []
        for _ in range(3000):
            a = db.iloc[rng.integers(0, len(db), len(db))] if len(db) else db
            c = dk.iloc[rng.integers(0, len(dk), len(dk))]
            if len(db):
                diffs.append(a["sum"].sum() / a["size"].sum() - c["sum"].sum() / c["size"].sum())
        out[k] = {"bloklanır": int(m.sum()), "gün": int(days_b), "bloklanan_p": round(g.pts[m].mean(), 2) if m.any() else None,
                  "kalan_p": round(g.pts[~m].mean(), 2), "bloklanan_usd": round(g.usd[m].sum(), 0),
                  "P(fark<0)": round(float(np.mean(np.array(diffs) < 0)), 3) if diffs else None}
    # T6 bot: 16:55 NY'yi aşan SELL'ler
    close1655 = []
    tt = b.t.to_numpy()
    for r in g[sell].itertuples():
        o_ny = r.ot.tz_convert("America/New_York")
        cut = o_ny.normalize() + pd.Timedelta(hours=16, minutes=55)
        if o_ny >= cut or r.ct.tz_convert("America/New_York") <= cut:
            continue
        ci = np.searchsorted(tt, int(cut.tz_convert("UTC").timestamp()) - 60)
        if ci >= len(tt):
            continue
        px = b.ac.iat[ci]
        close1655.append({"pts_hold": r.pts, "pts_close": r.op - px, "day": str(o_ny.date())})
    x = pd.DataFrame(close1655)
    out["T6 bot SELL 16:55'i aşan"] = ({"n": len(x), "gün": x.day.nunique(), "tutmak_p": round(x.pts_hold.mean(), 2),
                                       "16:55'te_kapat_p": round(x.pts_close.mean(), 2)} if len(x) else {"n": 0})
    return out


def long_tf(tf: str) -> dict:
    """30m/15m: T1 (gün-düzeyi) + T2/T3 bu TF'nin kendi kanal/hacmiyle (farklı zaman dilimi)."""
    T = dt.long_trades(tf)
    T = T[T.nyd.dt.year >= 2021].reset_index(drop=True)
    L = load_long(tf)
    cz = chan_z(L.close.to_numpy(float))
    v = L.volume.to_numpy(float)
    prev20 = pd.Series(v).shift(1).rolling(20).mean().to_numpy()
    L["cz"], L["vr"] = cz, np.where(prev20 > 0, v / prev20, np.nan)
    T = T.merge(L[["ts", "cz", "vr"]], on="ts", how="left")
    ctx = daily_ctx(T.nyd)
    z5 = ctx.z5.to_numpy()
    y = {s: (T[f"R_{s}"] - T.groupby(["grp", "utc_h"])[f"R_{s}"].transform("mean")).to_numpy() for s in "BS"}
    days, grp = T.nyd.astype(str).to_numpy(), T.grp.to_numpy()
    H = {"T1 gerilme pusulası": (z5 >= 1, z5 <= -1),
         "T2 bıçak (bu TF kanal ≥2σ)": (T.cz.to_numpy() <= -2, T.cz.to_numpy() >= 2),
         "T3 hacim patlaması (bu TF ≥1.5)": (T.vr.to_numpy() >= 1.5, T.vr.to_numpy() >= 1.5)}
    out = {k: lift(y, m, days, grp) for k, m in H.items()}
    terc = pd.Series(ctx.dvol.to_numpy()).groupby(grp).transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)).to_numpy()
    mb, ms = H["T1 gerilme pusulası"]
    out["T4 T1 vol tertili"] = {f"tertil{q}": lift(y, (mb & (terc == q), ms & (terc == q)), days, grp).get("fark_R") for q in range(3)}
    C = conds(T.nyd, ((T.ts + pd.Timedelta(minutes=int(tf[:-1]))).dt.tz_convert("America/New_York").dt.hour * 60).to_numpy(), T.wd.to_numpy(), None)
    for k in ["K1 Pazartesi SELL yok", "K5 Stres-dönüş SELL yok", "K6 Aşırı uzama BUY yok"]:
        mb, ms = C[k]
        out[f"T4 {k} vol tertili"] = {f"tertil{q}": lift(y, (mb & (terc == q), ms & (terc == q)), days, grp).get("fark_R") for q in range(3)}
    return out


if __name__ == "__main__":
    print("kanal-z doğrulama hatası:", sanity_chan())
    res = {"genel_1m": generic("all"), "bot_evreni_1m": generic("bot"), "30m_2021+": long_tf("30m"),
           "15m_2023+": long_tf("15m"), "T6_genel_1m": t6_generic(), "bot_islemleri": bot()}
    (OUT / "round2.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for sec, v in res.items():
        print(f"\n=== {sec} ===")
        for k, val in v.items():
            print(f"  {k}: {val}")
