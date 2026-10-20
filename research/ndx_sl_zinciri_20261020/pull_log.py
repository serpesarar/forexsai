"""Kutudaki demo_bot.log'dan 2026-10-19 NDX akışını salt-okuma çek → results/log_1019.txt."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("box_z", ROOT / "research" / "donus_vs_sl_20261009" / "box.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

CODE = r'''
import json,zlib,base64,re
KEY=re.compile(r"DAYCOMBO|RE-ENTRY|REENTRY|zarar|ZARAR|NDX.INDX:BUY|NAS100.*BUY|global tavan|DUR|halt|açıldı|ACILDI|order_send|POZ|SL |TP |kapand|ayar ",re.I)
out=[]
for l in open('yeni deneme/demo_bot.log',encoding='utf-8',errors='ignore'):
    if not l.startswith(('2026-10-19','2026-10-20 0')): continue
    if KEY.search(l): out.append(l.rstrip()[:260])
print("TICK_DATA_BEGIN"+base64.b64encode(zlib.compress("\n".join(out).encode())).decode()+"TICK_DATA_END")
'''

if __name__ == "__main__":
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    raw = B.run_code(CODE, "demo_bot.log 10-19", timeout=900)
    import base64, zlib
    blob = raw.split("TICK_DATA_BEGIN")[1].split("TICK_DATA_END")[0]
    txt = zlib.decompress(base64.b64decode(blob)).decode()
    (out / "log_1019.txt").write_text(txt, encoding="utf-8")
    print(len(txt.splitlines()), "satır")
