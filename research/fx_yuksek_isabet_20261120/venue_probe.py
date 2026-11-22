"""Kutudaki İKİNCİ terminal (C:\\Program Files\\MetaTrader 5) — salt-okuma: broker adı + taahhütlü kur sembollerinin işlem modu. EMİR YOK."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fx_secim_20261113"))
from kutu import run
CODE = r'''import MetaTrader5 as m,json,base64,zlib
assert m.initialize(path=r"C:\Program Files\MetaTrader 5\terminal64.exe"),m.last_error()
a=m.account_info()
o={"_acc":{"company":a.company,"server":a.server,"trade_mode":a.trade_mode,"currency":a.currency}}
keys=("HKD","DKK","SGD","CNH","CNY","AED","SAR","BGN","QAR","KWD","BHD","OMR","JOD")
for s in m.symbols_get() or []:
  if any(k in s.name.upper() for k in keys):
    o[s.name]=[s.path,s.trade_mode,s.spread,s.swap_long,s.swap_short,s.point,s.trade_contract_size]
out=base64.b64encode(zlib.compress(json.dumps(o).encode(),9)).decode()
print("WTI_DATA_BEGIN"+out+"WTI_DATA_END");m.shutdown()
'''
x = run(CODE, "ikinci terminal taahhütlü kur sembolleri salt-okuma", 600)
(Path(__file__).parent / "results" / "venue_probe.json").write_text(json.dumps(x, indent=1))
print(json.dumps(x, indent=1))
