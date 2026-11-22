"""Kutuda salt-okuma: tüm sembollerin işlem modu (HKD/DKK/SGD/CNH/AED/SAR/BGN içerenler + Forex yolu). EMİR YOK."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fx_secim_20261113"))
from kutu import run
CODE = r'''import MetaTrader5 as m,json,base64,zlib
assert m.initialize(path=r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"),m.last_error()
assert m.account_info().login==61628380
o={}
keys=("HKD","DKK","SGD","CNH","CNY","AED","SAR","BGN","QAR","KWD","BHD","OMR","JOD")
for s in m.symbols_get() or []:
  if "Forex" in s.path or any(k in s.name.upper() for k in keys):
    o[s.name]=[s.path,s.trade_mode,s.spread,s.swap_long,s.swap_short]
out=base64.b64encode(zlib.compress(json.dumps(o).encode(),9)).decode()
print("WTI_DATA_BEGIN"+out+"WTI_DATA_END");m.shutdown()
'''
x = run(CODE, "sembol işlem modu salt-okuma", 600)
(Path(__file__).parent / "results" / "trade_probe.json").write_text(json.dumps(x, indent=1))
keys=("HKD","DKK","SGD","CNH","AED","SAR","BGN")
print("toplam", len(x), "işleme açık(4)", sum(v[1]==4 for v in x.values()), "kapalı(0)", sum(v[1]==0 for v in x.values()))
for k,v in sorted(x.items()):
    if any(z in k for z in keys) or v[1]!=4: print(k, v)
