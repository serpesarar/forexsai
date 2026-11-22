"""Kutu salt-okuma: HK/Çin/Asya ilişkili TÜM sembollerin adı, yolu, işlem modu. EMİR YOK."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fx_secim_20261113"))
from kutu import run
CODE = r'''import MetaTrader5 as m,json,base64,zlib
assert m.initialize(path=r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"),m.last_error()
assert m.account_info().login==61628380
o={}
keys=("HK","CHINA","CN","A50","HSI","HANG","SGD","TWN","ASIA","SING","USDX","DXY","DOLLAR","TENCENT","ALIBABA","BABA","FXI","EWH")
for s in m.symbols_get() or []:
  u=(s.name+" "+s.path+" "+(s.description or "")).upper()
  if any(k in u for k in keys) and "Forex" not in s.path:
    o[s.name]=[s.path,s.trade_mode,s.spread,s.description,s.point,s.trade_contract_size,s.swap_long,s.swap_short]
out=base64.b64encode(zlib.compress(json.dumps(o).encode(),9)).decode()
print("WTI_DATA_BEGIN"+out+"WTI_DATA_END");m.shutdown()
'''
x = run(CODE, "HK/Çin vekil sembol listesi salt-okuma", 600)
(Path(__file__).parent / "results" / "proxy_probe.json").write_text(json.dumps(x, indent=1))
for k, v in sorted(x.items()): print(k, v)
