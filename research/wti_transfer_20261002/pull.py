"""Read-only oil data downloads. Never prints credentials or submits trading commands."""
import sys, json, time, hashlib, base64, zlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DATA=HERE/'data';DATA.mkdir(exist_ok=True)
OUT=HERE/'results';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'research/ndx_buy_lab'))
from pull_data import client,fetch_all
sys.path.insert(0,str(ROOT))
from scripts.remote import _client,submit

def metadata():
    c=client();res={}
    for tf in ['1m','5m','15m','30m','1h','1d']:
        q=c.table('candle_cache').select('candle_time,fetched_at',count='exact').eq('symbol','USOIL.FOREX').eq('timeframe',tf)
        lo=q.order('candle_time').limit(1).execute()
        hi=c.table('candle_cache').select('candle_time,fetched_at').eq('symbol','USOIL.FOREX').eq('timeframe',tf).order('candle_time',desc=True).limit(1).execute()
        res[tf]={'n':lo.count,'first':lo.data,'last':hi.data};print(tf,res[tf],flush=True)
    (DATA/'metadata.json').write_text(json.dumps(res,indent=2))

def cache_one(tf):
    path=DATA/f'cache_{tf}.parquet'
    if path.exists():print('preserved',path.name,flush=True);return
    z=fetch_all(client(),'candle_cache','candle_time,open,high,low,close,volume,fetched_at',[('symbol','eq','USOIL.FOREX'),('timeframe','eq',tf)],'candle_time')
    z.to_parquet(path,index=False);print('saved',tf,len(z),flush=True)

def macro():
    import yfinance as yf
    for name,tick in [('VIX','^VIX'),('OVX','^OVX'),('WTI_REFERENCE','CL=F'),('DXY','DX-Y.NYB')]:
        path=DATA/f'macro_{name}.csv'
        if path.exists():continue
        z=yf.Ticker(tick).history(start='2008-01-01',end='2026-10-02',auto_adjust=False)
        if z.empty:raise RuntimeError('No macro history: '+name)
        z.to_csv(path);print('macro',name,len(z),flush=True)

def remote(code,label):
    enc=base64.b64encode(code.encode()).decode()
    command='python -c "import base64;exec(base64.b64decode(\''+enc+'\'))"'
    c=_client();cid=submit(c,'mt5_box','run_analysis',{'command':command,'timeout':100},'WTI read-only research: '+label)
    print('queued read-only',label,cid,flush=True)
    for _ in range(75):
        r=c.table('evolution_commands').select('status,output,return_code').eq('id',cid).limit(1).execute().data
        if r and r[0]['status']in ['done','failed','timeout']:
            out=r[0].get('output')or''
            if r[0]['status']!='done' or 'WTI_DATA_BEGIN'not in out:raise RuntimeError(out[-1300:])
            enc=out.split('WTI_DATA_BEGIN',1)[1].split('WTI_DATA_END',1)[0]
            return json.loads(zlib.decompress(base64.b64decode(enc)))
        time.sleep(2)
    raise TimeoutError(label)

PREFIX='''
import MetaTrader5 as m,time,json,base64,zlib,statistics
from datetime import datetime,timezone,timedelta
assert m.initialize(),'MT5 unavailable'
offsets=[]
for s in ['NAS100','GER40','XAUUSD','SpotCrude']:
 t=m.symbol_info_tick(s)
 if t is not None:
  off=round((t.time-time.time())/1800)*1800
  if 0<=off<=14400 and abs(t.time-time.time()-off)<120:offsets.append(off)
off=int(statistics.median(offsets)) if len(offsets)>=2 else None
if len(offsets)>=2:assert max(offsets)-min(offsets)<=1800,'Clock disagreement'
info=m.symbol_info('SpotCrude')
assert info is not None,'SpotCrude unavailable'
'''
SUFFIX='''
raw=json.dumps(payload,separators=(',',':')).encode()
out=base64.b64encode(zlib.compress(raw,9)).decode()
assert len(out)<55000,'Chunk too large'
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END')
m.shutdown()
'''

def probe():
    code=PREFIX+'''
payload={'offset_seconds':off,'server_now':time.time(),'point':info.point,'digits':info.digits,'symbol':'SpotCrude','description':info.description,
 'trade_contract_size':info.trade_contract_size,'tick_size':info.trade_tick_size,'tick_value':info.trade_tick_value,
 'volume_min':info.volume_min,'volume_step':info.volume_step,'swap_long':info.swap_long,'swap_short':info.swap_short,'swap_mode':info.swap_mode,
 'tick':{'time_raw':m.symbol_info_tick('SpotCrude').time,'bid':m.symbol_info_tick('SpotCrude').bid,'ask':m.symbol_info_tick('SpotCrude').ask},'history':{}}
for name,tf in [('1m',m.TIMEFRAME_M1),('15m',m.TIMEFRAME_M15),('30m',m.TIMEFRAME_M30),('1h',m.TIMEFRAME_H1),('1d',m.TIMEFRAME_D1)]:
 r=m.copy_rates_from_pos('SpotCrude',tf,0,200000)
 if r is None:r=m.copy_rates_from_pos('SpotCrude',tf,0,100000)
 if r is None:r=m.copy_rates_from_pos('SpotCrude',tf,0,50000)
 payload['history'][name]={'n':0 if r is None else len(r),'first_raw':int(r[0]['time'])if r is not None and len(r) else None,'last_raw':int(r[-1]['time'])if r is not None and len(r) else None}
r=m.copy_rates_from_pos('SpotCrude',m.TIMEFRAME_M1,1,180)
payload['reference_rows']=[[int(v['time']),float(v['open']),float(v['high']),float(v['low']),float(v['close']),int(v['tick_volume']),int(v['spread'])]for v in r]
'''+SUFFIX
    x=remote(code,'symbol and clock probe');(DATA/'mt5_metadata.json').write_text(json.dumps(x,indent=2));print(json.dumps(x),flush=True)

def direct():
    meta=json.loads((DATA/'mt5_metadata.json').read_text())
    clock=json.loads((OUT/'remote_clock.json').read_text())
    offset=clock['offset_seconds'];assert clock['status']=='PASS'
    first=(pd.Timestamp(meta['history']['1m']['first_raw'],unit='s',tz='UTC')-pd.Timedelta(seconds=offset)).floor('D')
    end=pd.Timestamp('2026-10-02',tz='UTC');chunks=DATA/'mt5_chunks';chunks.mkdir(exist_ok=True)
    start=first
    while start<end:
        stop=min(start+pd.Timedelta(days=2),end);p=chunks/f'{start:%Y%m%d}.json'
        if not p.exists():
            code="import MetaTrader5 as m,json,base64,zlib\nfrom datetime import datetime,timedelta\nassert m.initialize()\ninfo=m.symbol_info('SpotCrude')\n"+f'''
# Frozen offset from historical overlap, not stale present-day tick ages.
off={offset}
start=datetime.fromisoformat('{start.isoformat()}')+timedelta(seconds=off)
end=datetime.fromisoformat('{stop.isoformat()}')+timedelta(seconds=off)
r=m.copy_rates_range('SpotCrude',m.TIMEFRAME_M1,start,end)
rows=[] if r is None else [[int(v['time'])-off,float(v['open']),float(v['high']),float(v['low']),float(v['close']),int(v['tick_volume']),int(v['spread'])]for v in r]
payload={{'symbol':'SpotCrude','offset_seconds':off,'point':info.point,'start':'{start.isoformat()}','end':'{stop.isoformat()}','rows':rows}}
'''+SUFFIX
            p.write_text(json.dumps(remote(code,f'M1 {start:%Y-%m-%d}'),separators=(',',':')))
        print('preserved/exported',p.name,flush=True);start=stop
    rows=[]
    for p in sorted(chunks.glob('*.json')):
        x=json.loads(p.read_text());rows+=x['rows']
    z=pd.DataFrame(rows,columns=['t','open','high','low','close','volume','spread']).drop_duplicates('t').sort_values('t')
    z['spread_px']=z.spread*meta['point'];z.to_parquet(DATA/'mt5_1m.parquet',index=False)
    z.to_csv(DATA/'mt5_1m.csv',index=False)
    print('direct M1',len(z),flush=True)

def provenance():
    paths=list(DATA.glob('*.*'))+list((DATA/'mt5_chunks').glob('*.json'))
    (OUT/'download_provenance.json').write_text(json.dumps({'created_utc':pd.Timestamp.now(tz='UTC').isoformat(),'files':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths if p.is_file()}},indent=2))

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='meta':metadata()
    elif mode=='cache':
        with ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(cache_one,['1m','5m','15m','30m','1h','1d']))
    elif mode=='macro':macro()
    elif mode=='probe':probe()
    elif mode=='direct':direct()
    elif mode=='provenance':provenance()
