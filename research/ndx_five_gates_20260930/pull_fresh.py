"""Read-only MT5 bar export through the existing remote command bridge.

The remote code only initializes its own API connection, reads quotes/bars and
prints compressed data. It does not write remote files, alter settings, restart
processes or send orders. The bridge creates ordinary command-queue records.
"""
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.remote import _client, submit  # noqa: E402

HERE = Path(__file__).resolve().parent


def command(start: str, end: str, probe: bool = False) -> str:
    code = f'''
import MetaTrader5 as m, time, json, base64, zlib, statistics
from datetime import datetime, timezone, timedelta
assert m.initialize(), 'MT5 connection unavailable'
offsets=[]
for sym in ['NAS100','GER40','XAUUSD']:
 t=m.symbol_info_tick(sym)
 if t is not None:
  off=round((t.time-time.time())/1800)*1800
  if 0 <= off <= 14400 and abs(t.time-time.time()-off)<120:
   offsets.append(off)
assert len(offsets)>=2, 'No trustworthy broker clock'
off=int(statistics.median(offsets))
assert max(offsets)-min(offsets)<=1800, 'Broker clocks disagree'
info=m.symbol_info('NAS100')
assert info is not None, 'NAS100 symbol unavailable'
begin=datetime.fromisoformat('{start}').replace(tzinfo=timezone.utc)+timedelta(seconds=off)
end=datetime.fromisoformat('{end}').replace(tzinfo=timezone.utc)+timedelta(seconds=off)
r=m.copy_rates_range('NAS100',m.TIMEFRAME_M1,begin,end)
assert r is not None and len(r)>0, 'M1 history unavailable'
rows=[[int(x['time'])-off,float(x['open']),float(x['high']),float(x['low']),float(x['close']),int(x['tick_volume']),int(x['spread'])] for x in r]
payload={{'offset_seconds':off,'point':info.point,'digits':info.digits,'start':'{start}','end':'{end}','rows':rows}}
if {probe!r}:
 payload['rows']=[rows[0],rows[-1]]
 payload['count']=len(rows)
raw=json.dumps(payload,separators=(',',':')).encode()
out=base64.b64encode(zlib.compress(raw,9)).decode()
assert len(out)<55000, 'Chunk exceeds remote output limit'
print('NDX_DATA_BEGIN'+out+'NDX_DATA_END')
m.shutdown()
'''
    enc = base64.b64encode(code.encode()).decode()
    return 'python -c "import base64;exec(base64.b64decode(\''+enc+'\'))"'


def fetch(c, start: str, end: str, probe: bool = False) -> dict:
    cid = submit(c,"mt5_box","run_analysis",{"command":command(start,end,probe),"timeout":90},"NDX offline research: read-only M1 export")
    print("read-only export queued",start,end,"id",cid,flush=True)
    for _ in range(65):
        r=c.table("evolution_commands").select("status,output,return_code").eq("id",cid).limit(1).execute().data
        if r and r[0]["status"] in ("done","failed","timeout"):
            x=r[0]
            out=x.get("output") or ""
            if x["status"]!="done" or "NDX_DATA_BEGIN" not in out:
                # Remote code contains no credentials; keep diagnostics concise.
                raise RuntimeError(f"Read-only export failed: {out[-1500:]}")
            data=out.split("NDX_DATA_BEGIN",1)[1].split("NDX_DATA_END",1)[0]
            return json.loads(zlib.decompress(base64.b64decode(data)))
        time.sleep(2)
    raise TimeoutError("Read-only MT5 export did not finish")


def main() -> None:
    c=_client()
    if len(sys.argv)>1 and sys.argv[1]=="probe":
        p=fetch(c,"2026-09-01","2026-09-30",True)
        print(json.dumps(p),flush=True)
        return
    directory=HERE/"results/fresh_chunks"
    directory.mkdir(parents=True,exist_ok=True)
    start=datetime(2026,8,29,tzinfo=timezone.utc)
    end=datetime(2026,9,30,tzinfo=timezone.utc)
    while start<end:
        stop=min(start+timedelta(days=2),end)
        p=directory/f"{start:%Y%m%d}.json"
        if not p.exists():
            try:
                x=fetch(c,start.isoformat(),stop.isoformat())
            except RuntimeError as exc:
                if "M1 history unavailable" in str(exc):
                    start=stop
                    continue
                raise
            p.write_text(json.dumps(x),encoding="utf-8")
        print("saved",p.name,flush=True)
        start=stop
    rows=[]
    meta=[]
    for p in sorted(directory.glob("*.json")):
        x=json.loads(p.read_text())
        rows.extend(x.pop("rows"))
        meta.append({**x,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    payload={"export":"read-only direct MT5", "chunks":meta,"rows":sorted({r[0]:r for r in rows}.values())}
    out=HERE/"results/fresh_mt5_september.json"
    out.write_text(json.dumps(payload),encoding="utf-8")
    print("COMPLETED",len(payload["rows"]),"M1 bars",out,flush=True)


if __name__=="__main__":
    main()
