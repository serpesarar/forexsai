"""Kutu demo_bot.log'dan iki USOIL SL girişinin karar penceresi (salt-okuma) → results/log_sl.txt.
Log saati kutu yereli (UTC−4): #405554591 2026-10-18 18:09, #406667349 2026-10-20 08:15."""
from __future__ import annotations
import base64, importlib.util, zlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("box_l", HERE.parents[1] / "research" / "donus_vs_sl_20261009" / "box.py")
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
CODE = r'''
import zlib,base64
W=[("2026-10-18 17:5","2026-10-18 18:1"),("2026-10-20 07:5","2026-10-20 08:1")]
out=[]
for l in open('yeni deneme/demo_bot.log',encoding='utf-8',errors='ignore'):
    if 'USOIL' not in l and 'SpotCrude' not in l and 'tarama' not in l: continue
    if any(l.startswith(a) or l.startswith(b) for a,b in W) or l.startswith("2026-10-18 18:0") or l.startswith("2026-10-20 08:0") or l.startswith("2026-10-20 08:1") or l.startswith("2026-10-18 18:1"):
        out.append(l.rstrip()[:400])
print("TICK_DATA_BEGIN"+base64.b64encode(zlib.compress("\n".join(out).encode())).decode()+"TICK_DATA_END")
'''
raw = B.run_code(CODE, "usoil sl log", 900)
txt = zlib.decompress(base64.b64decode(raw.split("TICK_DATA_BEGIN")[1].split("TICK_DATA_END")[0])).decode()
(HERE / "results" / "log_sl.txt").write_text(txt, encoding="utf-8")
print(len(txt.splitlines()))
