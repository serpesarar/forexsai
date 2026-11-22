"""USDHKD vekil adayları: HK/Çin endeksleri, ETF'ler, USDX, altın, HK hisseleri — kutudan salt-okuma D1+H1. EMİR YOK."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fx_secim_20261113"))
import export, fx_core
SYMS = ["HK50", "CHINAH", "HSTECH", "CN50", "USDX", "EWH.US", "FXI.US", "XAUUSD", "0388.HK", "0005.HK", "XAUCNH"]
code = export.CODE.replace("__PAIRS__", json.dumps(SYMS)).replace("__TFS__", json.dumps(["D1", "H1"])).replace("__BUDGET__", "2400")
x = export.run(code, "USDHKD vekil adayları bar dışa aktarımı", 3000)
(Path(__file__).parent / "results" / "kutu_cek_vekil.json").write_text(json.dumps(x, indent=1))
print(json.dumps(x)[:2500])
fx_core.download()
