"""oynatici_kur.py — replay.json + destek seviyeleri (xp_destek_20261119/results/seviyeler.csv) → korku_gecesi_oynatici.html.
python oynatici_kur.py [ornek]   # ornek: her 4. işlemle küçük test sayfası"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parents[1]
FAMS = ["D5", "D5_2", "D20", "P5", "P20", "W8"]
tr = json.loads((HERE / "results/replay.json").read_text())
lv = pd.read_csv(HERE.parent / "xp_destek_20261119/results/seviyeler.csv")
lv = lv[lv.besleme == "DUKA_NDX"].assign(d=lambda z: z.d.str[:10]).set_index("d")
eslesen = 0
for t in tr:
    if t["d"] in lv.index:
        r = lv.loc[t["d"]]
        t["dest"] = {f: round(float(r[f]), 1) for f in FAMS if np.isfinite(r[f])}
        eslesen += 1
print("işlem", len(tr), "seviyesi eşleşen", eslesen)
if len(sys.argv) > 1 and sys.argv[1] == "ornek":
    tr, out = tr[::4], "ornek_oynatici.html"
else:
    out = "korku_gecesi_oynatici.html"
s = (HERE / "replay_sablon.html").read_text()
(HERE / out).write_text(s.replace("__DATA__", json.dumps(tr, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")))
