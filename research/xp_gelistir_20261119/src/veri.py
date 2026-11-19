"""veri.py — K1 + XP işlemleri: giriş anı özellikleri (yalnız 16:00'da bilinen) + işlem sonrası fiyat yolu. python veri.py"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/son_rapor_20261118/src"))
import rapor as R  # noqa: E402
import ek_kapilar as EK  # noqa: E402

G, V, NY, FIN = R.G, R.V, R.NY, R.FIN
HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "results"
CHECK = {"c17": (0, 17, 0), "c20": (0, 20, 0), "c00": (1, 0, 0), "c04": (1, 4, 0), "c0930": (1, 9, 30), "c1200": (1, 12, 0)}


def ts(d, hh, mm) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def daily_frame(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [570, 600, 900, 930, 960], step)
    x = G._local(b, NY)
    rth = x[(x.mn >= 570) & (x.mn < 960)]
    g = rth.groupby("day")
    dp = dp.join(pd.DataFrame({"tw": g.c.mean(), "hi": g.h.max(), "lo": g.l.min(), "lo_mn": g.apply(lambda z: z.mn.values[np.argmin(z.l.values)])}))
    if "v" in b.columns:
        dp = dp.join(g.v.sum().rename("vol"))
    dp = dp[[d.weekday() < 5 and G.nyse_ok(d) for d in dp.index]]
    dp.index = pd.to_datetime(dp.index)
    return dp


def entry_features(b: pd.DataFrame, step: int, ev: set | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Gün başına 16:00 NY'de bilinen özellikler + K1 bayrağı (çıkışı belli olmayan son sinyaller dahil).
    `ev` verilmezse araştırma olay takvimi (R.event_days) kullanılır; ileri gölge kendi takvimini geçer."""
    dp = daily_frame(b, step)
    cal = R.trading_calendar()
    k, a = R.cycle(cal)
    ev = R.event_days() if ev is None else ev
    vr = EK.vix_ratio()
    vix = pd.read_parquet(ROOT / "research/qs03_akis_takvim_20261111/data/VIX.parquet")
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)
    vix.index = pd.to_datetime(vix.index).tz_localize(None).normalize()
    vixp = vix.Close.shift(1)
    q = pd.read_parquet(ROOT / "research/nq_yapi2_20261118/data/QQQ.parquet")
    q.index = pd.to_datetime(q.index).tz_localize(None).normalize()
    qv = (q.Volume / q.Volume.shift(1).rolling(20).mean())
    p = dp.o960
    r1 = p / p.shift(1) - 1
    feats = pd.DataFrame(index=dp.index)
    feats["gun_ret"] = r1 * 1e4
    feats["seans_ret"] = (p / dp.o570 - 1) * 1e4
    feats["son_saat"] = (p / dp.o900 - 1) * 1e4
    feats["son_yarim"] = (p / dp.o930 - 1) * 1e4
    feats["ilk_yarim_saat"] = (dp.o600 / dp.o570 - 1) * 1e4
    feats["twap_uz"] = (p / dp.tw - 1) * 1e4
    feats["bosluk"] = (dp.o570 / p.shift(1) - 1) * 1e4
    feats["aralik"] = (dp.hi / dp.lo - 1) * 1e4
    feats["kapanis_konum"] = (p - dp.lo) / (dp.hi - dp.lo)
    feats["dip_saati"] = dp.lo_mn / 60.0
    feats["r5"] = (p / p.shift(5) - 1) * 1e4
    feats["r20"] = (p / p.shift(20) - 1) * 1e4
    feats["rsi2"] = EK.rsi2(p)
    for n in (20, 50, 200):
        feats[f"sma{n}_uz"] = (p / p.rolling(n).mean() - 1) * 1e4
    feats["rv20"] = np.log(p).diff().rolling(20).std() * np.sqrt(252) * 100
    feats["aralik_oran"] = feats.aralik / feats.aralik.shift(1).rolling(20).mean()
    feats["zirve_uz"] = (p / p.rolling(252, min_periods=60).max() - 1) * 1e4
    feats["vix"] = vixp.reindex(dp.index).values
    feats["vix_deg"] = (vix.Close / vix.Close.shift(1) - 1).shift(1).reindex(dp.index).values * 100
    feats["vix_vix3m"] = vr.reindex(dp.index).values
    feats["qqq_hacim_oran"] = qv.reindex(dp.index).values
    if "vol" in dp:
        feats["mt5_hacim_oran"] = dp.vol / dp.vol.shift(1).rolling(20).mean()
    feats["gun"] = dp.index.dayofweek
    feats["ay"] = dp.index.month
    feats["opex_k"] = k.reindex(dp.index).values
    feats["opex_a"] = a.reindex(dp.index).values
    feats["olay"] = dp.index.isin(ev).astype(int)
    feats["sess_dun"] = feats.seans_ret.shift(1)
    # K1 tanımı
    k1 = (feats.twap_uz <= -50) & (feats.son_saat < 0)
    feats["K1"] = k1
    feats["K1_dun"] = k1.shift(1).fillna(False).astype(bool)
    feats["K1_son10"] = k1.shift(1).rolling(10, min_periods=1).sum()
    return dp, feats, k1


def build(b: pd.DataFrame, step: int, name: str, ev: set | None = None) -> pd.DataFrame:
    dp, feats, k1 = entry_features(b, step, ev)
    p = dp.o960
    # işlemler + yol
    t, o, h, l, sp = b.t.values, b.o.values, b.h.values, b.l.values, b.sp.values
    tol = 300 if step == 60 else step
    days = list(dp.index)
    rows = []
    for i, d in enumerate(days[:-1]):
        if not k1.iloc[i]:
            continue
        pc = p.iloc[i]
        prev, ex = pc, None
        for j in range(i + 1, min(i + 6, len(days))):
            pj = p.iloc[j]
            if not np.isfinite(pj):
                break
            if pj > prev or j == min(i + 5, len(days) - 1):
                ex = days[j]
                break
            prev = pj
        if ex is None:
            continue
        u0, ux = ts(d, 16, 0), ts(ex, 16, 0)
        i0, ix = int(np.searchsorted(t, u0)), int(np.searchsorted(t, ux))
        if i0 >= len(t) or t[i0] - u0 > tol or ix >= len(t) or t[ix] - ux > tol:
            continue
        ask = o[i0] + sp[i0]
        cal_days = (ex - d).days
        net = (o[ix] / ask - 1) * 1e4 - FIN * cal_days
        seg_l, seg_h = l[i0:ix], h[i0:ix]
        jm = int(np.argmin(seg_l))
        rec = {"d": d, "cikis": ex, "tutus_gun": days.index(ex) - i, "net": net, "giris": ask,
               "mae": (seg_l.min() / ask - 1) * 1e4, "mfe": (seg_h.max() / ask - 1) * 1e4,
               "mae_saat": (t[i0 + jm] - t[i0]) / 3600.0}
        nd = days[i + 1]
        for cn, (off, hh, mm) in CHECK.items():
            dd = d if off == 0 else nd
            hh2 = hh
            uu = ts(dd, hh2, mm) if not (off == 1 and hh < 9 and cn in ("c00", "c04")) else ts(dd, hh, mm)
            kk = int(np.searchsorted(t, uu))
            rec[cn] = (o[kk] / ask - 1) * 1e4 if kk < ix and kk < len(t) and abs(t[kk] - uu) <= 3 * 3600 else np.nan
        # gün gün 16:00 yolu
        for jj in range(1, 6):
            if i + jj < len(days):
                rec[f"g{jj}"] = (p.iloc[i + jj] / ask - 1) * 1e4 if days[i + jj] <= ex else np.nan
        rows.append({**rec, **feats.iloc[i].to_dict()})
    df = pd.DataFrame(rows)
    df["donem"] = np.where(df.d <= pd.Timestamp("2021-10-31"), "KESIF", "TEST")
    df["besleme"] = name
    return df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    feeds = {"DUKA_NDX": (G.ndx_bars(), 60)}
    for s, since in (("NAS100", None), ("US500", "2018-06-01"), ("US30", None), ("US2000", None)):
        x = pd.read_csv(ROOT / f"research/c1_turev_20261105/data/mt5/{s}_M30.csv.gz")
        b = R.KD.mt5_m30(s, since)
        sys.path.insert(0, str(ROOT / "research/ndx_tf_yapilandirma_20261117/src"))
        import kaynak  # noqa: E402
        tv = pd.Series(x.v.values, index=kaynak.server_to_utc(x["t"].to_numpy()).astype(np.int64))
        tv = tv[~tv.index.duplicated()]
        b["v"] = tv.reindex(b.t.values).values
        feeds[f"MT5_{s}"] = (b, 1800)
    allf = []
    for nm, (b, st) in feeds.items():
        df = build(b, st, nm)
        allf.append(df)
        print(nm, len(df), "işlem", round(df.net.mean(), 1), flush=True)
    pd.concat(allf, ignore_index=True).to_parquet(OUT / "islemler.parquet")


if __name__ == "__main__":
    main()
