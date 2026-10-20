"""Kutuda salt-okuma: today_realized_pnl() penceresi broker saatiyle kayıyor mu? (2026-10-19 vakası)"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("box_w", HERE.parents[1] / "research" / "donus_vs_sl_20261009" / "box.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

CODE = r'''
import MetaTrader5 as m, sys
from datetime import datetime, timezone, timedelta
sys.path.insert(0, "yeni deneme")
import config
m.initialize()
base=config.MAGIC_NUMBER
mg={base,base+4,base+5,base+6,getattr(config,"VIX_REGIME_MAGIC",-1),getattr(config,"CHANNEL_REVERSION_MAGIC",-1)}
tick=m.symbol_info_tick("NAS100"); import time as T
print("broker_offset_h", round((tick.time-T.time())/3600,2))
day=datetime(2026,10,19,tzinfo=timezone.utc)
for lab,(a,b) in {"bot_penceresi(UTC)":(day,day+timedelta(days=1)),"genis":(day-timedelta(days=1),day+timedelta(days=2))}.items():
    ds=m.history_deals_get(a,b) or []
    ds=[d for d in ds if d.magic in mg and d.entry in (1,3)]
    print(lab,len(ds),round(sum(d.profit for d in ds),2))
    for d in ds:
        if abs(d.profit)>500: print("  ",d.position_id,d.magic-base,datetime.fromtimestamp(d.time,timezone.utc).strftime("%m-%d %H:%M"),round(d.profit))
# 16:32 UTC anında botun gördüğü
now=datetime(2026,10,19,16,32,tzinfo=timezone.utc)
ds=[d for d in (m.history_deals_get(day,now) or []) if d.magic in mg]
print("16:32'de gorulen (eski+yeni magic)", round(sum(d.profit+d.swap+d.commission for d in ds),2))
old={base,getattr(config,"VIX_REGIME_MAGIC",-1),getattr(config,"CHANNEL_REVERSION_MAGIC",-1)}
print("16:32'de gorulen (yalniz eski magic)", round(sum(d.profit+d.swap+d.commission for d in ds if d.magic in old),2))
'''
print(B.run_code(CODE, "pnl penceresi", timeout=300)[-3000:])
