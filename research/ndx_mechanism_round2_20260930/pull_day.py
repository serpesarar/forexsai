"""Read only the completed September 30 MT5 day, after the derivative freeze."""
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ndx_five_gates_20260930"))
from pull_fresh import _client, fetch

if __name__=="__main__":
    p=HERE/"results/fresh_day.json"
    if p.exists():raise SystemExit("Fresh-day export already exists; preserve it")
    x=fetch(_client(),"2026-09-29T00:00:00+00:00","2026-10-01T00:00:00+00:00")
    p.write_text(json.dumps(x),encoding="utf-8")
    audit={k:v for k,v in x.items() if k!="rows"}
    audit.update({"rows":len(x["rows"]),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                  "purpose":"Rules frozen before the new Sep30 day. MT5 read-only; no orders/files/config on box."})
    (HERE/"results/fresh_day_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    print("Fresh-day bars saved",len(x["rows"]),"offset",x["offset_seconds"],"point",x["point"],flush=True)
