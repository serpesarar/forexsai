"""GF-18 (cross_market.py DAX kısmı) düzeltilmiş veriyle: stres×VIXhi aynı gün / ertesi gün / ayna SELL / saat plasebosu,
1h-30m-15m; orijinal ↔ düzeltilmiş. Kural ve kod aynen (cm.events / cm.exits / cm.stat / cm.hour_placebo)."""
import json, sys
from pathlib import Path
sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge")
import cross_market as cm
HERE = Path(__file__).resolve().parent; ORIG = cm.DATA
out = {}
for lab, data in (("ORJ", ORIG), ("FIX", HERE / "data_fixed")):
    cm.DATA = data
    for tf in ("1h", "30m", "15m"):
        d = cm.build_dax(tf); E = cm.events(d, "stress", "hi"); x = cm.exits(d, E)
        r = {"aynı gün": cm.stat(x, "d0"), "ertesi gün": cm.stat(x, "d1"),
             "ayna SELL aynı gün": cm.stat(cm.exits(d, E, side=-1), "d0"),
             "stres×VIXlo aynı gün": cm.stat(cm.exits(d, cm.events(d, "stress", "lo")), "d0"),
             "stressiz×VIXhi aynı gün": cm.stat(cm.exits(d, cm.events(d, "nonstress", "hi")), "d0"),
             "saat plasebosu": cm.hour_placebo(d, E)}
        out[f"{lab} DAX {tf}"] = r
        print(lab, tf, {k: (v.get("n"), v.get("ort"), v.get("P(>0)"), v.get("yıl+")) if "n" in v else v for k, v in r.items()}, flush=True)
cm.DATA = ORIG
(HERE / "results/recheck_gf18.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
