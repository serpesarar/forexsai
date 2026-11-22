"""Kutuda salt-okuma: sabit kurların swap modu/birimi ve 3'lü gün. EMİR YOK."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fx_secim_20261113"))
from kutu import run
CODE = r'''import MetaTrader5 as m,json,base64,zlib
assert m.initialize(path=r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"),m.last_error()
assert m.account_info().login==61628380
o={}
for s in ["USDAED","USDHKD","EURUSD","USDTHB","USDCNH"]:
  m.symbol_select(s,True); i=m.symbol_info(s)
  if i is None: o[s]=None; continue
  o[s]={k:getattr(i,k) for k in ["swap_mode","swap_long","swap_short","swap_rollover3days","point","trade_tick_value","trade_contract_size","bid","ask","currency_profit","trade_mode","volume_min"]}
out=base64.b64encode(zlib.compress(json.dumps(o).encode(),9)).decode()
print("WTI_DATA_BEGIN"+out+"WTI_DATA_END");m.shutdown()
'''
x = run(CODE, "swap modu salt-okuma", 600)
(Path(__file__).parent / "results" / "swap_probe.json").write_text(json.dumps(x, indent=1))
print(json.dumps(x, indent=1))
