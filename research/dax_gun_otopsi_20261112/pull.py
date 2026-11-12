"""Salt-okuma: kutudaki Pepperstone MT5'ten GER40 deal/emir geçmişi + M1 bar + bot log satırları. EMİR GÖNDERMEZ."""
import sys, json, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; DATA = HERE / "data"
sp = importlib.util.spec_from_file_location("wti_pull", ROOT / "research/wti_transfer_20261002/pull.py")
wti = importlib.util.module_from_spec(sp); sp.loader.exec_module(wti)

HEAD = r'''import MetaTrader5 as m,json,base64,zlib,time
from datetime import datetime,timezone
assert m.initialize(path=r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"),m.last_error()
acc=m.account_info().login
'''
TAIL = r'''
out=base64.b64encode(zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)).decode()
assert len(out)<55000,len(out)
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END');m.shutdown()
'''
DEALS = HEAD + r'''
a=datetime(2026,11,9,tzinfo=timezone.utc);b=datetime(2026,11,14,tzinfo=timezone.utc)
D=m.history_deals_get(a,b) or []
d=[{k:getattr(x,k)for k in ['ticket','order','time','time_msc','type','entry','magic','position_id','reason','volume','price','swap','profit','symbol','comment']}for x in D if x.symbol=='GER40']
O=m.history_orders_get(a,b) or []
o=[{k:getattr(x,k)for k in ['ticket','time_setup','time_done','type','state','magic','position_id','volume_initial','price_open','sl','tp','symbol','comment']}for x in O if x.symbol=='GER40']
P=[{k:getattr(x,k)for k in ['ticket','time','type','magic','volume','price_open','sl','tp','price_current','profit','symbol','comment']}for x in (m.positions_get() or [])]
t=m.symbol_info_tick('GER40')
payload={'acc':acc,'deals':d,'orders':o,'positions':P,'srv_now':t.time,'utc_now':time.time()}
''' + TAIL
BARS = HEAD + r'''
r=m.copy_rates_from_pos('GER40',m.TIMEFRAME_M1,0,int(sys.argv[1]) if False else 2900)
payload={'acc':acc,'bars':[[int(x['time']),float(x['open']),float(x['high']),float(x['low']),float(x['close']),int(x['tick_volume']),int(x['spread'])]for x in r]}
''' + TAIL
LOG = r'''import json,base64,zlib,re
from pathlib import Path
rows=[]
for p in [Path('yeni deneme/demo_bot.log')]+sorted(Path('yeni deneme').glob('demo_bot*.log*'))[-3:]:
  if not p.exists():continue
  for line in p.open(encoding='utf-8',errors='replace'):
    if ('2026-11-11' in line[:12] or '2026-11-12' in line[:12]) and re.search(r'GDAXI|GER40|DAX',line):
      rows.append(line.rstrip()[:260])
rows=list(dict.fromkeys(rows))
keep=[r for r in rows if re.search(r'Açıld|CANLI|SL|TP|kapı|KAPI|veto|engel|blok|oy|vote|giriş|GİRİŞ|CHREV|MOM|DECIDER|reddet|atla',r)]
payload={'n_all':len(rows),'rows':keep[-900:]}
out=base64.b64encode(zlib.compress(json.dumps(payload,ensure_ascii=False).encode(),9)).decode()
if len(out)>=55000: payload['rows']=keep[-400:]; out=base64.b64encode(zlib.compress(json.dumps(payload,ensure_ascii=False).encode(),9)).decode()
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END')
'''
if __name__ == "__main__":
    what = sys.argv[1]
    code = {"deals": DEALS, "bars": BARS, "log": LOG}[what]
    x = wti.remote(code, f"dax gün otopsisi {what} (salt-okuma)")
    (DATA / f"{what}.json").write_text(json.dumps(x, ensure_ascii=False))
    print(what, {k: (len(v) if isinstance(v, list) else v) for k, v in x.items()})
