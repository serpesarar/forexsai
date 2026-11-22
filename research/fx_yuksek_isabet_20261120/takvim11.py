"""EK-11 takvimleri (.venv: holidays) → results/takvim11.csv: gün, gotobi, jbd, ay_sonu, fomc."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fx_secim_20261113"))
import hyp
got, jbd = hyp.gotobi_days("2010-10-08", "2026-11-12")
ms = set(hyp.last_bdays("2010-10-01", "2026-11-12"))
fo = set(pd.Timestamp(d) for d in hyp.fomc_days())
days = pd.bdate_range("2010-10-08", "2026-11-12")
pd.DataFrame({"d": days, "gotobi": [d in got for d in days], "jbd": [d in jbd for d in days],
              "ay_sonu": [d in ms for d in days], "fomc": [d in fo for d in days]}).to_csv(
    Path(__file__).resolve().parent / "results" / "takvim11.csv", index=False)
print(len(days), len(got), len(ms), len(fo))
