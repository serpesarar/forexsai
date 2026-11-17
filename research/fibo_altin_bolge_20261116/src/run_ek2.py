"""run_ek2.py — EK-2: C1 platosu, Fibonacci katkısı (itki anında giriş kontrolü), US30/US2000 bilgi."""
from __future__ import annotations
import itertools, json
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
import fblib as F
from run_ek1 import run, _load, YON_MT5, diff_p

def impulse_now(bars, p, smin=6.0, hold=300):
    Hh, Ll = bars.h, bars.l
    N, K, M = len(Hh), F.K_WIN, F.M_WIN
    am = sliding_window_view(Hh[:-1], K).argmax(axis=1); t = np.arange(K, N); hidx = am + (t - K)
    lw = np.full(N, -1); lw[M:] = sliding_window_view(Ll, M + 1).argmin(axis=1) + np.arange(N - M)
    ok = (am > 0) & (hidx <= t - 2) & (hidx >= M); t, hidx = t[ok], hidx[ok]; lidx = lw[hidx]
    df = pd.DataFrame({"t": t, "hidx": hidx, "lidx": lidx}).drop_duplicates(["lidx", "hidx"], keep="first")
    H, L = Hh[df.hidx.values], Ll[df.lidx.values]; R = H - L
    S = R / bars.atr[df.lidx.values]
    df = df.assign(side=1, H=H, L=L, R=R, S=S, speed=S / np.maximum(df.hidx - df.lidx, 1), plow=L, atr=bars.atr[df.t.values])
    df = df[(df.R > 0) & (df.S >= smin)]
    tr = F.resolve(F.setup_trades(df, bars, p, "L", "x1618", hold, "sig382"), p)
    return tr[tr.session == "NY"]

def main():
    p = F.load_ndx_1m(); bars = F.build_bars(p, 5, 0, "5m"); out = {}
    cand = F.detect(bars, 1); rows = []
    for pat, z, sl, tp, hold, smin in itertools.product(["none", "eng"], ["cok_sig", "sig382", "altin"], ["L", "inv"],
                                                      ["H", "x1272", "x1618", "2R"], [100, 300], [4.0, 6.0]):
        tr = F.resolve(F.setup_trades(F.signals(cand, pat, z, smin, 0.0), bars, p, sl, tp, hold, z), p)
        tr = tr[tr.session == "NY"]
        r = {"pattern": pat, "zone": z, "sl": sl, "tp": tp, "hold": hold, "smin": smin}
        for per in ["KESIF", "TEST", "KOR"]:
            g = tr[tr.period == per]; r[f"n_{per}"] = len(g); r[f"R_{per}"] = g.R.mean() if len(g) else np.nan
        rows.append(r)
    pl = pd.DataFrame(rows); pl.round(4).to_csv(F.RESULTS / "ek2_plato.csv", index=False)
    both = (pl.R_TEST > 0) & (pl.R_KOR > 0)
    out["plato"] = {"komsu": len(pl), "TEST_ve_KOR_arti_oran": float(both.mean()),
                    "uc_donem_arti_oran": float((both & (pl.R_KESIF > 0)).mean()),
                    "bolge_bazinda": pl.assign(b=both).groupby("zone").b.mean().round(3).to_dict(),
                    "tp_bazinda": pl.assign(b=both).groupby("tp").b.mean().round(3).to_dict(),
                    "oruntu_bazinda": pl.assign(b=both).groupby("pattern").b.mean().round(3).to_dict()}
    c1 = run(bars, p, "none", "sig382", 6.0, 0.0, "L", "x1618", 300)
    ctl = impulse_now(bars, p)
    out["fib_katkisi"] = {}
    for per in ["KESIF", "TEST", "KOR", None]:
        a = c1 if per is None else c1[c1.period == per]; b = ctl if per is None else ctl[ctl.period == per]
        out["fib_katkisi"][per or "TUM"] = {"C1": F.summarize(a, boot=True), "itki_aninda": F.summarize(b, boot=True),
                                            "fark": round(float(a.R.mean() - b.R.mean()), 4), "fark_P": diff_p(a, b)}
    out["us_bilgi"] = {}
    for sym in ["US30", "US2000"]:
        F.BROKER_SPREAD.setdefault("US30", 2.0); F.BROKER_SPREAD.setdefault("US2000", 0.3)
        bp = _load(YON_MT5 / f"{sym}_M5.csv.gz", sym); bb = F.build_bars(bp, 1, 0, "M5")
        tr = run(bb, bp, "none", "sig382", 6.0, 0.0, "L", "x1618", 300)
        out["us_bilgi"][sym] = {"basla": str(pd.to_datetime(bp.local[0], unit="s").date()), **F.summarize(tr, boot=True)}
    (F.RESULTS / "ek2.json").write_text(json.dumps(out, indent=1, default=str)); print(json.dumps(out, indent=1, default=str))

if __name__ == "__main__":
    main()
