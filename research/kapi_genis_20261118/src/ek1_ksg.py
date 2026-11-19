import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/vade_mantik_20261118/src")); sys.path.insert(0, str(ROOT / "research/son4_20261118/src"))
sys.path.insert(0, str(ROOT / "research/fitil_kesisim_20261118/src"))
import vm, ek2_sonra as E2, hp
import ksg_dogrulama as KD, ksg_ek2 as KE
CAL = E2.cal; ex = vm.expiries(CAL, "fri3"); kser = pd.Series(vm.days_to(CAL, ex), index=CAL)
feeds = {"MT5_NAS100": KD.mt5_m30("NAS100"), "H1_NAS100_2016_18": hp.h1_bars(), "EET30": KE.bars("EET30")[0], "NQ_5m": KE.bars("NQ")[0],
         "MT5_US500": KD.mt5_m30("US500", "2018-06-01"), "MT5_US30": KD.mt5_m30("US30"), "MT5_US2000": KD.mt5_m30("US2000")}
out, pool = {}, []
for nm, b in feeds.items():
    t = KD.ksg_m30(b).rename(columns={"net_bp": "net"})
    if t.empty:
        out[nm] = {"n": 0, "not": "09:30 barı yok (H1)"}; print(nm, out[nm]); continue
    t["d"] = pd.to_datetime(t.d)
    if nm == "H1_NAS100_2016_18": t = t[t.d <= "2018-04-30"]
    if nm == "MT5_NAS100": t = t[t.d >= "2018-05-01"]
    t = t.reset_index(drop=True); m = np.isin(kser.reindex(t.d).values, [0, 1, 2])
    out[nm] = vm.diff(t, m, seed=5)
    if nm in ("MT5_NAS100", "H1_NAS100_2016_18", "MT5_US500", "MT5_US30", "MT5_US2000"): pool.append((t, m))
    print(nm, out[nm])
out["havuz_ortusmesiz"] = vm.zpool(pool); print("havuz", out["havuz_ortusmesiz"])
Path(__file__).resolve().parents[1].joinpath("results/ek1_ksg.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
