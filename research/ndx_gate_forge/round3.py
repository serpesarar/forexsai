"""Tur 3 — PROTOCOL_3.md: V1 kovalama endeksi, V2 M15 karşıtlığı, V3 teyitsiz kapitülasyon alımı."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, DATA, ROOT, load_1m, simulate, atr, block_boot
from evaluate import load
from features import _last_complete, map_asof
from final_candidates import lift
from round2 import tf_feats
from long_data import load_long, macro
import daylevel_trades as dt


def tf_dir(b: pd.DataFrame, tf: int, dec_t: np.ndarray) -> np.ndarray:
    """Diğer ajanın m{tf}_dir tanımı: kapanış>EMA20 ve EMA20 3 bar yükselen → +1; ayna −1; yoksa 0."""
    s = _last_complete(b[["ts", "t", "open", "high", "low", "close", "volume"]], tf)
    ema = s.close.ewm(span=20, adjust=False, min_periods=20).mean()
    v = np.where((s.close > ema) & (ema > ema.shift(3)), 1, np.where((s.close < ema) & (ema < ema.shift(3)), -1, 0)).astype(float)
    v[ema.isna().to_numpy()] = np.nan
    return map_asof(dec_t, s.avail.to_numpy(), v, tf * 60 * 3)


def chase(side: int, cz: np.ndarray, mdir: np.ndarray, price: np.ndarray, pdh: np.ndarray, pdl: np.ndarray,
          stress: np.ndarray, euph: np.ndarray) -> np.ndarray:
    if side == -1:
        c = [cz <= -1, mdir == -1, price < pdl, stress]
    else:
        c = [cz >= 1, mdir == 1, price > pdh, euph]
    return np.sum(np.vstack([np.nan_to_num(x.astype(float)) for x in c]), axis=0)


def day_flags(nyd: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    x = dt.day_conditions(nyd, pd.Series(np.zeros(len(nyd)), index=nyd.index), pd.Series(np.zeros(len(nyd)), index=nyd.index))
    stress = ((x.ndx_ret1 <= -.015) | (x.ndx_ret5 <= -.04)).to_numpy()
    euph = ((x.ndx_ret1 >= .015) | (x.ndx_ret5 >= .04)).to_numpy()
    return stress, euph


# ───────────────────────── V1 / V2: genel 1m ─────────────────────────
def v1_generic() -> dict:
    b = load_1m()
    d = load(1)
    dec = b.t.to_numpy()[d.i.to_numpy()] + 60
    nyd = pd.to_datetime(d.ny_date)
    stress, euph = day_flags(nyd)
    vix = pd.read_parquet(DATA / "feat2.parquet", columns=["vix"]).iloc[d.i.to_numpy()].reset_index(drop=True).vix.to_numpy()
    tq = d.utc_h.between(15, 17).to_numpy()
    ub = (vix >= 18.4) & (d.h1_trend.to_numpy() > 0) & (d.pos4.to_numpy() <= .6) & ~tq
    us = (vix < 18.4) & (d.h1_trend.to_numpy() < 0) & (d.pos4.to_numpy() >= .4) & ~tq
    days, per = d.ny_date.to_numpy(), d.period.to_numpy()
    price, pdh, pdl = d.price.to_numpy(), d.pdh.to_numpy(), d.pdl.to_numpy()
    out = {}
    for lab, (tfc, tfd) in {"V1 (5m kanal, M15)": (5, 15), "V1-TF (15m kanal, M60)": (15, 60)}.items():
        cz, _ = tf_feats(b, tfc, dec)
        md = tf_dir(b, tfd, dec)
        cs = chase(-1, cz, md, price, pdh, pdl, stress, euph)
        cb = chase(1, cz, md, price, pdh, pdl, stress, euph)
        for uni, (UB, US) in {"genel": (np.ones(len(d), bool), np.ones(len(d), bool)), "bot_evreni": (ub, us)}.items():
            y = {}
            for s, u in [("B", UB), ("S", US)]:
                v = d[f"R_G80_{s}"].where(u)
                y[s] = (v - v.groupby([d.period, d.utc_h]).transform("mean")).to_numpy()
            z = np.zeros(len(d), bool)
            rec = {}
            for k in range(5):
                rec[f"SELL kovalama={k}"] = lift(y, (z, (cs == k) & US), days, per)
                rec[f"BUY kovalama={k}"] = lift(y, ((cb == k) & UB, z), days, per)
            for thr in (2, 3):
                rec[f"KAPI kovalama≥{thr} (iki yön)"] = lift(y, ((cb >= thr) & UB, (cs >= thr) & US), days, per)
                rec[f"KAPI kovalama≥{thr} (yalnız SELL)"] = lift(y, (z, (cs >= thr) & US), days, per)
            out[f"{lab} | {uni}"] = rec
        if tfd == 15:
            y = {}
            for s, u in [("B", ub), ("S", us)]:
                v = d[f"R_G80_{s}"].where(u)
                y[s] = (v - v.groupby([d.period, d.utc_h]).transform("mean")).to_numpy()
            out["V2 M15 zaten hizalı SELL (bot evreni)"] = lift(y, (np.zeros(len(d), bool), (md == -1) & us), days, per)
            out["V2 M15 zaten hizalı BUY (bot evreni)"] = lift(y, ((md == 1) & ub, np.zeros(len(d), bool)), days, per)
    return out


# ───────────────────────── V1 / V2: bot işlemleri ─────────────────────────
def v1_bot() -> dict:
    t = pd.read_csv(ROOT / "nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv")
    bx = pd.read_csv(DATA / "box_trades_40d.csv")
    bx = bx[bx.symbol == "NAS100"]
    t = pd.concat([t, bx[~bx.position_id.isin(t.position_id)]], ignore_index=True)
    t["ot"] = pd.to_datetime(t.open_time_utc, utc=True)
    t["pts"] = t.profit / t.volume
    t["dec"] = t.ot.dt.floor("min").astype(str) + t.direction
    g = t.groupby("dec").agg(ot=("ot", "first"), side=("direction", "first"), pts=("pts", "mean"), usd=("profit", "sum"),
                             op=("open_price", "first"), magic=("magic", "first")).reset_index()
    b = load_1m()
    dec = g.ot.astype("int64").to_numpy() // 10**9
    f1 = pd.read_parquet(DATA / "feat_tf1.parquet", columns=["pdh", "pdl"])
    k = np.searchsorted(b.t.to_numpy() + 60, dec, side="right") - 1
    pdh, pdl = f1.pdh.to_numpy()[k], f1.pdl.to_numpy()[k]
    ny = g.ot.dt.tz_convert("America/New_York")
    stress, euph = day_flags(pd.to_datetime(ny.dt.date))
    out = {"_toplam": {"karar": len(g), "puan/karar": round(g.pts.mean(), 2)}}
    for lab, (tfc, tfd) in {"V1": (5, 15), "V1-TF": (15, 60)}.items():
        cz, _ = tf_feats(b, tfc, dec)
        md = tf_dir(b, tfd, dec)
        sell = (g.side == "SELL").to_numpy()
        cs = chase(-1, cz, md, g.op.to_numpy(), pdh, pdl, stress, euph)
        cb = chase(1, cz, md, g.op.to_numpy(), pdh, pdl, stress, euph)
        c = np.where(sell, cs, cb)
        tab = g.assign(c=c).groupby(["side", "c"]).agg(n=("pts", "size"), gün=("ot", lambda s: s.dt.date.nunique()),
                                                         puan=("pts", "mean")).round(1)
        out[f"{lab} kovalama kovası"] = {f"{a} {int(bq)}": r.to_dict() for (a, bq), r in tab.iterrows()}
        for thr in (2, 3):
            m = c >= thr
            out[f"{lab} KAPI kovalama≥{thr}"] = {"bloklanır": int(m.sum()), "gün": int(g.ot[m].dt.date.nunique()),
                                               "bloklanan_p": round(g.pts[m].mean(), 2) if m.any() else None,
                                               "kalan_p": round(g.pts[~m].mean(), 2), "bloklanan_usd": round(g.usd[m].sum(), 0)}
        if tfd == 15:
            m = sell & (md == -1)
            out["V2 bot SELL M15 zaten aşağı"] = {"n": int(m.sum()), "p": round(g.pts[m].mean(), 2),
                                                  "diğer SELL p": round(g.pts[sell & ~m].mean(), 2)}
    return out


# ───────────────────────── V3: teyitsiz kapitülasyon alımı ─────────────────────────
def v3_1m() -> dict:
    b = load_1m()
    f1 = pd.read_parquet(DATA / "feat_tf1.parquet", columns=["pdl", "ny_min", "ny_date", "wd", "atr70"])
    nyd = pd.to_datetime(f1.ny_date)
    stress, _ = day_flags(nyd)
    win = f1.ny_min.between(180, 930).to_numpy() & (f1.wd.to_numpy() <= 3) & (b.period.to_numpy() != "")
    below = b.close.to_numpy() < f1.pdl.to_numpy()
    df = pd.DataFrame({"i": np.arange(len(b)), "day": f1.ny_date, "ev": win & below, "w": win, "stress": stress,
                       "per": b.period.to_numpy(), "nym": f1.ny_min})
    ev = df[df.ev].groupby("day").first().reset_index()           # günün İLK dip-altı kapanışı
    rng = np.random.default_rng(13)
    wins = df[df.w].groupby("day").i.apply(lambda s: s.to_numpy())
    rows = []
    for r in ev.itertuples():
        rows.append((r.i, r.day, r.per, bool(r.stress), "olay"))
        arr = wins.get(r.day)
        if arr is not None and len(arr):
            rows.append((int(rng.choice(arr)), r.day, r.per, bool(r.stress), "rastgele_saat"))
    E = pd.DataFrame(rows, columns=["i", "day", "per", "stress", "kind"])
    a70 = atr(b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy(), 70)
    D = np.clip(6 * a70[E.i], 40, 250)
    tny = f1.ny_min.to_numpy()[E.i]
    hold_close = np.maximum(955 - tny, 5)
    res = {}
    for side, sn in [(1, "BUY"), (-1, "SELL")]:
        sd = np.full(len(E), side)
        geo = {"G80": (np.full(len(E), 80.), np.full(len(E), 110.), 720),
               "GS": (D, D, 720), "GR": (2 * D, D, 720)}
        for gname, (tp, sl, hold) in geo.items():
            E[f"{sn}_{gname}"] = simulate(b, E.i.to_numpy(), sd, tp, sl, maxhold_min=hold)[0]
        # 15:55'te kapat (SL 2D felaket stopu); R birimi D
        Rc = np.full(len(E), np.nan)
        for h in np.unique(hold_close):
            m = hold_close == h
            Rc[m] = simulate(b, E.i.to_numpy()[m], sd[m], np.full(m.sum(), 1e6), 2 * D[m], maxhold_min=int(h))[0] * 2
        E[f"{sn}_close1555"] = Rc
    E.to_parquet(OUT / "v3_events.parquet")
    for col in [c for c in E.columns if c.startswith(("BUY_", "SELL_"))]:
        for lab, m in {"stres+olay": (E.kind == "olay") & E.stress, "stressiz+olay": (E.kind == "olay") & ~E.stress,
                       "stres+rastgele saat": (E.kind == "rastgele_saat") & E.stress}.items():
            x = E[m]
            per = x.groupby("per")[col].mean()
            bs = block_boot(x[col].dropna().to_numpy(), x.day[x[col].notna()].to_numpy(), 3000)
            res.setdefault(col, {})[lab] = {"n": int(x[col].notna().sum()), "EV_R": round(float(x[col].mean()), 3),
                                            "P(EV>0)": round(float(np.mean(bs > 0)), 3),
                                            "dönem+": f"{int((per > 0).sum())}/{len(per)}",
                                            "dönemler": per.round(3).to_dict()}
    return res


def v3_10y() -> dict:
    """1h, 2016-05→2026-07: stres günü ilk saatlik kapanış < önceki RTH dibi → BUY, 16:00 NY'de çık."""
    d = load_long("1h")
    ny = d.ts.dt.tz_convert("America/New_York")
    d["nyd"] = pd.to_datetime(ny.dt.date.values)
    d["nyh"] = ny.dt.hour.values
    d["wd"] = ny.dt.weekday.values
    rth = d[(d.nyh >= 9) & (d.nyh <= 15)]
    lo = rth.groupby("nyd").low.min()
    days = lo.index.to_numpy()
    k = np.searchsorted(days, d.nyd.to_numpy(), side="left") - 1
    d["pdl"] = np.where(k >= 0, lo.to_numpy()[np.maximum(k, 0)], np.nan)
    m = macro()
    full = pd.date_range("2014-01-01", "2026-12-31")
    ndx = m.NDXCASH_close.dropna()
    prev = d.nyd - pd.Timedelta(days=1)
    r1 = ndx.pct_change().reindex(full).ffill().reindex(prev).to_numpy()
    r5 = ndx.pct_change(5).reindex(full).ffill().reindex(prev).to_numpy()
    vol = ndx.pct_change().rolling(20).std().reindex(full).ffill().reindex(prev).to_numpy()
    d["stress"] = (r1 <= -.015) | (r5 <= -.04)
    d["dvol"] = vol
    close16 = d[d.nyh == 15].groupby("nyd").close.last()       # 15:00 barının kapanışı = 16:00 NY
    out = {}
    w = d[(d.nyh >= 3) & (d.nyh <= 14) & (d.wd <= 3)].copy()
    w["ev"] = w.close < w.pdl
    first = w[w.ev].groupby("nyd").head(1).copy()
    nxt = d.set_index("ts").open
    first["entry"] = nxt.reindex(first.ts + pd.Timedelta(hours=1)).to_numpy()
    first["exit"] = close16.reindex(first.nyd).to_numpy()
    first["r"] = (first.exit / first.entry - 1 - 0.00006) / first.dvol
    # kontrol: aynı günler 10:00 açılışında BUY → 16:00
    o10 = d[d.nyh == 10].set_index("nyd").open
    first["r_ctrl10"] = (close16.reindex(first.nyd).to_numpy() / o10.reindex(first.nyd).to_numpy() - 1 - .00006) / first.dvol
    first["year"] = first.nyd.dt.year
    for lab, mm in {"stres+olay": first.stress, "stressiz+olay": ~first.stress}.items():
        x = first[mm & first.r.notna()]
        py = x.groupby("year").r.mean()
        bs = block_boot(x.r.to_numpy(), x.nyd.astype(str).to_numpy(), 3000)
        out[lab] = {"gün": len(x), "ort_z×100": round(x.r.mean() * 100, 2), "P(>0)": round(float(np.mean(bs > 0)), 3),
                    "yıl+": f"{int((py > 0).sum())}/{len(py)}", "2016-20": round(x[x.year <= 2020].r.mean() * 100, 2),
                    "2021+": round(x[x.year >= 2021].r.mean() * 100, 2),
                    "kontrol 10:00 BUY aynı günler ×100": round(x.r_ctrl10.mean() * 100, 2)}
    return out


if __name__ == "__main__":
    res = {"V1_V2_genel": v1_generic(), "V1_V2_bot": v1_bot(), "V3_1m": v3_1m(), "V3_10y_1h": v3_10y()}
    (OUT / "round3.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for sec, v in res.items():
        print(f"\n=== {sec} ===")
        for k, val in v.items():
            if isinstance(val, dict) and all(isinstance(x, dict) for x in val.values()):
                print(f"  ## {k}")
                for kk, vv in val.items():
                    print(f"     {kk}: {vv}")
            else:
                print(f"  {k}: {val}")
