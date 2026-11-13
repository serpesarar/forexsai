"""Salt-okuma: Pepperstone MT5'teki döviz çiftleri ve maliyetleri. EMİR GÖNDERMEZ."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from kutu import run
CODE = r'''import MetaTrader5 as m,json,base64,zlib
assert m.initialize(path=r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"),m.last_error()
acc=m.account_info(); S=m.symbols_get() or []
payload={'acc':acc.login,'server':acc.server,'n_all':len(S),'paths':sorted({'\\'.join((s.path or '').split('\\')[:2]) for s in S}),'fx':{}}
for s in S:
  p=s.path or ''
  C={'USD','EUR','GBP','JPY','CHF','CAD','AUD','NZD','TRY','ZAR','MXN','SEK','NOK','DKK','PLN','HUF','CZK','SGD','HKD','CNH','ILS','THB'}
  nm=s.name.upper().split('.')[0]
  if not ('forex' in p.lower() or (len(nm)==6 and nm[:3] in C and nm[3:] in C)): continue
  payload['fx'][s.name]={'path':p,'point':s.point,'digits':s.digits,'contract':s.trade_contract_size,'tick_value':s.trade_tick_value,'spread_now':s.spread,
     'swap_long':s.swap_long,'swap_short':s.swap_short,'swap_mode':s.swap_mode,'bid':s.bid,'ask':s.ask,'cur_profit':s.currency_profit,'cur_base':s.currency_base}
out=base64.b64encode(zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)).decode()
print('WTI_DATA_BEGIN'+out+'WTI_DATA_END');m.shutdown()
'''
if __name__ == "__main__":
    x = run(CODE, "FX sembol listesi", 300)
    (HERE / "data/probe.json").write_text(json.dumps(x, indent=1))
    print(x["acc"], x["server"], x["n_all"], x["paths"], len(x["fx"]))
