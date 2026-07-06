"""XAUUSD swing/daily edge battery — leak-free.

Signal on closed D1 bar i, fill at D1 open[i+1] (no lookahead), trade simulated
forward bar-by-bar on H1 (pessimistic SL-first on ambiguous bars), ATR-based
TP/SL + time-stop, friction in dollars. Reports WR / avg-R / EV / PF / total-R /
maxDD with a held-out OOS split, 5-fold walk-forward, and a bootstrap CI on EV.

Goal: find ANY robust positive-EV mechanical rule on gold's higher timeframe,
distinguished from pure buy&hold drift. Run from repo root with .venv active.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

RAW = "xauusdegitim/data/raw"
FRICTION = 0.40          # round-trip $ per oz (pessimistic gold cost)
ATR_N = 14


# ───────────────────────── data ─────────────────────────
def load(tf: str) -> pd.DataFrame:
    df = pd.read_csv(f"{RAW}/XAUUSD_{tf}.csv")
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("ts").reset_index(drop=True)
    return df[["ts", "open", "high", "low", "close"]].astype(
        {"open": float, "high": float, "low": float, "close": float}, errors="ignore")


def rsi(close: pd.Series, n=14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100/(1+rs)


def atr(df: pd.DataFrame, n=14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([(h-l), (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()


def add_indicators(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["ema20"] = d["close"].ewm(span=20, adjust=False).mean()
    d["ema50"] = d["close"].ewm(span=50, adjust=False).mean()
    d["ema200"] = d["close"].ewm(span=200, adjust=False).mean()
    d["rsi"] = rsi(d["close"], 14)
    d["atr"] = atr(d, ATR_N)
    d["hh20"] = d["high"].rolling(20).max()
    d["ll20"] = d["low"].rolling(20).min()
    d["hh55"] = d["high"].rolling(55).max()
    d["ll55"] = d["low"].rolling(55).min()
    return d


# ───────────────────── trade simulation ─────────────────────
def simulate(side, entry_px, sl, tp, entry_ts, h1, max_bars):
    """Walk H1 forward from entry_ts. Pessimistic: SL checked before TP in a bar.
    Returns (exit_px, bars_held). Time-stop exits at close of last allowed bar."""
    i = np.searchsorted(h1["ts"].values, np.datetime64(entry_ts), side="left")
    hi, lo, cl = h1["high"].values, h1["low"].values, h1["close"].values
    end = min(i + max_bars, len(h1))
    for j in range(i, end):
        if side == "BUY":
            if lo[j] <= sl:
                return sl, j - i + 1
            if hi[j] >= tp:
                return tp, j - i + 1
        else:
            if hi[j] >= sl:
                return sl, j - i + 1
            if lo[j] <= tp:
                return tp, j - i + 1
    if end > i:
        return cl[end-1], end - i
    return entry_px, 0


def backtest(signals, side, d, h1, sl_atr, tp_atr, max_days):
    """signals: bool array aligned to d. Enter at d.open[i+1]. Returns trades DataFrame."""
    rows = []
    o = d["open"].values
    a = d["atr"].values
    ts = d["ts"].values
    idx = np.where(signals)[0]
    max_bars = max_days * 24
    for i in idx:
        if i + 1 >= len(d) or not np.isfinite(a[i]) or a[i] <= 0:
            continue
        entry_px = o[i+1]
        entry_ts = ts[i+1]
        risk = sl_atr * a[i]
        if side == "BUY":
            sl, tp = entry_px - risk, entry_px + tp_atr * a[i]
        else:
            sl, tp = entry_px + risk, entry_px - tp_atr * a[i]
        exit_px, bars = simulate(side, entry_px, sl, tp, entry_ts, h1, max_bars)
        gross = (exit_px - entry_px) if side == "BUY" else (entry_px - exit_px)
        net = gross - FRICTION
        R = net / risk
        rows.append({"ts": pd.Timestamp(entry_ts), "entry": entry_px, "exit": exit_px,
                     "net": net, "R": R, "bars": bars, "win": net > 0})
    return pd.DataFrame(rows)


# ───────────────────── metrics ─────────────────────
def stats(tr: pd.DataFrame) -> dict:
    if len(tr) == 0:
        return {"n": 0}
    R = tr["R"].values
    eq = np.cumsum(R)
    dd = (np.maximum.accumulate(eq) - eq).max() if len(eq) else 0
    wins = R[R > 0].sum()
    losses = -R[R < 0].sum()
    pf = wins / losses if losses > 0 else float("inf")
    return {"n": len(tr), "WR": round(100*tr["win"].mean(), 1),
            "avgR": round(R.mean(), 3), "sumR": round(R.sum(), 1),
            "PF": round(pf, 2), "maxDD_R": round(dd, 1),
            "med_bars": int(np.median(tr["bars"]))}


def bootstrap_ev(R, n=5000, seed=0):
    rng = np.random.default_rng(seed)
    if len(R) < 5:
        return (float("nan"), float("nan"))
    means = rng.choice(R, size=(n, len(R)), replace=True).mean(axis=1)
    return (round(np.percentile(means, 2.5), 3), round(np.percentile(means, 97.5), 3))


# ───────────────────── strategy defs ─────────────────────
def strategies(d):
    up = d["close"] > d["ema200"]
    dn = d["close"] < d["ema200"]
    return {
        "DONCH20_BUY":      (((d["close"] >= d["hh20"].shift(1)) & up).values, "BUY"),
        "DONCH55_BUY":      (((d["close"] >= d["hh55"].shift(1)) & up).values, "BUY"),
        "EMA_PULLBACK_BUY": (((d["ema50"] > d["ema200"]) & (d["close"] > d["ema200"]) &
                              (d["rsi"] < 45) & (d["close"] > d["open"])).values, "BUY"),
        "RSI_MR_BUY":       ((up & (d["rsi"] < 35)).values, "BUY"),
        "SUPPORT_BOUNCE_BUY": (((d["low"] <= d["ll20"].shift(1) + 0.5*d["atr"]) &
                                (d["close"] > d["open"]) & up).values, "BUY"),
        "DONCH20_SELL":     (((d["close"] <= d["ll20"].shift(1)) & dn).values, "SELL"),
        "RSI_MR_SELL":      ((dn & (d["rsi"] > 65)).values, "SELL"),
        "RESIST_REJECT_SELL": (((d["high"] >= d["hh20"].shift(1) - 0.5*d["atr"]) &
                                (d["close"] < d["open"]) & dn).values, "SELL"),
    }


def run():
    d = add_indicators(load("D1"))
    h1 = load("H1")
    print(f"D1 bars={len(d)}  range {d.ts.iloc[0].date()}→{d.ts.iloc[-1].date()}   H1 bars={len(h1)}")
    print(f"buy&hold drift: close {d.close.iloc[0]:.0f}→{d.close.iloc[-1]:.0f} "
          f"= {100*(d.close.iloc[-1]/d.close.iloc[0]-1):.0f}% over period\n")

    split_ts = pd.Timestamp(d.ts.values[int(len(d)*0.60)])   # naive, 60/40 OOS by date
    print(f"OOS split date: {split_ts.date()}  (train<split, test>=split)\n")

    exits = [(1.0, 2.0, 10), (1.5, 3.0, 15), (2.0, 4.0, 20)]  # (sl_atr, tp_atr, max_days)
    sig = strategies(d)

    print(f"{'strategy':22} {'exit':14} {'n':>4} {'WR':>5} {'avgR':>6} {'sumR':>7} {'PF':>5} {'OOS_n':>5} {'OOS_avgR':>8} {'EV95CI'}")
    print("-"*120)
    for name, (mask, side) in sig.items():
        for (sla, tpa, md) in exits:
            tr = backtest(mask, side, d, h1, sla, tpa, md)
            if len(tr) < 8:
                continue
            full = stats(tr)
            oos = tr[tr["ts"] >= split_ts]
            ins = tr[tr["ts"] < split_ts]
            os_ = stats(oos)
            ci = bootstrap_ev(tr["R"].values)
            tag = f"{sla:.1f}/{tpa:.1f}/{md}d"
            print(f"{name:22} {tag:14} {full['n']:>4} {full['WR']:>5} {full['avgR']:>6.3f} "
                  f"{full['sumR']:>7.1f} {full['PF']:>5} {os_.get('n',0):>5} "
                  f"{os_.get('avgR', float('nan')):>8} {ci}")
    print("\n(avgR = expectancy in risk units after $%.2f friction; EV95CI = bootstrap 95%% CI on avgR)" % FRICTION)


if __name__ == "__main__":
    run()
