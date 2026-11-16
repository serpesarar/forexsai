import sys
from datetime import date
import pandas as pd
import draw, lib
m1 = lib.load_m1()
o = pd.read_parquet(lib.RESULTS / "orb_tp3_trades.parquet").set_index("d")
for s in sys.argv[1:]:
    d = date.fromisoformat(s); r = o.loc[d]
    print(draw.draw(m1, d, 570, 720, f"ORB_R{r.R:+.2f}", {"OR_hi": r.or_hi, "OR_mid": r.or_hi - r.or_w / 2}))
