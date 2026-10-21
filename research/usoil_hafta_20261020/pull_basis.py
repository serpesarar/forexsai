"""Kutu demo_bot.log: her USOIL BUY canlı girişinden (✅ ticket) önceki son [BASIS] farkı + aynı turdaki skor satırı → results/basis.csv"""
from __future__ import annotations
import base64, importlib.util, zlib, io
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("box_b", HERE.parents[1] / "research" / "donus_vs_sl_20261009" / "box.py")
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
CODE = r'''
import re,zlib,base64,glob,os
files=sorted(glob.glob('yeni deneme/demo_bot.log*'),key=os.path.getmtime)
last_gap=None; last_t=None; out=["ts,ticket,gap"]
for f in files:
    for l in open(f,encoding='utf-8',errors='ignore'):
        if 'USOIL.FOREX:BUY' not in l: continue
        m=re.search(r'basis_gap, fark=([0-9.]+)%',l)
        if m: last_gap=m.group(1); last_t=l[:19]; continue
        if 'Açıldı ticket=' in l or 'LIMIT kuruldu ticket=' in l:
            k=re.search(r'ticket=(\d+)',l)
            if k: out.append(l[:19]+","+k.group(1)+","+(last_gap if last_gap and last_t and last_t[:13]==l[:13] else ""))
            last_gap=None
print("TICK_DATA_BEGIN"+base64.b64encode(zlib.compress("\n".join(out).encode())).decode()+"TICK_DATA_END")
'''
raw = B.run_code(CODE, "usoil basis", 1200)
txt = zlib.decompress(base64.b64decode(raw.split("TICK_DATA_BEGIN")[1].split("TICK_DATA_END")[0])).decode()
d = pd.read_csv(io.StringIO(txt))
d.to_csv(HERE / "results" / "basis.csv", index=False)
print(len(d), d.gap.notna().sum()); print(d.tail(8))
