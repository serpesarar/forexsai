"""
Price Action Miner — model-bağımsız, ham grafik üzerinden örüntü keşfi.

Mevcut pattern_miner.py modellerimizin sinyallerini analiz eder. Bu yeni miner
HİÇBİR MODEL ÇIKTISINA BAKMAZ — yalnızca ham OHLCV + teknik göstergeler
üzerinden örüntü mining yapar. Üç katman:

  1) SMC STRUCTURE LAYER
       - Swing pivots (HH/HL/LL/LH classification)
       - Fair Value Gaps (bullish + bearish)
       - CHoCH (Change of Character) — recent swing break against trend
       - BOS (Break of Structure) — trend continuation break
       - Order Blocks — last opposing candle before strong move
       Backend'deki smc_calculator_service.py reuse edilir.

  2) TREND LADDER LAYER (kullanıcı isteği)
       - M1/M5'te ritmik kademeli yükseliş/düşüş tespiti
       - Linreg R² ≥ 0.85 + sign-consistent returns + benzer büyüklük
       - Her ladder için BEFORE (önceki 30 bar) ve AFTER (sonraki 30 bar) condition
         analizi → "ladder oluşmadan önce hangi koşullar var?", "ladder sonrası
         devam mı reverse mi?"

  3) GENERIC EVENT LAYER
       - S/R cluster touches (pivot historisinden seviye keşfi)
       - Range breakout/breakdown
       - Candle patterns (bullish/bearish engulfing, doji, hammer, shooting star)
       - Gap events (open vs prev close)
       - Round number proximity
       - stumpy motif discovery (geçmişte tekrarlayan şekiller)

Çıktı:
  - chart_pattern_rules.json     (machine-readable, pattern_matcher uyumlu)
  - chart_pattern_report.md      (human-readable, segment bazlı)
  - ladder_analysis_report.md    (sadece ladder findings)

CLI:
  python xauusdegitim/price_action_miner.py [--symbols XAUUSD,NDX.INDX]
                                              [--timeframes 5m,15m,30m,1h]
                                              [--days 60]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import warnings
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.tree import DecisionTreeClassifier, _tree

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
NOW = datetime.now(timezone.utc)

# Make backend services importable for reusing smc_calculator_service
_BACKEND = ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def iso(dt): return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Data fetch — candle_cache from Supabase
# ---------------------------------------------------------------------------

def fetch_candles(symbol: str, timeframe: str, limit: int = 10000) -> pd.DataFrame:
    rows: list[dict] = []
    with httpx.Client(timeout=60) as c:
        offset = 0
        while True:
            r = c.get(f"{URL}/rest/v1/candle_cache", headers=HEADERS,
                      params={"symbol": f"eq.{symbol}", "timeframe": f"eq.{timeframe}",
                              "select": "candle_time,open,high,low,close,volume",
                              "order": "candle_time.desc",
                              "limit": "1000", "offset": str(offset)})
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < 1000 or len(rows) >= limit:
                break
            offset += 1000
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["candle_time"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Indicators (self-contained — match xauusdegitim/features.py)
# ---------------------------------------------------------------------------

def _ema(s, n): return s.ewm(span=n, adjust=False).mean()


def _atr(h, l, c, n=14):
    tr = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()


def _rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _adx(h, l, c, n=14):
    up = h.diff(); dn = -l.diff()
    plus_dm = ((up > dn) & (up > 0)).astype(float) * up
    minus_dm = ((dn > up) & (dn > 0)).astype(float) * dn
    a = _atr(h, l, c, n)
    plus_di = 100 * plus_dm.ewm(alpha=1/n, adjust=False).mean() / a
    minus_di = 100 * minus_dm.ewm(alpha=1/n, adjust=False).mean() / a
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1/n, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Standard indicator block used as event-time context features."""
    df = df.copy()
    df["atr"] = _atr(df["high"], df["low"], df["close"], 14)
    df["rsi"] = _rsi(df["close"], 14)
    df["adx"] = _adx(df["high"], df["low"], df["close"], 14)
    df["ema20"] = _ema(df["close"], 20)
    df["ema50"] = _ema(df["close"], 50)
    df["ema200"] = _ema(df["close"], 200) if len(df) >= 200 else np.nan
    df["vol_z50"] = (df["volume"] - df["volume"].rolling(50).mean()) / df["volume"].rolling(50).std()
    df["bb_mid"] = df["close"].rolling(20).mean()
    df["bb_sd"] = df["close"].rolling(20).std()
    df["bb_width_atr"] = (df["bb_sd"] * 4) / df["atr"]
    df["body_atr"] = (df["close"] - df["open"]) / df["atr"]
    df["upper_wick_atr"] = (df["high"] - df[["close", "open"]].max(axis=1)) / df["atr"]
    df["lower_wick_atr"] = (df[["close", "open"]].min(axis=1) - df["low"]) / df["atr"]
    return df


# ---------------------------------------------------------------------------
# Layer 1 — SMC STRUCTURE
# ---------------------------------------------------------------------------

def detect_swing_pivots(df: pd.DataFrame, period: int = 5) -> list[dict]:
    """Find swing highs/lows + classify HH/HL/LL/LH."""
    h = df["high"].values
    l = df["low"].values
    pivots: list[dict] = []
    for i in range(period, len(df) - period):
        if h[i] == max(h[i - period:i + period + 1]):
            pivots.append({"idx": i, "type": "HIGH", "price": float(h[i]), "ts": df["ts"].iloc[i]})
        if l[i] == min(l[i - period:i + period + 1]):
            pivots.append({"idx": i, "type": "LOW", "price": float(l[i]), "ts": df["ts"].iloc[i]})
    pivots.sort(key=lambda p: p["idx"])
    last_high = last_low = None
    for p in pivots:
        if p["type"] == "HIGH":
            if last_high is None:
                p["structure"] = "H_FIRST"
            else:
                p["structure"] = "HH" if p["price"] > last_high["price"] else "LH"
            last_high = p
        else:
            if last_low is None:
                p["structure"] = "L_FIRST"
            else:
                p["structure"] = "HL" if p["price"] > last_low["price"] else "LL"
            last_low = p
    return pivots


def detect_fvg(df: pd.DataFrame) -> list[dict]:
    """3-bar Fair Value Gap: bullish if low[i] > high[i-2], bearish if high[i] < low[i-2]."""
    fvgs: list[dict] = []
    h = df["high"].values
    l = df["low"].values
    for i in range(2, len(df)):
        if l[i] > h[i - 2]:
            fvgs.append({
                "idx": i, "type": "bullish", "gap_top": float(l[i]),
                "gap_bottom": float(h[i - 2]),
                "size_atr": float((l[i] - h[i - 2]) / df["atr"].iloc[i])
                            if pd.notna(df["atr"].iloc[i]) else None,
                "ts": df["ts"].iloc[i],
            })
        elif h[i] < l[i - 2]:
            fvgs.append({
                "idx": i, "type": "bearish", "gap_top": float(l[i - 2]),
                "gap_bottom": float(h[i]),
                "size_atr": float((l[i - 2] - h[i]) / df["atr"].iloc[i])
                            if pd.notna(df["atr"].iloc[i]) else None,
                "ts": df["ts"].iloc[i],
            })
    return fvgs


def detect_choch_bos(swings: list[dict]) -> list[dict]:
    """Walk swing sequence — when HH chain breaks (LL forms) = CHoCH, vice versa.
    BOS = continuation break (HH after HH chain, LL after LL chain)."""
    out: list[dict] = []
    chain = None  # 'up' / 'down'
    for s in swings:
        st = s.get("structure")
        if st in ("HH", "HL"):
            if chain == "down":
                out.append({"idx": s["idx"], "type": "CHoCH_bullish",
                            "price": s["price"], "ts": s["ts"]})
                chain = "up"
            elif chain == "up" and st == "HH":
                out.append({"idx": s["idx"], "type": "BOS_bullish",
                            "price": s["price"], "ts": s["ts"]})
            else:
                chain = "up"
        elif st in ("LL", "LH"):
            if chain == "up":
                out.append({"idx": s["idx"], "type": "CHoCH_bearish",
                            "price": s["price"], "ts": s["ts"]})
                chain = "down"
            elif chain == "down" and st == "LL":
                out.append({"idx": s["idx"], "type": "BOS_bearish",
                            "price": s["price"], "ts": s["ts"]})
            else:
                chain = "down"
    return out


def detect_order_blocks(df: pd.DataFrame, swings: list[dict],
                         displacement_atr: float = 1.5) -> list[dict]:
    """Last opposing candle before a strong displacement move (≥1.5×ATR)."""
    out: list[dict] = []
    for i in range(2, len(df) - 1):
        atr = df["atr"].iloc[i]
        if pd.isna(atr) or atr <= 0:
            continue
        # Bullish OB: down candle followed by strong up displacement
        if df["close"].iloc[i] < df["open"].iloc[i]:
            future = df.iloc[i + 1:i + 4]
            if not future.empty:
                up_move = future["high"].max() - df["close"].iloc[i]
                if up_move > displacement_atr * atr:
                    out.append({"idx": i, "type": "bullish_OB",
                                "ob_low": float(df["low"].iloc[i]),
                                "ob_high": float(df["high"].iloc[i]),
                                "displacement_atr": float(up_move / atr),
                                "ts": df["ts"].iloc[i]})
        # Bearish OB
        elif df["close"].iloc[i] > df["open"].iloc[i]:
            future = df.iloc[i + 1:i + 4]
            if not future.empty:
                down_move = df["close"].iloc[i] - future["low"].min()
                if down_move > displacement_atr * atr:
                    out.append({"idx": i, "type": "bearish_OB",
                                "ob_low": float(df["low"].iloc[i]),
                                "ob_high": float(df["high"].iloc[i]),
                                "displacement_atr": float(down_move / atr),
                                "ts": df["ts"].iloc[i]})
    return out


# ---------------------------------------------------------------------------
# Layer 2 — TREND LADDER DETECTION
# ---------------------------------------------------------------------------

def detect_trend_ladders(df: pd.DataFrame, window: int = 7,
                          r2_threshold: float = 0.85,
                          min_atr_per_bar: float = 0.15) -> list[dict]:
    """A "ladder" = N consecutive bars that fit a clean linear trend AND
    move sign-consistently AND with similar magnitude per bar.

    Detection:
      - Rolling N-bar window
      - Fit linreg on closes; require R² ≥ r2_threshold (rhythmic, not noisy)
      - Require sign consistency (all returns same sign)
      - Require average move per bar ≥ min_atr_per_bar (not flat)

    Returns each ladder with: start_idx, end_idx, direction, slope_atr,
    r_squared, total_move_atr, n_bars
    """
    out: list[dict] = []
    if len(df) < window * 2:
        return out
    closes = df["close"].values
    atrs = df["atr"].values
    last_end = -1
    for start in range(window, len(df) - window):
        if start < last_end:
            continue
        end = start + window
        y = closes[start:end]
        atr_avg = float(np.nanmean(atrs[start:end]))
        if not np.isfinite(atr_avg) or atr_avg <= 0:
            continue
        x = np.arange(window)
        try:
            slope, intercept = np.polyfit(x, y, 1)
        except Exception:
            continue
        pred = slope * x + intercept
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        if ss_tot == 0:
            continue
        r2 = 1 - ss_res / ss_tot
        if r2 < r2_threshold:
            continue
        # Sign consistency
        rets = np.diff(y)
        if not (all(r > 0 for r in rets) or all(r < 0 for r in rets)):
            continue
        avg_per_bar_atr = float(abs(slope) / atr_avg)
        if avg_per_bar_atr < min_atr_per_bar:
            continue
        direction = "up" if slope > 0 else "down"
        out.append({
            "start_idx": start, "end_idx": end - 1,
            "direction": direction,
            "slope_atr": round(slope / atr_avg, 4),
            "r_squared": round(r2, 4),
            "total_move_atr": round(abs(closes[end - 1] - closes[start]) / atr_avg, 3),
            "n_bars": window,
            "start_ts": df["ts"].iloc[start],
            "end_ts": df["ts"].iloc[end - 1],
            "start_price": float(closes[start]),
            "end_price": float(closes[end - 1]),
        })
        last_end = end - 1  # avoid heavy overlap
    return out


def analyze_ladder_context(ladder: dict, df: pd.DataFrame,
                            before_bars: int = 30, after_bars: int = 30) -> dict:
    """Snapshot conditions BEFORE the ladder + outcome AFTER."""
    s, e = ladder["start_idx"], ladder["end_idx"]
    out: dict = {}

    # BEFORE — what was setting up?
    before = df.iloc[max(0, s - before_bars):s]
    if not before.empty:
        out["before_rsi_avg"] = float(before["rsi"].mean())
        out["before_rsi_last"] = float(before["rsi"].iloc[-1]) if pd.notna(before["rsi"].iloc[-1]) else None
        out["before_adx_avg"] = float(before["adx"].mean()) if before["adx"].notna().any() else None
        out["before_atr_avg"] = float(before["atr"].mean())
        out["before_volz_avg"] = float(before["vol_z50"].mean()) if before["vol_z50"].notna().any() else None
        out["before_bb_width_atr_avg"] = float(before["bb_width_atr"].mean()) if before["bb_width_atr"].notna().any() else None
        # Was there a compression (BB squeeze)?
        if before["bb_width_atr"].notna().any():
            out["before_bb_squeeze"] = bool(before["bb_width_atr"].iloc[-1] < 2.0)
        # Distance from EMA50 at start of ladder
        if pd.notna(df["ema50"].iloc[s]) and pd.notna(df["atr"].iloc[s]):
            out["start_dist_ema50_atr"] = float((df["close"].iloc[s] - df["ema50"].iloc[s]) / df["atr"].iloc[s])

    # AFTER — did it continue, reverse, consolidate?
    after = df.iloc[e:min(len(df), e + after_bars + 1)]
    if not after.empty and len(after) >= 5:
        atr_e = df["atr"].iloc[e]
        end_price = ladder["end_price"]
        if ladder["direction"] == "up":
            max_continuation = (after["high"].max() - end_price) / atr_e if atr_e > 0 else 0
            max_reversal = (end_price - after["low"].min()) / atr_e if atr_e > 0 else 0
        else:
            max_continuation = (end_price - after["low"].min()) / atr_e if atr_e > 0 else 0
            max_reversal = (after["high"].max() - end_price) / atr_e if atr_e > 0 else 0
        out["after_max_continuation_atr"] = float(max_continuation)
        out["after_max_reversal_atr"] = float(max_reversal)
        out["after_outcome"] = (
            "continued" if max_continuation > max_reversal * 1.5
            else "reversed" if max_reversal > max_continuation * 1.5
            else "consolidated"
        )

    out["ladder_direction"] = ladder["direction"]
    out["ladder_slope_atr"] = ladder["slope_atr"]
    out["ladder_r2"] = ladder["r_squared"]
    out["ladder_total_atr"] = ladder["total_move_atr"]
    out["timestamp"] = ladder["start_ts"]
    return out


def mine_ladder_rules(contexts: list[dict], min_samples: int = 10) -> dict:
    """Decision tree on ladder contexts → which preconditions predict continuation?"""
    if len(contexts) < min_samples * 2:
        return {"skipped": True, "reason": f"only {len(contexts)} ladders"}
    df = pd.DataFrame(contexts)
    df["target_continued"] = (df.get("after_outcome", "consolidated") == "continued").astype(int)
    feature_cols: list[str] = []
    bins = {
        "before_rsi_avg": [-np.inf, 30, 50, 70, np.inf],
        "before_rsi_last": [-np.inf, 30, 50, 70, np.inf],
        "before_adx_avg": [-np.inf, 18, 25, np.inf],
        "before_volz_avg": [-np.inf, -0.5, 0.5, np.inf],
        "before_bb_width_atr_avg": [-np.inf, 2.0, 4.0, np.inf],
        "start_dist_ema50_atr": [-np.inf, -1, 0, 1, np.inf],
        "ladder_slope_atr": [-np.inf, 0.2, 0.5, 1.0, np.inf],
        "ladder_total_atr": [-np.inf, 1.0, 2.5, np.inf],
    }
    for col, edges in bins.items():
        if col in df.columns:
            df[f"{col}_bucket"] = pd.cut(df[col], bins=edges, include_lowest=True).astype(str)
            feature_cols.append(f"{col}_bucket")
    df["bb_squeeze_str"] = df.get("before_bb_squeeze", False).astype(str)
    df["direction"] = df["ladder_direction"]
    feature_cols += ["bb_squeeze_str", "direction"]

    X = pd.get_dummies(df[feature_cols].fillna("NA").astype(str), prefix_sep="=")
    y = df["target_continued"]
    if y.nunique() < 2:
        return {"skipped": True, "reason": "y constant"}
    tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=min_samples,
                                   class_weight="balanced", random_state=42)
    tree.fit(X, y)
    leaves = tree.apply(X.values)
    rules: list[dict] = []
    feat_names = list(X.columns)
    t = tree.tree_

    leaf_stats = {}
    for lid in np.unique(leaves):
        mask = leaves == lid
        n = int(mask.sum())
        wins = int(y[mask].sum())
        leaf_stats[int(lid)] = (n, wins)

    def recurse(node, conds):
        if t.feature[node] == _tree.TREE_UNDEFINED:
            stats = leaf_stats.get(node)
            if not stats:
                return
            n, wins = stats
            if n < min_samples:
                return
            rules.append({
                "conditions": conds[:],
                "samples": n, "continued": wins,
                "continue_rate": round(wins / n * 100, 1),
            })
            return
        feat = feat_names[t.feature[node]]
        if "=" in feat:
            field, val = feat.split("=", 1)
            recurse(t.children_left[node], conds + [f"{field} ≠ {val}"])
            recurse(t.children_right[node], conds + [f"{field} = {val}"])
        else:
            recurse(t.children_left[node], conds + [f"{feat} ≤ 0.5"])
            recurse(t.children_right[node], conds + [f"{feat} > 0.5"])
    recurse(0, [])
    rules.sort(key=lambda r: -r["continue_rate"])
    return {
        "n_ladders": len(contexts),
        "n_continued": int(df["target_continued"].sum()),
        "n_reversed": int((df["after_outcome"] == "reversed").sum()) if "after_outcome" in df else 0,
        "baseline_continue_rate": round(float(df["target_continued"].mean() * 100), 1),
        "rules": rules,
    }


# ---------------------------------------------------------------------------
# Layer 3 — GENERIC EVENTS
# ---------------------------------------------------------------------------

def detect_candle_patterns(df: pd.DataFrame) -> list[dict]:
    """Pure-python detection of common single/2-bar patterns."""
    out: list[dict] = []
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    body = (c - o).abs()
    rng = h - l
    upper_wick = h - df[["close", "open"]].max(axis=1)
    lower_wick = df[["close", "open"]].min(axis=1) - l

    for i in range(1, len(df)):
        # Doji: body very small relative to range
        if rng.iloc[i] > 0 and body.iloc[i] / rng.iloc[i] < 0.1:
            out.append({"idx": i, "type": "doji", "ts": df["ts"].iloc[i]})
        # Hammer: small body, long lower wick, small upper
        if rng.iloc[i] > 0 and lower_wick.iloc[i] > 2 * body.iloc[i] and upper_wick.iloc[i] < body.iloc[i]:
            out.append({"idx": i, "type": "hammer", "ts": df["ts"].iloc[i]})
        # Shooting star: small body, long upper wick, small lower
        if rng.iloc[i] > 0 and upper_wick.iloc[i] > 2 * body.iloc[i] and lower_wick.iloc[i] < body.iloc[i]:
            out.append({"idx": i, "type": "shooting_star", "ts": df["ts"].iloc[i]})
        # Bullish engulfing
        if c.iloc[i] > o.iloc[i] and c.iloc[i - 1] < o.iloc[i - 1] \
                and c.iloc[i] > o.iloc[i - 1] and o.iloc[i] < c.iloc[i - 1]:
            out.append({"idx": i, "type": "engulfing_bull", "ts": df["ts"].iloc[i]})
        # Bearish engulfing
        if c.iloc[i] < o.iloc[i] and c.iloc[i - 1] > o.iloc[i - 1] \
                and c.iloc[i] < o.iloc[i - 1] and o.iloc[i] > c.iloc[i - 1]:
            out.append({"idx": i, "type": "engulfing_bear", "ts": df["ts"].iloc[i]})
    return out


def detect_breakouts(df: pd.DataFrame, lookback: int = 20) -> list[dict]:
    """Range break: close > N-bar high or < N-bar low (excluding current)."""
    out: list[dict] = []
    for i in range(lookback, len(df)):
        prev_high = df["high"].iloc[i - lookback:i].max()
        prev_low = df["low"].iloc[i - lookback:i].min()
        if df["close"].iloc[i] > prev_high:
            out.append({"idx": i, "type": "breakout_up", "ts": df["ts"].iloc[i],
                        "prev_high": float(prev_high)})
        elif df["close"].iloc[i] < prev_low:
            out.append({"idx": i, "type": "breakdown", "ts": df["ts"].iloc[i],
                        "prev_low": float(prev_low)})
    return out


def detect_sr_clusters(swings: list[dict], price_tolerance_atr: float = 0.5,
                        atr_avg: float = 0) -> list[dict]:
    """Cluster historical pivots → S/R levels with strength (touch count)."""
    if not swings or atr_avg <= 0:
        return []
    levels = sorted([s["price"] for s in swings])
    clusters: list[list[float]] = []
    tol = price_tolerance_atr * atr_avg
    for p in levels:
        if clusters and abs(p - clusters[-1][-1]) < tol:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    out = [{"price": round(float(np.mean(c)), 4), "touches": len(c),
            "strength": "strong" if len(c) >= 5 else "moderate" if len(c) >= 3 else "weak"}
           for c in clusters if len(c) >= 2]
    return sorted(out, key=lambda x: -x["touches"])[:30]


def compute_event_outcomes(events: list[dict], df: pd.DataFrame,
                            horizon_bars: int = 20) -> pd.DataFrame:
    """For each event: max favorable/adverse move + reversal/continuation tag."""
    rows: list[dict] = []
    n = len(df)
    for ev in events:
        i = ev["idx"]
        if i + 5 >= n:
            continue
        end = min(n, i + horizon_bars + 1)
        future = df.iloc[i + 1:end]
        if future.empty:
            continue
        atr_i = df["atr"].iloc[i]
        if pd.isna(atr_i) or atr_i <= 0:
            continue
        entry = float(df["close"].iloc[i])
        max_up = (future["high"].max() - entry) / atr_i
        max_down = (entry - future["low"].min()) / atr_i
        # Tag-aware "reversal" depending on event semantics
        bullish_event = ev["type"] in ("hammer", "engulfing_bull", "breakout_up", "bullish",
                                        "CHoCH_bullish", "BOS_bullish", "bullish_OB")
        bearish_event = ev["type"] in ("shooting_star", "engulfing_bear", "breakdown", "bearish",
                                        "CHoCH_bearish", "BOS_bearish", "bearish_OB")
        if bullish_event:
            outcome = "continued" if max_up > 1.0 and max_up > max_down * 1.5 \
                else "failed" if max_down > 1.0 else "neutral"
        elif bearish_event:
            outcome = "continued" if max_down > 1.0 and max_down > max_up * 1.5 \
                else "failed" if max_up > 1.0 else "neutral"
        else:
            outcome = "neutral"
        rows.append({
            "idx": i, "ts": ev.get("ts"), "type": ev["type"],
            "max_up_atr": float(max_up), "max_down_atr": float(max_down),
            "outcome": outcome,
            "rsi": float(df["rsi"].iloc[i]) if pd.notna(df["rsi"].iloc[i]) else None,
            "adx": float(df["adx"].iloc[i]) if pd.notna(df["adx"].iloc[i]) else None,
            "vol_z": float(df["vol_z50"].iloc[i]) if pd.notna(df["vol_z50"].iloc[i]) else None,
            "atr_pct": float(atr_i / entry * 100) if entry > 0 else None,
            "hour_utc": ev["ts"].hour if hasattr(ev.get("ts"), "hour") else None,
            "dow": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][ev["ts"].weekday()]
                   if hasattr(ev.get("ts"), "weekday") else None,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mining — turn events with outcomes into rules
# ---------------------------------------------------------------------------

def mine_event_rules(events_df: pd.DataFrame, segment_label: str,
                      min_samples: int = 15) -> dict:
    """For each event-type, find conditions that predict continuation."""
    if events_df.empty:
        return {"label": segment_label, "skipped": True, "reason": "no events"}
    events_df = events_df[events_df["outcome"] != "neutral"]
    if len(events_df) < min_samples * 2:
        return {"label": segment_label, "skipped": True, "reason": f"only {len(events_df)} events"}

    events_df = events_df.copy()
    events_df["target_continued"] = (events_df["outcome"] == "continued").astype(int)
    bins = {
        "rsi": [-np.inf, 30, 50, 70, np.inf],
        "adx": [-np.inf, 18, 25, np.inf],
        "vol_z": [-np.inf, -0.5, 0.5, np.inf],
        "atr_pct": [-np.inf, 0.05, 0.15, 0.4, np.inf],
    }
    for col, edges in bins.items():
        if col in events_df.columns:
            events_df[f"{col}_b"] = pd.cut(events_df[col], bins=edges,
                                            include_lowest=True).astype(str)

    feature_cols = ["type", "rsi_b", "adx_b", "vol_z_b", "atr_pct_b", "dow"]
    feature_cols = [c for c in feature_cols if c in events_df.columns]
    X = pd.get_dummies(events_df[feature_cols].fillna("NA").astype(str), prefix_sep="=")
    y = events_df["target_continued"]
    if y.nunique() < 2:
        return {"label": segment_label, "skipped": True, "reason": "y constant"}

    tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=min_samples,
                                   class_weight="balanced", random_state=42)
    tree.fit(X, y)
    leaves = tree.apply(X.values)
    feat_names = list(X.columns)
    t = tree.tree_
    leaf_stats: dict[int, tuple[int, int]] = {}
    for lid in np.unique(leaves):
        mask = leaves == lid
        n = int(mask.sum())
        wins = int(y[mask].sum())
        leaf_stats[int(lid)] = (n, wins)

    rules: list[dict] = []

    def recurse(node, conds):
        if t.feature[node] == _tree.TREE_UNDEFINED:
            stats = leaf_stats.get(node)
            if not stats:
                return
            n, wins = stats
            if n < min_samples:
                return
            rate = wins / n * 100
            rules.append({
                "conditions": conds[:],
                "samples": n, "continued": wins,
                "continue_rate": round(rate, 1),
            })
            return
        feat = feat_names[t.feature[node]]
        if "=" in feat:
            field, val = feat.split("=", 1)
            recurse(t.children_left[node], conds + [f"{field} ≠ {val}"])
            recurse(t.children_right[node], conds + [f"{field} = {val}"])
        else:
            recurse(t.children_left[node], conds + [f"{feat} ≤ 0.5"])
            recurse(t.children_right[node], conds + [f"{feat} > 0.5"])

    recurse(0, [])
    rules.sort(key=lambda r: -r["continue_rate"])

    baseline = round(float(y.mean() * 100), 1)
    high_quality = [r for r in rules if r["continue_rate"] >= 70 and r["samples"] >= min_samples]
    avoid = [r for r in rules if r["continue_rate"] <= 30 and r["samples"] >= min_samples]
    return {
        "label": segment_label,
        "n_events": int(len(events_df)),
        "baseline_continue_rate": baseline,
        "winning_patterns": high_quality[:10],
        "avoid_patterns": avoid[:10],
    }


# ---------------------------------------------------------------------------
# Stumpy motifs (optional — graceful fallback if not installed)
# ---------------------------------------------------------------------------

def find_motifs_stumpy(df: pd.DataFrame, m: int = 30, top_k: int = 5) -> list[dict]:
    try:
        import stumpy
    except ImportError:
        return []
    closes = df["close"].values.astype(np.float64)
    if len(closes) < m * 4:
        return []
    try:
        mp = stumpy.stump(closes, m=m)
        # mp[:,0] = matrix profile distance; mp[:,1] = nearest neighbor index
        # Lowest distances = strongest motifs (most repeating)
        order = np.argsort(mp[:, 0])
        motifs: list[dict] = []
        seen_idx: set[int] = set()
        for idx in order[:top_k * 5]:
            i = int(idx)
            j = int(mp[i, 1])
            if i in seen_idx or j in seen_idx:
                continue
            seen_idx.add(i); seen_idx.add(j)
            motifs.append({
                "occurrence_a": i, "occurrence_b": j,
                "distance": float(mp[i, 0]),
                "len_bars": m,
                "ts_a": df["ts"].iloc[i].isoformat() if i < len(df) else None,
                "ts_b": df["ts"].iloc[j].isoformat() if j < len(df) else None,
            })
            if len(motifs) >= top_k:
                break
        return motifs
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Per-symbol per-timeframe pipeline
# ---------------------------------------------------------------------------

@dataclass
class SymbolTfReport:
    symbol: str
    timeframe: str
    n_candles: int
    n_swings: int
    n_fvg: int
    n_choch_bos: int
    n_order_blocks: int
    n_ladders: int
    n_candle_patterns: int
    n_breakouts: int
    sr_levels: list[dict]
    ladder_analysis: dict
    event_mining: list[dict]
    motifs: list[dict]


def analyze_symbol_tf(symbol: str, timeframe: str, days: int) -> SymbolTfReport:
    print(f"\n  >> {symbol} / {timeframe}: fetching candles...")
    df = fetch_candles(symbol, timeframe, limit=10000)
    if df.empty or len(df) < 100:
        print(f"     {len(df)} candles — skipping")
        return SymbolTfReport(symbol, timeframe, len(df), 0, 0, 0, 0, 0, 0, 0, [], {}, [], [])
    df = add_indicators(df)
    print(f"     {len(df)} candles, indicators ready")

    # SMC layer
    swings = detect_swing_pivots(df, period=5)
    fvgs = detect_fvg(df)
    choch_bos = detect_choch_bos(swings)
    order_blocks = detect_order_blocks(df, swings, displacement_atr=1.5)

    # S/R clusters
    atr_avg = float(df["atr"].mean())
    sr_levels = detect_sr_clusters(swings, price_tolerance_atr=0.5, atr_avg=atr_avg)

    # Ladders (M1 / M5 focus per user request, but works on any TF)
    ladder_window = 7 if timeframe in ("1m", "5m") else 5
    ladders = detect_trend_ladders(df, window=ladder_window, r2_threshold=0.85,
                                    min_atr_per_bar=0.15)
    ladder_contexts = [analyze_ladder_context(l, df) for l in ladders]
    ladder_analysis = mine_ladder_rules(ladder_contexts, min_samples=10)

    # Generic events
    candle_patts = detect_candle_patterns(df)
    breakouts = detect_breakouts(df, lookback=20)
    smc_events = [{**e, "type": e["type"]} for e in choch_bos]
    smc_events += [{**e, "type": e["type"]} for e in order_blocks]
    smc_events += [{**f, "type": f["type"]} for f in fvgs]

    # Outcomes for each event family
    all_events_df_parts: list[pd.DataFrame] = []
    if candle_patts:
        all_events_df_parts.append(compute_event_outcomes(candle_patts, df, horizon_bars=20))
    if breakouts:
        all_events_df_parts.append(compute_event_outcomes(breakouts, df, horizon_bars=20))
    if smc_events:
        all_events_df_parts.append(compute_event_outcomes(smc_events, df, horizon_bars=30))

    if all_events_df_parts:
        all_events_df = pd.concat(all_events_df_parts, ignore_index=True)
    else:
        all_events_df = pd.DataFrame()

    event_mining: list[dict] = []
    if not all_events_df.empty:
        # Mine GLOBAL across all event types in this TF
        global_mining = mine_event_rules(all_events_df, f"{symbol}/{timeframe} · ALL EVENTS",
                                         min_samples=15)
        event_mining.append(global_mining)
        # Per event family
        for ev_type, grp in all_events_df.groupby("type"):
            if len(grp) < 30:
                continue
            event_mining.append(mine_event_rules(grp, f"{symbol}/{timeframe} · {ev_type}",
                                                  min_samples=10))

    # Motifs (stumpy)
    motifs = find_motifs_stumpy(df, m=30, top_k=5) if len(df) >= 200 else []

    return SymbolTfReport(
        symbol=symbol, timeframe=timeframe, n_candles=len(df),
        n_swings=len(swings), n_fvg=len(fvgs), n_choch_bos=len(choch_bos),
        n_order_blocks=len(order_blocks), n_ladders=len(ladders),
        n_candle_patterns=len(candle_patts), n_breakouts=len(breakouts),
        sr_levels=sr_levels, ladder_analysis=ladder_analysis,
        event_mining=event_mining, motifs=motifs,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def render_report(reports: list[SymbolTfReport]) -> str:
    out = ["# Price Action Pattern Mining Report",
           f"_{iso(NOW)}_\n",
           "Bu rapor **HİÇBİR MODELE BAKMADAN** üretilmiştir — yalnızca ham OHLCV.",
           "Üç bağımsız layer:",
           "1. **SMC Structure**: swing pivots, FVG, CHoCH, BOS, Order Blocks",
           "2. **Trend Ladders**: ritmik kademeli hareketler + öncesi/sonrası analiz",
           "3. **Generic Events**: candle patterns, breakouts, S/R touches\n",
           "---\n"]
    for r in reports:
        if r.n_candles < 100:
            continue
        out.append(f"## {r.symbol} · {r.timeframe}")
        out.append(f"- Candles: **{r.n_candles}**  ·  Swing pivots: {r.n_swings}  ·  FVG: {r.n_fvg}")
        out.append(f"- CHoCH/BOS events: {r.n_choch_bos}  ·  Order Blocks: {r.n_order_blocks}")
        out.append(f"- Trend Ladders detected: {r.n_ladders}  ·  Candle patterns: {r.n_candle_patterns}  "
                   f"·  Breakouts: {r.n_breakouts}\n")

        if r.sr_levels:
            top_sr = r.sr_levels[:8]
            out.append("### S/R Cluster Seviyeleri (top 8)")
            for s in top_sr:
                out.append(f"- {s['price']} (touches: **{s['touches']}**, {s['strength']})")
            out.append("")

        # Ladders
        la = r.ladder_analysis
        if la and not la.get("skipped"):
            out.append(f"### 🪜 Trend Ladder Analizi ({la['n_ladders']} ladder)")
            out.append(f"- Continued: {la['n_continued']}  ·  Reversed: {la.get('n_reversed', 0)}  "
                       f"·  Baseline continuation: **{la['baseline_continue_rate']}%**\n")
            high = [r for r in la.get("rules", []) if r["continue_rate"] >= 70 and r["samples"] >= 10]
            low = [r for r in la.get("rules", []) if r["continue_rate"] <= 30 and r["samples"] >= 10]
            if high:
                out.append("**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**")
                for ru in high[:5]:
                    out.append(f"- **{ru['continue_rate']}%** ({ru['continued']}/{ru['samples']})")
                    for c in ru["conditions"]:
                        out.append(f"   - `{c}`")
                out.append("")
            if low:
                out.append("**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**")
                for ru in low[:5]:
                    out.append(f"- **{ru['continue_rate']}%** ({ru['continued']}/{ru['samples']})")
                    for c in ru["conditions"]:
                        out.append(f"   - `{c}`")
                out.append("")
        elif la and la.get("skipped"):
            out.append(f"_Ladder analizi atlandı: {la.get('reason')}_\n")

        # Event mining
        for em in r.event_mining:
            if em.get("skipped"):
                continue
            if not em.get("winning_patterns") and not em.get("avoid_patterns"):
                continue
            out.append(f"### 📊 {em['label']}")
            out.append(f"- Events: {em['n_events']}  ·  Baseline continuation: **{em['baseline_continue_rate']}%**\n")
            for ru in em.get("winning_patterns", [])[:5]:
                out.append(f"  - 🟢 **{ru['continue_rate']}%** ({ru['continued']}/{ru['samples']})")
                for c in ru["conditions"]:
                    out.append(f"      - `{c}`")
            for ru in em.get("avoid_patterns", [])[:5]:
                out.append(f"  - 🔴 **{ru['continue_rate']}%** ({ru['continued']}/{ru['samples']})")
                for c in ru["conditions"]:
                    out.append(f"      - `{c}`")
            out.append("")

        if r.motifs:
            out.append("### 🔁 Stumpy Matrix Profile Motifs (en sık tekrarlayan şekiller)")
            for m in r.motifs:
                out.append(f"- mesafe={m['distance']:.4f}, len={m['len_bars']} bar, "
                           f"a={m['ts_a']}, b={m['ts_b']}")
            out.append("")
        out.append("---\n")
    return "\n".join(out)


def to_machine_rules(reports: list[SymbolTfReport]) -> list[dict]:
    rules: list[dict] = []
    for r in reports:
        # Ladder rules → win-rate semantics
        la = r.ladder_analysis
        if la and not la.get("skipped"):
            for ru in la.get("rules", []):
                if ru["samples"] < 10:
                    continue
                kind = "winning_pattern" if ru["continue_rate"] >= 75 \
                    else "avoid_pattern" if ru["continue_rate"] <= 35 \
                    else None
                if not kind:
                    continue
                rules.append({
                    "kind": kind,
                    "segment": f"{r.symbol}/{r.timeframe} · LADDER",
                    "win_rate": ru["continue_rate"],
                    "samples": ru["samples"],
                    "conditions": ru["conditions"],
                })
        # Event mining rules
        for em in r.event_mining:
            if em.get("skipped"):
                continue
            for ru in em.get("winning_patterns", []):
                if ru["samples"] < 15:
                    continue
                rules.append({
                    "kind": "winning_pattern", "segment": em["label"],
                    "win_rate": ru["continue_rate"], "samples": ru["samples"],
                    "conditions": ru["conditions"],
                })
            for ru in em.get("avoid_patterns", []):
                if ru["samples"] < 15:
                    continue
                rules.append({
                    "kind": "avoid_pattern", "segment": em["label"],
                    "win_rate": ru["continue_rate"], "samples": ru["samples"],
                    "conditions": ru["conditions"],
                })
    return rules


# ---------------------------------------------------------------------------
# Main + CLI
# ---------------------------------------------------------------------------

def run_chart_mining(symbols: list[str], timeframes: list[str],
                      days: int = 60, write_files: bool = True) -> dict:
    reports: list[SymbolTfReport] = []
    for sym in symbols:
        for tf in timeframes:
            try:
                rep = analyze_symbol_tf(sym, tf, days)
                reports.append(rep)
            except Exception as e:
                print(f"     ERROR on {sym}/{tf}: {e}")
    md = render_report(reports)
    rules = to_machine_rules(reports)

    out_dir = Path(__file__).resolve().parent
    payload = {
        "generated_at": iso(NOW),
        "symbols": symbols, "timeframes": timeframes,
        "rules_count": len(rules),
        "rules": rules,
        "report_layers": ["smc_structure", "trend_ladders", "generic_events", "motifs"],
        "totals": {
            f"{r.symbol}/{r.timeframe}": {
                "candles": r.n_candles, "swings": r.n_swings, "fvg": r.n_fvg,
                "choch_bos": r.n_choch_bos, "order_blocks": r.n_order_blocks,
                "ladders": r.n_ladders, "candle_patterns": r.n_candle_patterns,
                "breakouts": r.n_breakouts, "sr_levels": len(r.sr_levels),
                "motifs": len(r.motifs),
            } for r in reports
        },
    }
    if write_files:
        (out_dir / "chart_pattern_report.md").write_text(md)
        (out_dir / "chart_pattern_rules.json").write_text(json.dumps(payload, indent=2, default=str))
        print(f"\nWrote chart_pattern_report.md ({len(md)} bytes)")
        print(f"Wrote chart_pattern_rules.json ({len(rules)} rules)")
    return {
        "status": "ok", "rules_count": len(rules),
        "symbols": symbols, "timeframes": timeframes,
        "generated_at": payload["generated_at"],
        "totals": payload["totals"],
        "rules": rules,
    }


DEFAULT_SYMBOLS = ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]
DEFAULT_TFS = ["5m", "15m", "30m", "1h"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--timeframes", default=",".join(DEFAULT_TFS))
    ap.add_argument("--days", type=int, default=60)
    args = ap.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    print(f"Price Action Miner — symbols={symbols} timeframes={timeframes} days={args.days}")
    summary = run_chart_mining(symbols=symbols, timeframes=timeframes, days=args.days)
    print(f"\nDone. {summary['rules_count']} chart-pattern rules extracted.")


if __name__ == "__main__":
    main()
