"""Veri çekme (salt-okuma): panel USOIL sinyalleri (prediction_logs 02-01 → bugün) + kutu gate_skipped USOIL BUY.
python3 research/usoil_hafta_20261020/pull.py"""
from __future__ import annotations

import base64
import importlib.util
import json
import sys
import zlib
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402

spec = importlib.util.spec_from_file_location("box_u", ROOT / "research" / "donus_vs_sl_20261009" / "box.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
MODELS = ["pulse1", "pulse2", "pulse3", "emel", "smc", "ml:main", "meta"]

CODE = r'''
import json,zlib,base64
from datetime import datetime,timedelta
last={};out=[]
for l in open('yeni deneme/gate_skipped.jsonl',encoding='utf-8',errors='ignore'):
    try: r=json.loads(l)
    except Exception: continue
    if r.get('symbol')!='USOIL.FOREX' or r.get('direction')!='BUY': continue
    try: t=datetime.fromisoformat(r['ts'])
    except Exception: continue
    k=(r.get('scope'),r.get('reason'))
    if k in last and t-last[k]<timedelta(minutes=30): continue
    last[k]=t
    out.append([r['ts'],r.get('scope'),r.get('reason'),r.get('price')])
print("TICK_DATA_BEGIN"+base64.b64encode(zlib.compress(json.dumps(out[__A__:__B__]+[len(out)]).encode())).decode()+"TICK_DATA_END")
'''

if __name__ == "__main__":
    rows = data.fetch_table(data.get_client(), "prediction_logs", "created_at,model_type,ml_direction",
                            [("created_at", "gte", "2026-02-01"), ("symbol", "eq", "USOIL.FOREX"),
                             ("model_type", "in_", MODELS)], "created_at")
    p = pd.DataFrame(rows)
    p["ts"] = pd.to_datetime(p.created_at, utc=True, format="ISO8601")
    p = p[p.ml_direction.isin(["BUY", "SELL"])][["ts", "model_type", "ml_direction"]]
    p.to_parquet(HERE / "results" / "panel_usoil.parquet", index=False)
    print("panel", len(p), p.ts.min(), p.ts.max(), p.groupby("ml_direction").size().to_dict())
    allr, a, step = [], 0, 700
    while True:
        out = B.decode(B.run_code(CODE.replace("__A__", str(a)).replace("__B__", str(a + step)), f"usoil skip {a}", 900))
        n = out.pop()
        allr += out
        a += step
        if a >= n:
            break
    s = pd.DataFrame(allr, columns=["ts", "scope", "reason", "price"])
    s["ts"] = pd.to_datetime(s.ts, utc=True, format="ISO8601")
    s.to_parquet(HERE / "results" / "skipped_usoil.parquet", index=False)
    print("skipped", len(s), s.ts.min(), s.ts.max())
    print(s.groupby("reason").size().sort_values(ascending=False).head(15))
