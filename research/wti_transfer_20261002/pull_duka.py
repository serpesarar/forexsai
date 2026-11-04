"""Independent oil CFD minute bid/ask download; no synthetic bars or credentials."""
import concurrent.futures as cf
import datetime as dt
import lzma,json,struct,time,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from pull import DATA,OUT

def fetch(arg):
    date,side=arg;p=DATA/'duka_chunks'/f'{date:%Y%m%d}_{side}.bi5';p.parent.mkdir(exist_ok=True)
    url=f'https://datafeed.dukascopy.com/datafeed/LIGHTCMDUSD/{date:%Y}/{date.month-1:02d}/{date:%d}/{side}_candles_min_1.bi5'
    raw=p.read_bytes()if p.exists()else None
    if raw is None:
        for attempt in range(3):
            try:
                r=requests.get(url,timeout=30)
                if r.status_code in (403,429):raise PermissionError(f'Dukascopy download denied/rate limited: HTTP {r.status_code}')
                if r.status_code==404:return []
                r.raise_for_status();raw=r.content;p.write_bytes(raw);break
            except PermissionError:raise
            except Exception:
                if attempt==2:raise
                time.sleep(attempt+1)
    if not raw:return []
    decompressed=lzma.decompress(raw)
    rows=[];base=int(dt.datetime.combine(date,dt.time(),tzinfo=dt.timezone.utc).timestamp())
    for secs,o,c,l,h,v in struct.iter_unpack('>5If',decompressed):
        if v>0 and min(o,c,l,h)>0:rows.append([base+secs,o/1000,h/1000,l/1000,c/1000,v])
    return rows

def main():
    begin=dt.date(2025,1,1);end=dt.date(2026,1,2)
    args=[(begin+dt.timedelta(days=i),s)for i in range((end-begin).days)for s in ['BID','ASK']]
    byside={'BID':[],'ASK':[]};done=0
    with cf.ThreadPoolExecutor(max_workers=12)as pool:
        fs={pool.submit(fetch,arg):arg for arg in args}
        for f in cf.as_completed(fs):
            date,side=fs[f];byside[side]+=f.result();done+=1
            if done%100==0:print('downloaded/preserved',done,'/',len(args),flush=True)
    cols=['t','open','high','low','close','volume']
    bid=pd.DataFrame(byside['BID'],columns=cols).sort_values('t').drop_duplicates('t')
    ask=pd.DataFrame(byside['ASK'],columns=cols).sort_values('t').drop_duplicates('t')
    ask=ask.rename(columns={c:'ask_'+c for c in cols if c!='t'})
    d=bid.merge(ask,on='t',how='inner')
    assert len(d)>200000,'Independent history incomplete'
    assert d.close.median()>20 and d.close.median()<150,'Unknown Dukascopy price scale'
    assert(d.high>=d[['open','close']].max(axis=1)).all()and(d.low<=d[['open','close']].min(axis=1)).all()
    assert(d.ask_open>=d.open).mean()>.999,'Bid/ask corruption'
    d['spread_px']=d.ask_open-d.open
    d.to_parquet(DATA/'duka_2025.parquet',index=False)
    audit={'instrument':'LIGHT.CMD/USD','datafeed_symbol':'LIGHTCMDUSD','price_scale':1000,'rows':len(d),'first_utc':str(pd.Timestamp(d.t.min(),unit='s',tz='UTC')),'last_utc':str(pd.Timestamp(d.t.max(),unit='s',tz='UTC')),'median_price':float(d.close.median()),'median_spread':float(d.spread_px.median()),'requested_day_sides':len(args),'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (DATA/'duka_chunks').glob('*.bi5')}}
    (OUT/'duka_download.json').write_text(json.dumps(audit,indent=2));print({k:v for k,v in audit.items()if k!='files_sha256'},flush=True)

if __name__=='__main__':main()
