"""Kutu MT5 (salt-okuma): SpotCrude haftalık açılışlar (Pazar ≈22:00 UTC) — ilk 60 dk spread + Cuma kapanışına göre boşluk,
kıyas: aynı haftanın Salı 14:00–15:00 UTC'si. Broker saati = UTC+3 (tick.time broker etiketli). → results/haftalik_acilis.csv"""
from __future__ import annotations
import base64, importlib.util, io, zlib
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("box_t", HERE.parents[1] / "research" / "donus_vs_sl_20261009" / "box.py")
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
CODE = r'''
import MetaTrader5 as m, zlib, base64, statistics
from datetime import datetime, timedelta, timezone
m.initialize()
S="SpotCrude"; OFF=timedelta(hours=3)
rows=["hafta,tur,spread_med,spread_p90,ilk_fiyat,cuma_kapanis,bosluk_pct,ilk15_hareket_pct"]
d=datetime(2026,8,30,tzinfo=timezone.utc)
while d<datetime(2026,10,20,tzinfo=timezone.utc):
    for tur,a in (("acilis",d+timedelta(hours=21,minutes=55)),("sali14",d+timedelta(days=2,hours=14))):
        b=a+timedelta(minutes=65)
        t=m.copy_ticks_range(S,(a+OFF).replace(tzinfo=None),(b+OFF).replace(tzinfo=None),m.COPY_TICKS_ALL)
        if t is None or len(t)==0: continue
        sp=[x['ask']-x['bid'] for x in t if x['ask']>0 and x['bid']>0]
        first=t[0]['bid']
        fr=m.copy_ticks_range(S,(a-timedelta(days=2,hours=4)+OFF).replace(tzinfo=None),(a-timedelta(days=2)+OFF).replace(tzinfo=None),m.COPY_TICKS_ALL) if tur=="acilis" else None
        fc=fr[-1]['bid'] if fr is not None and len(fr) else float('nan')
        t15=[x['bid'] for x in t if x['time']<=t[0]['time']+15*60]
        mv=(t15[-1]/first-1)*100 if t15 else float('nan')
        rows.append(f"{d.date()},{tur},{statistics.median(sp):.4f},{sorted(sp)[int(len(sp)*.9)]:.4f},{first:.3f},{fc:.3f},{(first/fc-1)*100 if fc==fc else float('nan'):.2f},{mv:.2f}")
    d+=timedelta(days=7)
print("TICK_DATA_BEGIN"+base64.b64encode(zlib.compress("\n".join(rows).encode())).decode()+"TICK_DATA_END")
'''
raw = B.run_code(CODE, "usoil weekly open ticks", 1200)
txt = zlib.decompress(base64.b64decode(raw.split("TICK_DATA_BEGIN")[1].split("TICK_DATA_END")[0])).decode()
d = pd.read_csv(io.StringIO(txt))
d.to_csv(HERE / "results" / "haftalik_acilis.csv", index=False)
print(d.to_string())
