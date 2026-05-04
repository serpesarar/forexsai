"""
Win-Rate Decay Analyzer — find which features change BEFORE win-rate drops.

Hypothesis: model performance degrades over time as market regime drifts.
Some features show systematic shifts (e.g. ADX trending DOWN over a 5-day
window) BEFORE win-rate also drops. If we can detect those leading-indicator
shifts, a future model can use them as priors / regularization to anticipate
its own degradation.

Method:
  1. Pull last N days of resolved signals + factors snapshot.
  2. Sort by created_at, compute ROLLING WIN-RATE in N-signal buckets.
  3. For each numeric/bucketed feature, compute its rolling MEAN/MODE in
     parallel windows.
  4. Find features whose rolling shift CORRELATES with rolling win-rate shift
     using Pearson correlation per bucket.
  5. Output: for each model, list top 10 features whose drift "leads"
     win-rate decline (negative correlation = feature increase paired with
     win-rate decrease, useful as a regime-shift early warning).

Output: xauusdegitim/win_rate_decay_report.md + decay_features.json

Run:
    python xauusdegitim/win_rate_decay_analyzer.py [--days 90] [--window-size 50]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
NOW = datetime.now(timezone.utc)


def iso(dt): return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_signals(days: int) -> pd.DataFrame:
    since = NOW - timedelta(days=days)
    rows: list[dict] = []
    with httpx.Client(timeout=60) as c:
        offset = 0
        while True:
            r = c.get(f"{URL}/rest/v1/prediction_logs", headers=HEADERS,
                      params={"select": "id,symbol,model_type,ml_direction,ml_confidence,"
                              "status,factors,created_at",
                              "created_at": f"gte.{iso(since)}",
                              "status": "in.(completed,stopped)",
                              "order": "created_at.asc",
                              "limit": "1000", "offset": str(offset)})
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < 1000 or len(rows) >= 50000:
                break
            offset += 1000
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["won"] = (df["status"] == "completed").astype(int)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df


# Numeric snapshot features whose drift is informative
NUMERIC_FACTORS = [
    "M30_rsi_14", "H1_rsi_14", "H4_rsi_14",
    "M30_adx_14", "H1_adx_14", "H4_adx_14",
    "M30_macd_hist_atr", "M30_atr_ratio_50", "M30_bb_pctb",
    "M30_dist_swing_high_30_atr", "M30_dist_swing_low_30_atr",
    "M30_consec_green", "M30_consec_red",
    "M30_chan_pct", "M30_sar_dist_atr",
    "macro_dxy_chg1d_pct", "macro_vix_chg1d_pct", "macro_us10y_chg1d_pct",
]


def parse_factors(v):
    if isinstance(v, dict): return v
    if isinstance(v, str):
        try: return json.loads(v)
        except: return {}
    return {}


def extract_numeric_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pull NUMERIC_FACTORS into wide columns. Cast to float, NaN-tolerant."""
    factors = df["factors"].apply(parse_factors)
    out = pd.DataFrame(index=df.index)
    out["created_at"] = df["created_at"]
    out["symbol"] = df["symbol"]
    out["model_type"] = df["model_type"]
    out["won"] = df["won"]
    for fac in NUMERIC_FACTORS:
        out[fac] = factors.apply(lambda f: float(f[fac]) if f.get(fac) is not None
                                  and isinstance(f.get(fac), (int, float)) else np.nan)
    return out


def rolling_win_rate(df: pd.DataFrame, window: int) -> pd.Series:
    return df["won"].rolling(window=window, min_periods=window // 2).mean() * 100


def analyze_segment(df: pd.DataFrame, segment_label: str, window: int) -> dict:
    if len(df) < window * 2:
        return {"label": segment_label, "skipped": True, "reason": f"only {len(df)} samples"}
    df = df.sort_values("created_at").reset_index(drop=True)
    wr = rolling_win_rate(df, window)
    # For each numeric feature, rolling mean
    correlations: list[dict] = []
    for fac in NUMERIC_FACTORS:
        s = df[fac]
        if s.notna().sum() < window * 2:
            continue
        roll = s.rolling(window=window, min_periods=window // 2).mean()
        # Align — both series same length
        valid = wr.notna() & roll.notna()
        if valid.sum() < 30:
            continue
        wr_v = wr[valid].values
        roll_v = roll[valid].values
        # Pearson correlation
        try:
            corr = float(np.corrcoef(wr_v, roll_v)[0, 1])
        except Exception:
            continue
        if not np.isfinite(corr):
            continue
        # Also compute the avg shift between high-wr periods and low-wr periods
        high_wr_mask = wr_v >= np.nanpercentile(wr_v, 70)
        low_wr_mask = wr_v <= np.nanpercentile(wr_v, 30)
        avg_high = float(np.nanmean(roll_v[high_wr_mask])) if high_wr_mask.any() else None
        avg_low = float(np.nanmean(roll_v[low_wr_mask])) if low_wr_mask.any() else None
        correlations.append({
            "feature": fac,
            "correlation_with_win_rate": round(corr, 3),
            "avg_when_winning": round(avg_high, 3) if avg_high is not None else None,
            "avg_when_losing": round(avg_low, 3) if avg_low is not None else None,
            "delta_winning_minus_losing": round(avg_high - avg_low, 3)
                                         if avg_high is not None and avg_low is not None else None,
        })
    correlations.sort(key=lambda c: -abs(c["correlation_with_win_rate"]))
    return {
        "label": segment_label,
        "n_signals": int(len(df)),
        "baseline_win_rate": round(float(df["won"].mean() * 100), 2),
        "rolling_window": window,
        "wr_min_max_swing_pp": round(float(wr.max() - wr.min()), 2)
                               if wr.notna().any() else 0,
        "feature_correlations": correlations[:20],
    }


def render(seg: dict) -> list[str]:
    out = [f"## {seg['label']}"]
    if seg.get("skipped"):
        out.append(f"_atlandı: {seg.get('reason')}_\n")
        return out
    out.append(f"- Sinyal sayısı: **{seg['n_signals']}**  ·  Baseline win-rate: **{seg['baseline_win_rate']}%**")
    out.append(f"- Win-rate dalga genişliği: **{seg['wr_min_max_swing_pp']:+.1f}pp** "
               f"(rolling window={seg['rolling_window']} sinyal)")
    if not seg.get("feature_correlations"):
        out.append("\n_⚠ Bu segmentteki çoğu sinyal **enriched snapshot'tan önce** loglandı — "
                   "numeric feature'lar boş. 2-3 hafta yeni veri biriktikten sonra tekrar koştur._\n")
        return out
    out.append("\n### En Yüksek Korelasyonlu Özellikler (drift ↔ win-rate)")
    out.append("| # | Özellik | Korelasyon | Kazanırken Ort | Kaybederken Ort | Delta |")
    out.append("|---|---|---|---|---|---|")
    for i, c in enumerate(seg["feature_correlations"], 1):
        marker = "🟢" if c["correlation_with_win_rate"] > 0.3 else (
                 "🔴" if c["correlation_with_win_rate"] < -0.3 else "⚪")
        out.append(f"| {i} | `{c['feature']}` {marker} | "
                   f"{c['correlation_with_win_rate']:+.3f} | "
                   f"{c.get('avg_when_winning', '—')} | "
                   f"{c.get('avg_when_losing', '—')} | "
                   f"{c.get('delta_winning_minus_losing', '—')} |")
    out.append("")
    out.append("**Yorum:**")
    pos = [c for c in seg['feature_correlations'] if c['correlation_with_win_rate'] > 0.3]
    neg = [c for c in seg['feature_correlations'] if c['correlation_with_win_rate'] < -0.3]
    if pos:
        names = ", ".join(f"`{c['feature']}`" for c in pos[:5])
        out.append(f"- 🟢 {names} ARTTIKÇA win-rate **artıyor** — model bunu yön sinyali olarak kullanmalı")
    if neg:
        names = ", ".join(f"`{c['feature']}`" for c in neg[:5])
        out.append(f"- 🔴 {names} ARTTIKÇA win-rate **düşüyor** — eğitim sırasında inverse weight olarak kullan")
    out.append("")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--window-size", type=int, default=50,
                    help="Rolling window size (signals)")
    args = ap.parse_args()

    print(f">> Fetching last {args.days} days resolved signals...")
    raw = fetch_signals(args.days)
    print(f"   {len(raw)} signals")
    if raw.empty:
        return

    print(">> Extracting numeric factor table...")
    table = extract_numeric_table(raw)

    segments: list[dict] = []
    segments.append(analyze_segment(table, "GLOBAL — tüm sembol & model", args.window_size))
    for (sym, model), grp in table.groupby(["symbol", "model_type"]):
        if len(grp) < args.window_size * 2:
            continue
        segments.append(analyze_segment(grp, f"{sym} · {model}", args.window_size))

    out_dir = Path(__file__).resolve().parent
    md = ["# Win-Rate Decay Pattern Analizi",
          f"_{iso(NOW)} — son {args.days} gün — rolling window {args.window_size}_\n",
          "**Yöntem:** Her sinyal için rolling win-rate ve rolling feature mean hesapla; "
          "Pearson korelasyon her özelliğin win-rate trendiyle birlikte hareketini ölçer.",
          "**Yorum:**",
          "- 🟢 (+0.3 üstü): feature artarken win-rate de artıyor — pozitif sinyal kaynağı",
          "- 🔴 (-0.3 altı): feature artarken win-rate düşüyor — regime-shift uyarı feature'ı, "
          "yeni eğitimde inverse weight olarak kullan",
          "- ⚪ (-0.3 / +0.3 arası): zayıf ilişki — büyük olasılıkla noise\n",
          "Yeni model eğitiminde bu içgörüleri **prior** olarak kullanabilirsin: "
          "kırmızı feature'lar regime-shift uyarısı, yeşiller ise sinyal pekiştirmesi.\n",
          "---\n"]
    for seg in segments:
        md.extend(render(seg))
        md.append("---\n")

    md_path = out_dir / "win_rate_decay_report.md"
    md_path.write_text("\n".join(md))
    json_path = out_dir / "decay_features.json"
    json_path.write_text(json.dumps({"generated_at": iso(NOW),
                                     "window_size": args.window_size,
                                     "segments": segments}, indent=2, default=str))
    print(f"\nWrote {md_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
