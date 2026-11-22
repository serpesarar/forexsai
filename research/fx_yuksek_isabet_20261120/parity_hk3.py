"""hk3_shadow.step ↔ hk3.trades birebirlik: 2010–2026 USDHKD H1 üzerinde bar bar besleme."""
import logging, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "yeni deneme"))
import hk3_shadow as sh
import band, hk3

REC = []
sh._append = REC.append
x = band.load_h1("USDHKD")
pt = float(band.META["USDHKD"]["point"])
B = [{"t": int(t), "o": o, "h": h, "l": l, "c": c, "sp": float(sp)} for t, o, h, l, c, sp in zip(x.t, x.o, x.h, x.l, x.c, x.sp)]
st = {"pos": None, "last_t": B[0]["t"] - 1}
log = logging.getLogger("p")
got = []
for k in range(1, len(B) + 1):
    if st["pos"] is None:
        win = B[max(0, k - 60):k]
    else:
        i0 = next(i for i in range(k - 1, -1, -1) if B[i]["t"] == st["pos"]["t_in"])
        win = B[i0:k]
    sh.step(st, win, None, pt, log, swap_long_pts=float(band.META['USDHKD']['swap_long']))
got = [r["t_in"] for r in REC if r["kind"] == "entry"]
res = [r for r in REC if r["kind"] == "result"]
ref = hk3.trades()
ref_t = [int(pd.Timestamp(v).timestamp()) for v in x.srv.values[ref.ei.values]]
same = len(set(got) & set(ref_t))
print("gölge", len(got), "araştırma", len(ref_t), "ortak giriş", same, "yalnız gölge", sorted(set(got) - set(ref_t))[:5], "yalnız araştırma", sorted(set(ref_t) - set(got))[:5])
import core
ref_net = ref.net.values
print("gölge sonuç", len(res), "isabet %", round(100 * np.mean([r['bp_model'] > 0 for r in res]), 1),
      "ort bp (swapsız)", round(np.mean([r['bp_model'] for r in res]), 2), "| araştırma swapsız ort", round((ref.net - ref.swap).mean(), 2))
print("gölge swaplı isabet %", round(100 * np.mean([r['bp_model_swap'] > 0 for r in res]), 1), "ort", round(np.mean([r['bp_model_swap'] for r in res]), 2),
      "| araştırma swaplı", round((ref.net > 0).mean() * 100, 1), round(ref.net.mean(), 2))
