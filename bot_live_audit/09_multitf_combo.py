"""
09 — MULTI-TIMEFRAME kombinasyon testi (1m + 5m + 15m birlikte).
Üretim sl_indicator_analysis.py 1m/5m/15m'i TF-önekli join edip combo_filter ile
cross-TF kural arar. Burada onu GERÇEK veride gösteriyoruz: XAU/USOIL 1m'ini
yerel olarak 5m+15m'e resample → her TF için entry göstergeleri → TF-önekli birleştir
→ combo_filter (nested-CV + placebo) cross-TF kuralları keşfeder.
(İndeksler 1m yok → canlıda data_recorder M1/M5/M15'i MT5'ten doğrudan kaydeder.)
"""
import json, sys, bisect
from datetime import datetime
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
sys.path.insert(0, str(ROOT / "yeni deneme"))
from indicators import compute_all
from combo_filter import combo_report
from discrimination import print_report

B = ROOT / "bot_live_audit" / "bars"
P = json.loads((ROOT / "bot_live_audit" / "positions.json").read_text())
def ep(s): return datetime.fromisoformat(s).timestamp()

TFS = {"1m": 60, "5m": 300, "15m": 900}

def load_1m(sym):
    rows = json.loads((B / f"{sym}_1m.json").read_text())
    return [(ep(r["candle_time"]), {"open": r["open"], "high": r["high"],
            "low": r["low"], "close": r["close"], "volume": r.get("volume", 0)}) for r in rows]

def resample(bars1m, sec):
    """1m → sec'lik barlar (tamamlanmış bucket'lar)."""
    buckets = {}
    for t, b in bars1m:
        k = t - (t % sec)
        g = buckets.get(k)
        if g is None:
            buckets[k] = {"open": b["open"], "high": b["high"], "low": b["low"],
                          "close": b["close"], "volume": b["volume"], "start": k}
        else:
            g["high"] = max(g["high"], b["high"]); g["low"] = min(g["low"], b["low"])
            g["close"] = b["close"]; g["volume"] += b["volume"]
    return [(g["start"], g) for _, g in sorted(buckets.items())]

# sembol → {tf: resampled bars}
series = {}
for sym in ["XAUUSD", "USOIL.FOREX"]:
    b1 = load_1m(sym)
    series[sym] = {"1m": b1}
    for tf, sec in TFS.items():
        if tf != "1m":
            series[sym][tf] = resample(b1, sec)

def ind_at(sym, tf, entry):
    sec = TFS[tf]
    arr = series[sym][tf]
    completed = [b for (k, b) in arr if k + sec <= entry]      # entry'den önce kapanmış
    if len(completed) < 30:
        return None
    win = completed[-320:]
    return compute_all([b["open"] for b in win], [b["high"] for b in win],
                       [b["low"] for b in win], [b["close"] for b in win],
                       [b["volume"] for b in win])

rows = []
for p in P:
    if p["symbol"] not in series or p["close_reason"] not in ("tp", "sl"):
        continue
    entry = ep(p["entry_time"])
    merged = {}
    ok = True
    for tf in TFS:
        ind = ind_at(p["symbol"], tf, entry)
        if ind is None or ind.get("insufficient"):
            ok = False; break
        for k, v in ind.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                merged[f"{tf}_{k}"] = v
    if ok and merged:
        rows.append({"win": p["close_reason"] == "tp", "ind": merged, "symbol": p["symbol"]})

print(f"{len(rows)} işlem 3 TF (1m+5m+15m) birlikte eşleşti.\n")
print_report(rows, "Multi-TF tek-gösterge ayrımı (en güçlü hangi TF/gösterge)")
print()
combo_report(rows, "XAU+USOIL  serbest (en iyi, TF fark etmez)", min_tfs=1)
print()
combo_report(rows, "XAU+USOIL  ZORUNLU cross-TF (≥2 farklı TF)", min_tfs=2)
