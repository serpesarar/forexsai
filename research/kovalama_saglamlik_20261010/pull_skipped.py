"""Kutudaki gate_skipped.jsonl'den NDX SELL engellenen sinyalleri çek (scope başına 10 dk'da bir) → results/skipped.parquet."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("box_k", ROOT / "research" / "donus_vs_sl_20261009" / "box.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

CODE = r'''
import json,zlib,base64,collections
from datetime import datetime,timedelta
last={};out=[];cnt=collections.Counter()
for l in open('yeni deneme/gate_skipped.jsonl',encoding='utf-8',errors='ignore'):
    try: r=json.loads(l)
    except Exception: continue
    if r.get('symbol')!='NDX.INDX' or r.get('direction')!='SELL': continue
    fam=r.get('scope','').split(':')[-1]; cnt[(fam,r.get('reason'))]+=1
    try: t=datetime.fromisoformat(r['ts'])
    except Exception: continue
    k=fam
    if k in last and t-last[k]<timedelta(minutes=10): continue
    last[k]=t
    out.append([r['ts'],fam,r.get('reason'),r.get('price'),r.get('pos'),r.get('veto_reason')])
blob={"rows":out[__A__:__B__],"n":len(out),"cnt":[[a,b,v] for (a,b),v in cnt.items()]}
print("TICK_DATA_BEGIN"+base64.b64encode(zlib.compress(json.dumps(blob).encode())).decode()+"TICK_DATA_END")
'''

if __name__ == "__main__":
    rows, a, step, d = [], 0, 700, None
    while True:
        d = B.decode(B.run_code(CODE.replace("__A__", str(a)).replace("__B__", str(a + step)), f"gate_skipped {a}", timeout=900))
        rows += d["rows"]
        a += step
        print(a, d["n"], flush=True)
        if a >= d["n"]:
            break
    df = pd.DataFrame(rows, columns=["ts", "aile", "reason", "price", "pos", "veto_reason"])
    df["ts"] = pd.to_datetime(df.ts, utc=True, format="ISO8601")
    df.to_parquet(HERE / "results" / "skipped.parquet")
    c = pd.DataFrame(d["cnt"], columns=["aile", "reason", "n"]).sort_values("n", ascending=False)
    c.to_csv(HERE / "results" / "skipped_counts.csv", index=False)
    print(len(df), df.ts.min(), df.ts.max())
    print(df.groupby(["aile", "reason"]).size().sort_values(ascending=False).head(25))
