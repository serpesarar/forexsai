"""Read-only MT5 deal/order and decision-fingerprint export. Never sends orders."""
import sys,json,base64,zlib,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DATA=HERE/'data';OUT=HERE/'results'
sys.path.insert(0,str(ROOT))
# Avoid importing another module with the same file basename.
import importlib.util
sp=importlib.util.spec_from_file_location('wti_data_pull',ROOT/'research/wti_transfer_20261002/pull.py');wti=importlib.util.module_from_spec(sp);sp.loader.exec_module(wti)
remote=wti.remote

def deals():
    code='''import MetaTrader5 as m,json,base64,zlib
from datetime import datetime,timezone
assert m.initialize()
D=m.history_deals_get(datetime(2026,1,1,tzinfo=timezone.utc),datetime(2026,10,3,tzinfo=timezone.utc))
assert D is not None,m.last_error()
syms={'SpotCrude','NAS100','USTEC','GER40','DE40','XAUUSD'}
# Export all engines for symbol inventory; main research later fixes the bot magic cohort.
d=[{k:getattr(x,k)for k in ['ticket','order','time','time_msc','type','entry','magic','position_id','reason','volume','price','commission','swap','profit','fee','symbol','comment']}for x in D if x.symbol in syms]
O=m.history_orders_get(datetime(2026,1,1,tzinfo=timezone.utc),datetime(2026,10,3,tzinfo=timezone.utc))or[]
ids={x['order']for x in d if x['entry']==0}
o=[{k:getattr(x,k)for k in ['ticket','time_setup','time_done','type','state','magic','position_id','volume_initial','volume_current','price_open','sl','tp','symbol','comment']}for x in O if x.ticket in ids]
payload={'deals':d,'opening_orders':o,'symbol_metadata':{}}
for s in syms:
 i=m.symbol_info(s)
 if i:payload['symbol_metadata'][s]={k:getattr(i,k)for k in ['point','digits','trade_tick_size','trade_tick_value','trade_contract_size','volume_min','volume_step']}
out=base64.b64encode(zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)).decode()
assert len(out)<55000,('Need smaller slices',len(out))
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END');m.shutdown()
'''
    x=remote(code,'loss-veto actual deal and opening-order history Jan-Oct2026');(DATA/'mt5_deals_orders.json').write_text(json.dumps(x,separators=(',',':')))
    from collections import Counter
    print('MT5 deals',len(x['deals']),'opening orders',len(x['opening_orders']),'symbols',dict(Counter(d['symbol']for d in x['deals'])),'magics',dict(Counter(d['magic']for d in x['deals'])),flush=True)

def database():
    client,fetch_all=wti.client,wti.fetch_all
    c=client()
    # Private research export; never print raw credentials or unrelated user records.
    for table,col in [('bot_trades','close_time'),('bot_entry_fingerprints','ts')]:
        path=DATA/(table+'.json')
        if path.exists():continue
        try:
            x=fetch_all(c,table,'*',[],col);path.write_text(x.to_json(orient='records',date_format='iso'));print(table,len(x),list(x.columns),flush=True)
        except Exception as e:print(table,type(e).__name__,str(e)[:250],flush=True)
def skips():
    code="""from pathlib import Path
import json,base64,zlib
p=Path('yeni deneme/gate_skipped.jsonl');rows=[];keys=None
if p.exists():
 for line in p.open(encoding='utf-8',errors='replace'):
  try:x=json.loads(line)
  except:continue
  if x.get('symbol')=='USOIL.FOREX'or x.get('mt5_symbol')=='SpotCrude':
   if keys is None:keys=list(x)
   rows.append({k:x.get(k)for k in ['ts','scope','symbol','mt5_symbol','direction','price','reason','rule','decision','sl','tp','sl_dist','tp_dist','atr_1m','band','shadow','score','confidence']if k in x})
payload={'file_exists':p.exists(),'count':len(rows),'first_keys':keys,'rows':rows[-1500:],'truncated':len(rows)>1500}
out=base64.b64encode(zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)).decode()
assert len(out)<55000,len(out)
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END')
"""
    x=remote(code,'loss-veto oil gate/WAIT opportunity log read');(DATA/'gate_skipped.json').write_text(json.dumps(x,separators=(',',':')));print('Oil opportunity logs',len(x['rows']),'of',x['count'],'exists',x['file_exists'],flush=True)

def snapshots():
    from concurrent.futures import ThreadPoolExecutor
    c=wti.client()
    def one(tf):
        p=DATA/('snap_'+tf+'.csv')
        if p.exists():print('preserved',tf,flush=True);return
        z=wti.fetch_all(wti.client(),'indicator_snapshots','candle_time,open,high,low,close,volume',[('symbol','eq','USOIL.FOREX'),('timeframe','eq',tf),('candle_time','gte','2026-06-01'),('candle_time','lt','2026-10-02')],'candle_time')
        z.to_csv(p,index=False);print('snapshots',tf,len(z),flush=True)
    with ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(one,['1m','5m','15m','1h']))

if __name__=='__main__':
    if sys.argv[1]=='deals':deals()
    elif sys.argv[1]=='database':database()
    elif sys.argv[1]=='snapshots':snapshots()
    elif sys.argv[1]=='skips':skips()
