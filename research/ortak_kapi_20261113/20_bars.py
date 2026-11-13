import sys; sys.path.insert(0,".")
import pandas as pd
from scripts.islem_otopsi import data as D
need={s:(pd.Timestamp("2026-06-17",tz="UTC"),pd.Timestamp("2026-11-14",tz="UTC")) for s in ["NDX.INDX","GDAXI.INDX","XAUUSD","USOIL.FOREX"]}
B=D.load_bars(list(need),need)
for s,b in B.items():
    b[["close"]].to_parquet(f"research/ortak_kapi_20261113/data/close_{s.replace('.','_')}.parquet"); print(s,len(b),b.index.min(),b.index.max())
