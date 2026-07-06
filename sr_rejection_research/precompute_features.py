"""
Faz 2 — her resolved sinyal için 5 analiz-TF'de S/R + kanal özellikleri.
Çıktı: features.jsonl  (sweep bunu okur; Supabase'e tekrar gitmez).
"""
import json, sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).parent))
import engine

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research")
TFS = ["5m", "15m", "30m", "1h", "4h"]
SYMS = ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "XAUUSD"]

sig = json.load(open(ROOT / "data" / "signals.json"))
by_sym = defaultdict(list)
for s in sig:
    if s.get("ml_entry_price") and s.get("ml_direction") in ("BUY", "SELL") and s["symbol"] in SYMS:
        by_sym[s["symbol"]].append(s)

out = open(ROOT / "data" / "features.jsonl", "w")
total = covered = 0
for sym in SYMS:
    sigs = by_sym[sym]
    states = {tf: engine.precompute(sym, tf) for tf in TFS}
    n_ok = 0
    for s in sigs:
        total += 1
        ep = datetime.fromisoformat(s["created_at"]).timestamp()
        price = float(s["ml_entry_price"])
        feats = {}
        for tf in TFS:
            try:
                f = engine.features_at(states[tf], ep, price)
            except Exception:
                f = None
            if f:
                feats[tf] = f
        if not feats:
            continue
        covered += 1; n_ok += 1
        rec = {"model": s["model_type"], "symbol": sym,
               "dir": s["ml_direction"], "win": s["status"] == "completed",
               "tf_sig": s.get("timeframe"), "t": s["created_at"][:16], "f": feats}
        out.write(json.dumps(rec) + "\n")
    print(f"  {sym}: {n_ok}/{len(sigs)} sinyal özellikli")
out.close()
print(f"TOPLAM: {covered}/{total} sinyal özellik aldı → features.jsonl")
