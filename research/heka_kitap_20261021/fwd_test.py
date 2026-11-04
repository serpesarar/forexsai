"""EK-1 ileri sınama: HK-1 (30m BUY X1 bağlayıcı; SELL/1h betimsel) broker 15m→30m/1h üzerinde."""
import numpy as np
import pandas as pd

from common import OUT, SPREAD, SYMS, TF_MIN, atr, day_boot, load, run_with_placebo
from hk1_ema import maker, signals

END = {"NDX": "2026-07-14 23:59", "DAX": "2026-10-02 23:59", "XAU": "2026-09-02 23:59", "OIL": "2026-09-02 23:59"}


def fwd_bars(sym: str, tf: str) -> pd.DataFrame:
    f = pd.read_csv(OUT / f"fwd_{sym}_15m.csv", parse_dates=["ts"])
    f = f.set_index("ts").sort_index()
    r = f.resample(tf.replace("m", "min"), label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna().reset_index()
    return r


def check_axis(sym: str) -> None:
    base = load(sym, "30m").set_index("ts").close
    fw = fwd_bars(sym, "30m").set_index("ts").close
    common_ix = base.index.intersection(fw.index)
    best = {}
    for off in (-180, -60, 0, 60, 180):
        s = fw.copy(); s.index = s.index + pd.Timedelta(minutes=off)
        ix = base.index.intersection(s.index)
        best[off] = round(float((base[ix] - s[ix]).abs().median()), 3) if len(ix) else None
    print(sym, "ortak bar", len(common_ix), "medyan |fark| ofsete göre", best)


def prep(d: pd.DataFrame, tf: str) -> pd.DataFrame:
    d = d.copy()
    d["atr"] = atr(d)
    gap = d.ts.diff().shift(-1) > pd.Timedelta(minutes=3 * TF_MIN[tf])
    blk = np.cumsum(np.r_[0, gap.values[:-1].astype(int)])
    d["blk_end"] = pd.Series(np.arange(len(d))).groupby(blk).transform("max").values
    d["year"], d["hour"] = d.ts.dt.year, d.ts.dt.hour
    return d


def main() -> None:
    for s in SYMS:
        check_axis(s)
    out = []
    for tf in ["30m", "1h"]:
        for sym in SYMS:
            d = prep(fwd_bars(sym, tf), tf)
            sig, e10, e25 = signals(d)
            t = run_with_placebo(d, sig, sym, maker(d, sym, "X1", e10, e25))
            t = t[t.ts > pd.Timestamp(END[sym], tz="UTC")]
            t["tf"] = tf
            out.append(t)
    t = pd.concat(out).dropna(subset=["d"])
    t.to_csv(OUT / "fwd_hk1_trades.csv", index=False)
    for (tf, dr), g in t.groupby(["tf", "dir"]):
        per = g.groupby("sym").agg(n=("r", "size"), R=("r", "mean"), d=("d", "mean")).round(3)
        print(f"\n{tf} {'BUY' if dr > 0 else 'SELL'} n={len(g)} ortR={g.r.mean():.3f} plc={g.plc.mean():.3f} "
              f"fark={g.d.mean():.3f} P={day_boot(g):.3f} x1.5={g.r_stress.mean():.3f}")
        print(per.to_string())


if __name__ == "__main__":
    main()
