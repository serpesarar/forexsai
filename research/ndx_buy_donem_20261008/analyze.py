"""NDX BUY: son 45 gün neden iyi, öncesi neden değil? python3 research/ndx_buy_donem_20261008/analyze.py

1) piyasa: NDX dönem getirisi + KAPISIZ TABAN (ABD seansında saatte bir BUY, botun 80/110 geometrisi
   ve kazanan 1,25/3 geometrisi, yönetimsiz) — ay ay.
2) bot girişi vs aynı saatte rastgele giriş (placebo.run) — dönem dönem.
3) aile karışımı ve ay ay sonuç; 4) bootstrap güven aralığı.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from scripts.islem_otopsi import align, build, cli, data  # noqa: E402
from scripts.islem_otopsi import placebo as pl  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.stats import boot_mean_ci  # noqa: E402

SYM = "NDX.INDX"
CUT_DAYS = 45
GEOS = {"bot 80/110": (110.0, 80.0), "kazanan 137,5/240": (137.5, 240.0)}
SPREAD = 1.5
US_OPEN_UTC_H, US_CLOSE_UTC_H = 14, 20        # saat başı girişler 14:00–19:00 UTC (yaz ABD seansı)


def load():
    a = cli.parse_args(["--base-days", "200", "--no-vix", "--symbol", "NDX"])
    now = data.utc_now()
    al, bars, fps, vix, _ = cli.load_everything(a, now)
    sbs = {k: SymbolBars(k, v) for k, v in bars.items() if len(v)}
    t, _ = build.build_table(al.trades, sbs, fps, data.load_vix(now - pd.Timedelta(days=200), now), now)
    t["decision_id"] = align.assign_decisions(t)
    t = t[(t["family"] != "MANUEL")].sort_values("entry_utc").drop_duplicates("decision_id")
    cut = now - pd.Timedelta(days=CUT_DAYS)
    t["donem"] = np.where(t["entry_utc"] >= cut, "son45", "önce")
    t["ay"] = t["entry_utc"].dt.strftime("%Y-%m")
    return t, sbs[SYM], cut


def market_baseline(sb: SymbolBars, cut: pd.Timestamp) -> pd.DataFrame:
    """Kapısız taban: her işlem gününde 14..19 UTC saat başı BUY, iki geometri, yönetimsiz."""
    idx = sb.m1.index
    starts = idx[(idx.minute == 0) & (idx.hour >= US_OPEN_UTC_H) & (idx.hour < US_CLOSE_UTC_H) & (idx.dayofweek < 5)]
    rows = []
    for ts in starts:
        j = sb.pos_at(ts)
        if j + 60 >= idx.size:
            continue
        entry = float(sb.a["open"][j]) + SPREAD
        rec = {"ts": ts, "ay": ts.strftime("%Y-%m"), "donem": "son45" if ts >= cut else "önce"}
        for name, (risk, reward) in GEOS.items():
            R, k, _ = pl.simulate(sb, 1, entry, j, risk, reward, SPREAD)
            rec[name] = R * risk / 110.0 if k >= 0 else np.nan     # 110 puanlık risk birimi (aynı lot)
        rows.append(rec)
    return pd.DataFrame(rows)


def price_context(sb: SymbolBars, cut: pd.Timestamp) -> pd.DataFrame:
    c = sb.m1["close"]
    daily = c.resample("1D").last().dropna()
    rows = []
    for name, d in (("önce", daily[daily.index < cut]), ("son45", daily[daily.index >= cut])):
        r = d.pct_change().dropna()
        rows.append({"dönem": name, "başlangıç": d.iloc[0], "bitiş": d.iloc[-1], "getiri_%": 100 * (d.iloc[-1] / d.iloc[0] - 1),
                     "yükselen_gün_%": 100 * (r > 0).mean(), "günlük_vol_%": 100 * r.std(), "gün": len(d)})
    months = daily.resample("ME").last()
    rows_m = (100 * months.pct_change()).dropna().round(2)
    return pd.DataFrame(rows), rows_m


def summarise(x: pd.Series) -> str:
    lo, hi, p = boot_mean_ci(x.to_numpy(float))
    return f"ort {x.mean():+.3f}R [%95 {lo:+.2f}…{hi:+.2f}] n={len(x)} WR %{100 * (x > 0).mean():.0f}"


def main() -> None:
    t, sb, cut = load()
    buy = t[t["side"] == "NDX BUY"]
    pd.set_option("display.width", 220)
    print(f"kesim: {cut:%Y-%m-%d}\n")

    pc, pm = price_context(sb, cut)
    print("== 1a) NDX fiyat bağlamı\n", pc.round(2).to_string(index=False), "\n  aylık getiri %:", pm.to_dict())

    mb = market_baseline(sb, cut)
    print("\n== 1b) KAPISIZ TABAN (saat başı BUY, yönetimsiz, 110p risk birimi)")
    print(mb.groupby("ay")[list(GEOS)].agg(["mean", "count"]).round(3).to_string())
    print(mb.groupby("donem")[list(GEOS)].mean().round(3).to_string())

    print("\n== 2) Botun NDX BUY'ları (gerçekleşen R)")
    for k, g in buy.groupby("donem"):
        print(f"  {k}: {summarise(g['r_exit'])}")
    print(buy.groupby("ay")["r_exit"].agg(["count", "mean", "sum"]).round(2).to_string())

    p = pl.run(buy, {SYM: sb})
    p = p.merge(buy[["pid", "donem"]], on="pid")
    print("\n== 2b) Bot girişi vs aynı saat/geometri rastgele giriş (yönetimsiz)")
    print(p.groupby(["donem", "tur"])["R"].agg(["mean", "count"]).round(3).to_string())

    print("\n== 3) Aile karışımı (NDX BUY)")
    print(pd.crosstab(buy["ay"], buy["family"]).to_string())
    print(buy.groupby(["donem", "family"])["r_exit"].agg(["count", "mean"]).round(2).to_string())
    print("\n  lot:", buy.groupby("donem")["volume"].describe()[["min", "max"]].to_dict())
    print("  1h trendle hizalı payı:", buy.groupby("donem")["pre_trend_align_1h"].mean().round(2).to_dict(),
          "| VIX ort:", buy.groupby("donem")["pre_vix_prev"].mean().round(1).to_dict())
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    buy.drop(columns=[c for c in buy.columns if c.startswith("_") or c == "kart"]).to_csv(out / "ndx_buy.csv", index=False)
    mb.to_csv(out / "kapisiz_taban.csv", index=False)


if __name__ == "__main__":
    main()
