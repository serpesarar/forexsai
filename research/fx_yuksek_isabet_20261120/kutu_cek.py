"""Bantlı/yönetimli kurların MT5 barlarını kutudan salt-okuma çek (export.py CODE'u, yalnız sembol listesi farklı). EMİR YOK."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fx_secim_20261113"))
import export, fx_core
PAIRS = ["USDHKD", "EURDKK", "USDDKK", "USDCNH", "USDSGD", "USDAED", "EURCZK", "EURHUF", "EURPLN", "USDILS", "USDTHB"]
code = export.CODE.replace("__PAIRS__", json.dumps(PAIRS)).replace("__TFS__", json.dumps(["D1", "H1", "M15"])).replace("__BUDGET__", "2400")
x = export.run(code, "bantlı FX bar dışa aktarımı", 3000)
(Path(__file__).parent / "results" / "kutu_cek.json").write_text(json.dumps(x, indent=1))
print(json.dumps(x)[:3000])
fx_core.download()
