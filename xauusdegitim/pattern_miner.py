"""
Pattern Miner — geçmiş sinyallerden kazanan/kaybeden kombinasyonları çıkarır.

Tek seferlik (occasional) bir analiz aracı. Mevcut prediction_logs + outcome
verisini tarar, "RSI<X + ADX>Y + regime=Z → win-rate W" tarzında insanca
okunabilir kurallar üretir. Bu kuralları sen okur, modellere filter olarak
uygular ya da yeni bir model eğitirken feature/prior olarak kullanırsın.

Algoritma:
  1. Last N gün resolved signal + factors snapshot çek
  2. Feature'ları discretize et (RSI: <30, 30-50, 50-70, 70+ gibi)
  3. Decision Tree (max_depth=4, min_samples_leaf=15) eğit, target = win
  4. Tree leaf'lerini Python tarafında walk et → her leaf bir kural
  5. Filter:
        - sample_size ≥ 20
        - win_rate > 75% (KAZANAN pattern) veya < 35% (KAÇINILACAK pattern)
  6. Per (symbol, model_type, direction) ayrı + globalde de göster
  7. Markdown rapor + JSON dosya çıktı

Kullanım:
    python xauusdegitim/pattern_miner.py [--days 60] [--min-samples 20]

Çıktılar:
    xauusdegitim/pattern_report.md   — insanca okunabilir
    xauusdegitim/pattern_rules.json  — makine-okunabilir, filter spec'lere uyumlu
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.tree import DecisionTreeClassifier, _tree
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
NOW = datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

def fetch_resolved(days: int) -> pd.DataFrame:
    since = NOW - timedelta(days=days)
    rows: list[dict] = []
    with httpx.Client(timeout=60) as c:
        offset = 0
        while True:
            r = c.get(f"{URL}/rest/v1/prediction_logs", headers=HEADERS,
                      params={
                          "select": "id,symbol,model_type,ml_direction,ml_confidence,"
                                    "status,resolution_reason,factors,created_at,timeframe",
                          "created_at": f"gte.{iso(since)}",
                          "status": "in.(completed,stopped)",
                          "order": "created_at.desc",
                          "limit": "1000", "offset": str(offset),
                      })
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
    return df


# ---------------------------------------------------------------------------
# Feature engineering — flatten factors into structured columns
# ---------------------------------------------------------------------------

CONTINUOUS_BINS: dict[str, list[float]] = {
    # Each list represents bin edges. We label bins via interval notation in output.
    "rsi": [-np.inf, 30, 50, 65, 75, np.inf],
    "adx": [-np.inf, 18, 25, 35, np.inf],
    "macd_hist_atr": [-np.inf, -0.3, 0, 0.3, np.inf],
    "bb_pctb": [-np.inf, 0.2, 0.5, 0.8, np.inf],
    "ml_confidence": [-np.inf, 50, 60, 70, 80, np.inf],
    "atr_ratio": [-np.inf, 0.7, 1.0, 1.3, 1.7, np.inf],
    "consec_streak": [-np.inf, 0, 2, 4, 6, np.inf],
    "dist_swing_atr": [-np.inf, 0.3, 0.7, 1.5, np.inf],
}


def _bucket_label(value: float, bins: list[float]) -> str:
    if pd.isna(value):
        return "NA"
    for i in range(len(bins) - 1):
        if bins[i] <= value < bins[i + 1]:
            lo = "−∞" if bins[i] == -np.inf else f"{bins[i]:g}"
            hi = "+∞" if bins[i + 1] == np.inf else f"{bins[i + 1]:g}"
            return f"[{lo},{hi})"
    return "NA"


def parse_factors(v: Any) -> dict:
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try: return json.loads(v)
        except Exception: return {}
    return {}


def build_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten factors snapshot into mineable columns. Discretize continuous fields."""
    out = pd.DataFrame(index=df.index)
    out["symbol"] = df["symbol"]
    out["model_type"] = df["model_type"]
    out["direction"] = df["ml_direction"]
    out["won"] = df["won"]
    out["created_at"] = df["created_at"]

    # ml_confidence (column-level, not in factors)
    out["ml_confidence_bucket"] = df["ml_confidence"].apply(
        lambda v: _bucket_label(float(v) if v is not None else np.nan, CONTINUOUS_BINS["ml_confidence"]))

    # Walk factors per row (slow but only ~5k rows, fine)
    factors_list = df["factors"].apply(parse_factors)

    # Categorical / boolean fields (use as-is)
    cat_keys = [
        "regime_label", "mtf_trend", "volatility_regime", "session",
        "near_resistance", "near_support", "overbought", "oversold",
        "exhaustion_up", "exhaustion_down", "bb_extreme_upper", "bb_extreme_lower",
        "sar_bearish", "rsi_extreme",
        "H4_ema_stack", "H1_ema_stack", "M30_ema_stack",
        "H4_adx_label", "H1_adx_label", "M30_adx_label",
    ]
    for k in cat_keys:
        out[k] = factors_list.apply(lambda f: f.get(k))

    # Continuous fields → bucket via the right CONTINUOUS_BINS family
    cont_map = {
        # column_name : (factors_key, bin_family)
        "rsi_M30":         ("M30_rsi_14", "rsi"),
        "rsi_H1":          ("H1_rsi_14", "rsi"),
        "rsi_H4":          ("H4_rsi_14", "rsi"),
        "adx_M30":         ("M30_adx_14", "adx"),
        "adx_H1":          ("H1_adx_14", "adx"),
        "adx_H4":          ("H4_adx_14", "adx"),
        "macd_atr_M30":    ("M30_macd_hist_atr", "macd_hist_atr"),
        "bb_pctb_M30":     ("M30_bb_pctb", "bb_pctb"),
        "atr_ratio_M30":   ("M30_atr_ratio_50", "atr_ratio"),
        "dist_high_M30":   ("M30_dist_swing_high_30_atr", "dist_swing_atr"),
        "dist_low_M30":    ("M30_dist_swing_low_30_atr", "dist_swing_atr"),
        "consec_green_M30": ("M30_consec_green", "consec_streak"),
        "consec_red_M30":   ("M30_consec_red", "consec_streak"),
    }
    for col, (key, family) in cont_map.items():
        out[col] = factors_list.apply(
            lambda f: _bucket_label(
                float(f.get(key)) if f.get(key) is not None else np.nan,
                CONTINUOUS_BINS[family]))

    # Macro
    out["dxy_chg1d"] = factors_list.apply(
        lambda f: _bucket_label(
            float(f.get("macro_dxy_chg1d_pct")) if f.get("macro_dxy_chg1d_pct") is not None else np.nan,
            [-np.inf, -0.5, 0, 0.5, np.inf]))
    out["vix_chg1d"] = factors_list.apply(
        lambda f: _bucket_label(
            float(f.get("macro_vix_chg1d_pct")) if f.get("macro_vix_chg1d_pct") is not None else np.nan,
            [-np.inf, -3, 0, 3, np.inf]))

    return out


# ---------------------------------------------------------------------------
# Decision tree rule extraction
# ---------------------------------------------------------------------------

def _onehot(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Return (X_dummies, y, feature_names) skipping identifier cols."""
    skip = {"won", "symbol", "model_type", "direction", "created_at"}
    cols = [c for c in df.columns if c not in skip]
    X_raw = df[cols].fillna("NA").astype(str)
    X = pd.get_dummies(X_raw, prefix_sep="=")
    y = df[target_col]
    return X, y, list(X.columns)


def extract_tree_rules(tree: DecisionTreeClassifier, X: pd.DataFrame, y: pd.Series,
                       feature_names: list[str], min_samples: int) -> list[dict]:
    """Walk the decision tree, collect leaf-rules with TRUE sample counts.

    class_weight='balanced' makes tree_.value weighted, so we recompute wins/total
    by mapping each training sample to its leaf via tree.apply().
    """
    t = tree.tree_
    leaves = tree.apply(X.values)
    y_arr = y.values
    leaf_to_stats: dict[int, tuple[int, int]] = {}  # leaf_node_id -> (samples, wins)
    for leaf_id in np.unique(leaves):
        mask = leaves == leaf_id
        n = int(mask.sum())
        wins = int(y_arr[mask].sum())
        leaf_to_stats[int(leaf_id)] = (n, wins)

    rules: list[dict] = []

    def recurse(node: int, conditions: list[str]) -> None:
        if t.feature[node] == _tree.TREE_UNDEFINED:
            stats = leaf_to_stats.get(node)
            if not stats:
                return
            samples, wins = stats
            if samples < min_samples:
                return
            win_rate = wins / samples * 100 if samples else 0
            rules.append({
                "conditions": conditions[:],
                "samples": samples,
                "wins": wins,
                "losses": samples - wins,
                "win_rate": round(win_rate, 1),
            })
            return
        feat = feature_names[t.feature[node]]
        if "=" in feat:
            field, value = feat.split("=", 1)
            recurse(t.children_left[node], conditions + [f"{field} ≠ {value}"])
            recurse(t.children_right[node], conditions + [f"{field} = {value}"])
        else:
            thresh = t.threshold[node]
            recurse(t.children_left[node], conditions + [f"{feat} ≤ {thresh:.3f}"])
            recurse(t.children_right[node], conditions + [f"{feat} > {thresh:.3f}"])

    recurse(0, [])
    return rules


def _is_data_quality_only(conditions: list[str]) -> bool:
    """Skip rules whose conditions are ALL about NA / data presence.
    These are 'we have data → predict OK' artifacts, not strategy insights."""
    if not conditions:
        return True
    informative = 0
    for c in conditions:
        # Strip "≠ NA" / "= NA" patterns; if rule still has substance, keep it
        if "= NA" in c or "≠ NA" in c:
            continue
        informative += 1
    return informative == 0


def feature_importance(rf: RandomForestClassifier, feature_names: list[str], top: int = 15) -> list[tuple]:
    fi = rf.feature_importances_
    idx = np.argsort(fi)[::-1][:top]
    return [(feature_names[i], float(fi[i])) for i in idx if fi[i] > 0.005]


# ---------------------------------------------------------------------------
# Per-segment analysis
# ---------------------------------------------------------------------------

def analyze_segment(df: pd.DataFrame, label: str, args) -> dict:
    """Return: rules_winning, rules_avoid, importance, baseline."""
    if len(df) < args.min_segment_size:
        return {"label": label, "skipped": True, "reason": f"only {len(df)} samples"}
    X, y, names = _onehot(df, "won")
    if y.nunique() < 2:
        return {"label": label, "skipped": True, "reason": "y is constant"}

    # Decision tree
    tree = DecisionTreeClassifier(
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples,
        class_weight="balanced",
        random_state=42,
    )
    tree.fit(X, y)
    rules = extract_tree_rules(tree, X, y, names, args.min_samples)
    # Filter out data-quality-only artifacts ("just had H4 data" type rules)
    rules = [r for r in rules if not _is_data_quality_only(r["conditions"])]

    # Random Forest for feature importance
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=10,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    rf.fit(X, y)
    importance = feature_importance(rf, names)

    baseline_win_rate = round(float(y.mean()) * 100, 1)
    winning = sorted([r for r in rules if r["win_rate"] >= 75 and r["samples"] >= args.min_samples],
                     key=lambda r: -r["win_rate"])
    avoid = sorted([r for r in rules if r["win_rate"] <= 35 and r["samples"] >= args.min_samples],
                   key=lambda r: r["win_rate"])

    return {
        "label": label,
        "n": len(df),
        "baseline_win_rate": baseline_win_rate,
        "winning_patterns": winning[:10],
        "avoid_patterns": avoid[:10],
        "feature_importance": importance,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def _condition_md(c: str) -> str:
    return f"`{c}`"


def render_segment(s: dict) -> list[str]:
    out: list[str] = []
    out.append(f"## {s['label']}")
    if s.get("skipped"):
        out.append(f"_atlandı: {s.get('reason')}_\n")
        return out
    out.append(f"- Toplam çözülmüş: **{s['n']}**  ·  Baseline win-rate: **{s['baseline_win_rate']}%**\n")

    if s["winning_patterns"]:
        out.append("### 🟢 Yüksek Başarı Pattern'leri")
        out.append("> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.\n")
        for i, r in enumerate(s["winning_patterns"], 1):
            lift = round(r['win_rate'] - s['baseline_win_rate'], 1)
            lift_txt = f"+{lift}pp vs baseline" if lift >= 0 else f"{lift}pp vs baseline"
            out.append(f"**{i}. Win-rate {r['win_rate']}%** "
                       f"({r['wins']} W / {r['losses']} L = {r['samples']} trade · {lift_txt})")
            for c in r["conditions"]:
                out.append(f"   - {_condition_md(c)}")
            out.append("")
    else:
        out.append("_yüksek başarı pattern bulunamadı (75%+ eşiği)_\n")

    if s["avoid_patterns"]:
        out.append("### 🔴 Kaçınılacak Pattern'ler")
        out.append("> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.\n")
        for i, r in enumerate(s["avoid_patterns"], 1):
            lift = round(r['win_rate'] - s['baseline_win_rate'], 1)
            out.append(f"**{i}. Win-rate {r['win_rate']}%** "
                       f"({r['wins']} W / {r['losses']} L = {r['samples']} trade · {lift}pp vs baseline)")
            for c in r["conditions"]:
                out.append(f"   - {_condition_md(c)}")
            out.append("")
    else:
        out.append("_kaçınılacak pattern bulunamadı (35% altı eşiği)_\n")

    if s["feature_importance"]:
        out.append("### 📊 En Tahminlikli 15 Özellik (Random Forest)")
        out.append("| Sıra | Özellik | Önem |")
        out.append("|---|---|---|")
        for i, (name, imp) in enumerate(s["feature_importance"], 1):
            out.append(f"| {i} | `{name}` | {imp:.4f} |")
        out.append("")

    return out


def to_machine_rules(s: dict) -> list[dict]:
    """Convert mined rules into a JSON shape the orchestrator could later auto-apply."""
    machine: list[dict] = []
    for r in s.get("winning_patterns", []):
        machine.append({
            "kind": "winning_pattern", "segment": s["label"],
            "win_rate": r["win_rate"], "samples": r["samples"], "conditions": r["conditions"],
        })
    for r in s.get("avoid_patterns", []):
        machine.append({
            "kind": "avoid_pattern", "segment": s["label"],
            "win_rate": r["win_rate"], "samples": r["samples"], "conditions": r["conditions"],
        })
    return machine


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60, help="Geçmiş kaç gün taransın")
    ap.add_argument("--min-samples", type=int, default=20, help="Bir kuralın min örnek sayısı")
    ap.add_argument("--min-segment-size", type=int, default=80, help="Bir segmentte min total signals")
    ap.add_argument("--max-depth", type=int, default=4, help="Decision tree max derinlik (kural uzunluğu)")
    args = ap.parse_args()

    print(f">> Fetching last {args.days} days resolved signals...")
    raw = fetch_resolved(args.days)
    print(f"   {len(raw)} resolved rows")
    if raw.empty:
        print("   data yok, çıkıyorum.")
        return

    print(">> Building feature table...")
    feats = build_feature_table(raw)
    print(f"   feature columns: {list(feats.columns)[:10]}...  total {len(feats.columns)}")

    print(">> Running decision tree mining per segment...")
    segments: list[dict] = [analyze_segment(feats, "GLOBAL — tüm sembol & model", args)]

    # Per (symbol, model_type) — sadece yeterli örnek var ise
    for (sym, model), grp in feats.groupby(["symbol", "model_type"]):
        if len(grp) < args.min_segment_size:
            continue
        segments.append(analyze_segment(grp, f"{sym} · {model}", args))

    # Per (symbol, model_type, direction)
    for (sym, model, direction), grp in feats.groupby(["symbol", "model_type", "direction"]):
        if len(grp) < args.min_segment_size or direction not in ("BUY", "SELL"):
            continue
        segments.append(analyze_segment(grp, f"{sym} · {model} · {direction}", args))

    print(f"   {len(segments)} segments analyzed")

    # Render
    out_dir = Path(__file__).resolve().parent
    md = []
    md.append(f"# Pattern Mining Raporu")
    md.append(f"_{iso(NOW)} — son {args.days} gün — {len(raw)} resolved sinyal_\n")
    md.append("**Yöntem:** Decision Tree (max_depth={}) + Random Forest feature importance.\n"
              "Her leaf bir kural. min_samples_leaf={}, class_weight=balanced.\n".format(
                  args.max_depth, args.min_samples))
    md.append("**Yorum kılavuzu:**")
    md.append("- 🟢 Win-rate ≥ %75 = pattern güvenilir (confidence boost veya yeni feature adayı)")
    md.append("- 🔴 Win-rate ≤ %35 = pattern toksik (filter rule olarak ekle)")
    md.append("- Baseline win-rate'i her segment için ayrıca göster — relative kazanım önemli\n")
    md.append("---\n")
    for s in segments:
        md.extend(render_segment(s))
        md.append("---\n")

    # Persist
    md_path = out_dir / "pattern_report.md"
    md_path.write_text("\n".join(md))
    json_path = out_dir / "pattern_rules.json"
    json_payload = {
        "generated_at": iso(NOW),
        "days": args.days,
        "total_signals": int(len(raw)),
        "rules": [r for s in segments for r in to_machine_rules(s)],
    }
    json_path.write_text(json.dumps(json_payload, indent=2, default=str))

    print(f"\nWrote {md_path}")
    print(f"Wrote {json_path}")
    print(f"\nÖzet: {len(json_payload['rules'])} kural çıktı.")
    win_count = sum(1 for r in json_payload["rules"] if r["kind"] == "winning_pattern")
    avoid_count = sum(1 for r in json_payload["rules"] if r["kind"] == "avoid_pattern")
    print(f"  - 🟢 winning: {win_count}")
    print(f"  - 🔴 avoid: {avoid_count}")


if __name__ == "__main__":
    main()
