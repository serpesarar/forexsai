import json
from pathlib import Path
import numpy as np, pandas as pd
import kural as KR, ek3_kademe as K3
HERE = Path(__file__).resolve().parents[1]
D = KR.D; th = json.loads((HERE / "results/esikler_kesif.json").read_text())
def stopv(z, S, base=None):
    v = z.net.values if base is None else base
    return np.where(z.mae.values <= -S, -S - 5.0, v)
def rel(v, z):
    return K3.rel(K3.m(v, z.d.values), K3.m(z.net.values, z.d.values))
out = {}
for e in ("KESIF", "TEST"):
    for f in ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]:
        z = D[(D.besleme == f) & (D.donem == e)]
        rec = {}
        for S in (200, 250, 300, 400, 500, 600):
            rec[f"S{S}"] = rel(stopv(z, S), z)
            v4, keep = KR.apply(z, th, "V_saat+V_vix+V_olay+V_opex")
            rec[f"S{S}+P4"] = rel(np.where(keep, stopv(z, S), 0.0), z)
            ka = K3.pkg(z, 0.5, 1.5, "c04", 25.0)
            hit = z.mae.values <= -S
            rec[f"S{S}+kademeA"] = rel(np.where(hit, (0.5 + 1.5 * ((z.c04.values > 25) & np.isfinite(z.c04.values))) * (-S - 5.0), ka), z)
        out[f"{f}_{e}"] = rec
for k, v in out.items():
    print("==", k)
    for r, m in v.items(): print(f"   {r:16s} kâr× {m['kar×']:6.2f} zarar× {m['zarar×']:5.2f} kötü10× {m['kotu10×']:5.2f} DD× {m['DD×']:5.2f} en kötü {m['en_kotu']}")
(HERE / "results/ek4_stop.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
