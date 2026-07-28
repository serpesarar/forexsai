"""mom_fair_test.py — momentum filtresinin ADİL sınavı (3.4 yıl).

Denetçi dersi: kural ile tabanı kıyaslarken SAAT KOMPOZİSYONU eşitlenmezse,
NDX'in gece yukarı sürüklenmesi tek başına sahte bir "seçim değeri" üretir.
Bu dosya üç kontrolü birden uygular:
  1. Gerçekçi sürtünme (1.3 puan — broker ölçümü)
  2. Saat-eşitlenmiş taban (aynı UTC saat kovalarında, aynı ağırlıkla)
  3. Hafta-bloklu bootstrap (örtüşen etiketler i.i.d. değil)
  4. Sürükleme çıkarılmış seride tekrar (kenar gerçek mi, beta mı?)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA, add_indicators, asof_features

HORIZON = 96
SPREAD = 1.3
RNG = np.random.default_rng(99)


def resample(d15, rule):
    g = (d15.set_index("ts").resample(rule, label="left", closed="left")
         .agg({"open": "first", "high": "max", "low": "min",
               "close": "last", "volume": "sum"}).dropna(subset=["open"]))
    return g.reset_index()


def demean_by_year(d):
    d = d.copy()
    lr = np.log(d["close"] / d["close"].shift(1)).fillna(0.0)
    adj = lr - lr.groupby(d["ts"].dt.year).transform("mean")
    scale = (np.exp(adj.cumsum()) * d["close"].iloc[0]) / d["close"]
    for c in ("open", "high", "low", "close"):
        d[c] = d[c] * scale
    return d


def prep(d15):
    f15 = add_indicators(d15, "M15")[["known_at", "M15_stoch_k", "M15_dist_ema20_atr"]]
    f1h = add_indicators(resample(d15, "1h"), "H1")[
        ["known_at", "H1_atr", "H1_adx", "H1_di_diff", "H1_sar_dist_atr"]]
    b = d15[["ts", "open", "high", "low", "close"]].copy()
    for f in (f15, f1h):
        b = asof_features(b, f.assign(ts=f["known_at"])).drop(columns=["known_at"])
    return b


def run(d15, tp_a=2.0, sl_a=1.0):
    b = prep(d15)
    o, h, l, c = (b[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(b) - HORIZON - 1
    idx = np.arange(n)[:, None] + np.arange(HORIZON)[None, :]
    entry = o[:n]
    up = np.maximum.accumulate(h[idx] - entry[:, None], axis=1)
    dn = np.minimum.accumulate(l[idx] - entry[:, None], axis=1)
    end_move = c[idx[:, -1]] - entry
    x = b.iloc[:n].reset_index(drop=True)
    a = x["H1_atr"].to_numpy()
    ok = np.isfinite(a) & (a > 0)
    tp, sl = a * tp_a, a * sl_a
    hit_tp, hit_sl = up >= tp[:, None], dn <= -sl[:, None]
    a_tp, a_sl = hit_tp.any(1), hit_sl.any(1)
    t_tp = np.where(a_tp, hit_tp.argmax(1), 10**6)
    t_sl = np.where(a_sl, hit_sl.argmax(1), 10**6)
    win = a_tp & (t_tp < t_sl)
    loss = a_sl & (t_sl <= t_tp)
    opn = ~win & ~loss
    r = np.where(win, (tp - SPREAD) / sl, np.where(loss, -(sl + SPREAD) / sl, 0.0))
    r = np.where(opn, (end_move - SPREAD) / sl, r)
    x["r"], x["win"], x["ok"] = r, win, ok
    x["hour"] = x.ts.dt.hour
    x["week"] = pd.PeriodIndex(x.ts, freq="W")
    x["MOM"] = ((x.M15_stoch_k > 70) & (x.M15_dist_ema20_atr > 0.8)
                & (x.H1_sar_dist_atr > 0))
    x["K1"] = ~((x.H1_adx > 25) & (x.H1_di_diff < 0))
    return x[x.ok].reset_index(drop=True)


def hour_matched_base(x, mask):
    """Kuralın saat dağılımına göre AĞIRLIKLANDIRILMIŞ taban EV."""
    w = x[mask].hour.value_counts(normalize=True)
    base = x.groupby("hour").r.mean()
    common = w.index.intersection(base.index)
    return float((w[common] * base[common]).sum() / w[common].sum())


def week_boot(x, mask, B=3000):
    v = x[mask]
    wk = v.week.to_numpy(); vals = v.r.to_numpy()
    uw = np.unique(wk)
    by = {u: vals[wk == u] for u in uw}
    out = np.empty(B)
    for i in range(B):
        pick = RNG.choice(uw, size=len(uw), replace=True)
        out[i] = np.concatenate([by[u] for u in pick]).mean()
    return float(np.quantile(out, .05)), float(np.quantile(out, .95)), float((out > 0).mean())


def report(x, label):
    print(f"\n══════ {label} ══════")
    rows = []
    gates = {"kapı YOK": np.ones(len(x), bool), "MOM": x.MOM.to_numpy(),
             "K1": x.K1.to_numpy(), "K1 & MOM": (x.K1 & x.MOM).to_numpy()}
    for name, m in gates.items():
        if m.sum() < 500:
            continue
        ev = float(x[m].r.mean())
        hb = hour_matched_base(x, m)
        lo, hi, p = week_boot(x, m)
        rows.append(dict(kapı=name, n=int(m.sum()), kapsam=round(m.mean(), 3),
                         wr=round(float(x[m].win.mean()), 4), ev=round(ev, 4),
                         ci5=round(lo, 4), ci95=round(hi, 4), P_poz=round(p, 3),
                         saat_esit_taban=round(hb, 4),
                         saat_esit_lift=round(ev - hb, 4)))
    print(pd.DataFrame(rows).to_string(index=False))


def main():
    pd.set_option("display.width", 220)
    d = pd.read_csv(DATA / "long_15m.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    print(f"veri: {len(d)} × 15m  {d.ts.min().date()} → {d.ts.max().date()}, sürtünme {SPREAD} puan")
    for tp, sl in ((0.67, 0.92), (2.0, 1.0), (3.0, 1.0)):
        report(run(d, tp, sl), f"GERÇEK SERİ · ATR {tp}/{sl} (RR {tp/sl:.2f})")
    report(run(demean_by_year(d), 2.0, 1.0), "SÜRÜKLEME ÇIKARILMIŞ · ATR 2.0/1.0")


if __name__ == "__main__":
    main()
