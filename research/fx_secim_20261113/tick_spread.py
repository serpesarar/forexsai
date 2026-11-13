"""Salt-okuma: son 2 günün tick'lerinden saat başına ortalama spread (bp) + hesap türü. EMİR YOK."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from kutu import run
CODE = r'''import MetaTrader5 as m,json,base64,zlib,time
from datetime import datetime,timezone
import numpy as np
assert m.initialize(path=r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"),m.last_error()
a=m.account_info(); assert a.login==61628380
payload={'acc':{'name':a.name,'company':a.company,'currency':a.currency,'leverage':a.leverage,'margin_mode':a.margin_mode,'trade_mode':a.trade_mode},'sp':{}}
t0=datetime(2026,11,11,0,0,tzinfo=timezone.utc); t1=datetime(2026,11,13,12,0,tzinfo=timezone.utc)
for s in ["EURUSD","USDJPY","EURJPY","GBPJPY","AUDJPY","USDCAD","GBPUSD","AUDCAD","EURGBP"]:
  m.symbol_select(s,True)
  tk=m.copy_ticks_range(s,t0,t1,m.COPY_TICKS_INFO)
  if tk is None or len(tk)==0: payload['sp'][s]=None; continue
  b=tk['bid'];k=tk['ask'];ok=(b>0)&(k>0)
  bp=(k[ok]-b[ok])/((k[ok]+b[ok])/2)*1e4
  hr=((tk['time'][ok]//3600)%24)
  payload['sp'][s]={'n':int(ok.sum()),'ort':float(bp.mean()),'med':float(np.median(bp)),'saat':{int(h):[round(float(bp[hr==h].mean()),3),int((hr==h).sum())] for h in np.unique(hr)}}
  time.sleep(2)
D=m.history_deals_get(datetime(2026,10,1,tzinfo=timezone.utc),datetime(2026,11,14,tzinfo=timezone.utc)) or []
payload['komisyon_ornek']=[[x.symbol,x.volume,x.commission,x.fee] for x in D if x.commission!=0 or x.fee!=0][:20]
payload['n_deals']=len(D)
out=base64.b64encode(zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)).decode()
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END');m.shutdown()
'''
if __name__ == "__main__":
    x = run(CODE, "FX tick spread ölçümü", 900)
    (HERE / "data/tick_spread.json").write_text(json.dumps(x, indent=1))
    print(json.dumps(x["acc"]), x["n_deals"], x["komisyon_ornek"][:5])
    for s, v in x["sp"].items():
        print(s, None if v is None else (v["n"], round(v["ort"], 3), round(v["med"], 3)))
