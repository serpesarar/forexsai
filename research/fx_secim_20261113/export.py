"""Kutuda: FX MT5 barlarını salt okunur çeker, gzip CSV olarak özel 'research-xfer' deposuna yükler. EMİR YOK."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from kutu import run
PAIRS = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD","EURJPY","GBPJPY","AUDJPY","CADJPY","NZDJPY","CHFJPY",
         "EURGBP","EURCHF","EURAUD","EURCAD","GBPAUD","GBPCHF","AUDNZD","AUDCAD","USDMXN","USDZAR","USDTRY","EURTRY","USDNOK","USDSEK"]
TFS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["D1","H1","M15"]
CODE = r'''import sys,io,gzip,json,base64,zlib,time
sys.path.insert(0,"remote_agent")
import agent_config as c, MetaTrader5 as m, requests
assert m.initialize(path=r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"),m.last_error()
assert m.account_info().login==61628380
url=c.SUPABASE_URL.rstrip("/"); key=c.SUPABASE_SERVICE_KEY
H={"Authorization":"Bearer "+key,"apikey":key}
try: requests.post(url+"/storage/v1/bucket",headers=dict(H,**{"Content-Type":"application/json"}),data=json.dumps({"id":"research-xfer","name":"research-xfer","public":False}),timeout=60)
except Exception as e: pass
PAIRS=__PAIRS__; TFS=__TFS__; BUDGET=__BUDGET__
summ={}
have=set()
try:
  L=requests.post(url+"/storage/v1/object/list/research-xfer",headers=dict(H,**{"Content-Type":"application/json"}),data=json.dumps({"prefix":"fx","limit":2000}),timeout=60).json()
  have={x["name"] for x in L if (x.get("metadata") or {}).get("size",0)>0}
except Exception as e: pass
import pandas as pd
T0=time.time()
for s in PAIRS:
  m.symbol_select(s,True); time.sleep(0.3); si=m.symbol_info(s)
  if si is None: summ[s]='yok'; continue
  summ[s]={"meta":{"point":si.point,"digits":si.digits,"tick_value":si.trade_tick_value,"contract":si.trade_contract_size,"swap_long":si.swap_long,"swap_short":si.swap_short,"spread_now":si.spread}}
for tf in TFS:
  for s in PAIRS:
    if summ.get(s)=='yok': continue
    if "%s_%s.csv.gz"%(s,tf) in have: summ[s][tf]="var"; continue
    if time.time()-T0>BUDGET: summ[s][tf]="sure"; continue
    pos,parts=0,[]
    for _ in range(60):
      r=m.copy_rates_from_pos(s,getattr(m,"TIMEFRAME_"+tf),pos,99000)
      if r is None or len(r)==0: break
      parts.append(r); pos+=len(r)
      if len(r)<99000: break
    if not parts: summ[s][tf]=[0]; continue
    import numpy as np
    a=np.concatenate(parts); df=pd.DataFrame({"t":a["time"].astype("int64"),"o":a["open"],"h":a["high"],"l":a["low"],"c":a["close"],"v":a["tick_volume"].astype("int64"),"sp":a["spread"].astype("int64")}).drop_duplicates("t").sort_values("t")
    buf=io.BytesIO(); df.to_csv(buf,index=False,compression={"method":"gzip"})
    name="fx/%s_%s.csv.gz"%(s,tf)
    rr=requests.post(url+"/storage/v1/object/research-xfer/"+name,headers=dict(H,**{"x-upsert":"true","Content-Type":"application/gzip"}),data=buf.getvalue(),timeout=600)
    summ[s][tf]=[len(df),int(df.t.iloc[0]),int(df.t.iloc[-1]),rr.status_code]
offs=[]
for s in ["EURUSD","NAS100","XAUUSD"]:
  t=m.symbol_info_tick(s)
  if t: offs.append(int(round((t.time-time.time())/900)*900))
summ["_srv_minus_utc_s"]=offs
out=base64.b64encode(zlib.compress(json.dumps(summ,separators=(',',':')).encode(),9)).decode()
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END');m.shutdown()
'''
if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "tum"
    code = CODE.replace("__PAIRS__", json.dumps(PAIRS)).replace("__TFS__", json.dumps(TFS)).replace("__BUDGET__", "2700")
    x = run(code, f"FX bar dışa aktarımı {tag}", 3600)
    (HERE / f"data/export_{tag}.json").write_text(json.dumps(x, indent=1))
    for k, v in x.items():
        print(k, v if not isinstance(v, dict) else {t: v.get(t) for t in TFS})
