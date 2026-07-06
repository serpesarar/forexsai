"""WHY do NDX/DAX let us lift win-rate but XAUUSD doesn't? Structural answer.

Indices are intraday MEAN-REVERTING (overshoot then snap back → 'buy oversold' works,
high WR). Gold is intraday TREND/DRIFT or random (no snap-back → oscillator filters
fail). We prove it on the same 1m data, resampled to M15, with the same metrics:
  - lag-1 autocorrelation of returns (NEGATIVE = mean-reverting)
  - variance ratio VR(k) (<1 mean-revert, ~1 random, >1 trend)
  - the actual edge: after RSI<30 (oversold), do prices BOUNCE? (forward return + WR)
    and after RSI>70 (overbought), do they DROP?
"""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import json, numpy as np, pandas as pd

FILES = {"NDX (NASDAQ)": "mt5_ustec_1m_bars", "DAX": "mt5_de40_1m_bars", "XAUUSD": "mt5_xauusd_1m_bars"}


def load_m15(stub):
    bars = json.load(open(f"1MDATA/{stub}.json"))["bars"]
    df = pd.DataFrame(bars)
    df["ts"] = pd.to_datetime(df["t"], unit="s", utc=True)
    df = df.set_index("ts")
    m = df.resample("15min").agg(o=("o","first"), h=("h","max"), l=("l","min"), c=("c","last")).dropna()
    return m


def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100/(1 + up/dn.replace(0, np.nan))


def var_ratio(ret, k):
    ret = ret.dropna().values
    if len(ret) < k*5: return np.nan
    v1 = np.var(ret)
    vk = np.var(pd.Series(ret).rolling(k).sum().dropna().values)
    return vk / (k * v1) if v1 > 0 else np.nan


def main():
    print(f"{'instrument':14} {'autocorr1':>10} {'VR(4)':>7} {'VR(16)':>7}   "
          f"{'oversold→fwd8':>22}  {'overbought→fwd8':>22}")
    print(f"{'':14} {'(neg=MR)':>10} {'(<1 MR)':>7} {'(<1 MR)':>7}   "
          f"{'bounceWR / mean%':>22}  {'dropWR / mean%':>22}")
    print("-"*100)
    for name, stub in FILES.items():
        m = load_m15(stub)
        c = m["c"]; ret = c.pct_change()
        ac1 = ret.autocorr(1)
        vr4, vr16 = var_ratio(ret, 4), var_ratio(ret, 16)
        r = rsi(c, 14)
        fwd8 = c.shift(-8)/c - 1                      # forward 8-bar (2h) return
        os_mask = (r < 30) & fwd8.notna()
        ob_mask = (r > 70) & fwd8.notna()
        os_wr = (fwd8[os_mask] > 0).mean()*100; os_mean = fwd8[os_mask].mean()*100
        ob_wr = (fwd8[ob_mask] < 0).mean()*100; ob_mean = fwd8[ob_mask].mean()*100
        print(f"{name:14} {ac1:>+10.3f} {vr4:>7.2f} {vr16:>7.2f}   "
              f"{os_wr:>7.1f}% / {os_mean:>+6.2f}%   {ob_wr:>9.1f}% / {ob_mean:>+6.2f}%")
    print("\nReading it:")
    print("  • NEGATIVE autocorr / VR<1  => mean-reverting => 'buy oversold, sell overbought' works (high WR).")
    print("  • bounceWR>>50% & oversold mean +  => oversold dips snap back UP (the index edge).")
    print("  • If gold shows ~0 autocorr, VR~1, bounceWR~50%  => no intraday snap-back => no WR to harvest.")


if __name__ == "__main__":
    main()
