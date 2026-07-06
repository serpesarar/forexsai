"""
07 — DAX (GDAXI) + Petrol (USOIL) için S/R parametre doğrulaması (gerçek 1m).
config'teki ZONE_WIDTH/MAX_ENTRY/MIN_TP değerleriyle örnek planlar üret.
GDAXI 1m candle_cache'te 06-12'de donmuş → pre-freeze pencere çekip test ediyoruz
(amaç: width=10'un mantıklı S/R üretip üretmediği — canlıda 1m MT5'ten gelecek).
"""
import json, sys, statistics as st
from pathlib import Path
from dotenv import dotenv_values
from supabase import create_client
sys.path.insert(0, str(Path("/Users/melihcanodacioglu/Desktop/panel/yeni deneme")))
import importlib.util
spec=importlib.util.spec_from_file_location("cfg","/Users/melihcanodacioglu/Desktop/panel/yeni deneme/config.py")
cfg=importlib.util.module_from_spec(spec); spec.loader.exec_module(cfg)
from sr_zones import detect_zones, plan_sr_entry

ROOT=Path("/Users/melihcanodacioglu/Desktop/panel"); B=ROOT/"bot_live_audit"/"bars"
# GDAXI 1m çek (pre-freeze)
gpath=B/"GDAXI.INDX_1m.json"
if not gpath.exists():
    c=dotenv_values(ROOT/"backend"/".env")
    sb=create_client(c["SUPABASE_URL"], c.get("SUPABASE_SERVICE_ROLE_KEY") or c["SUPABASE_KEY"])
    rows=[]; off=0
    while True:
        r=(sb.table("candle_cache").select("candle_time,open,high,low,close")
           .eq("symbol","GDAXI.INDX").eq("timeframe","1m")
           .gte("candle_time","2026-06-09").lt("candle_time","2026-06-12")
           .order("candle_time").range(off,off+999)).execute().data
        rows+=r
        if len(r)<1000: break
        off+=1000
    gpath.write_text(json.dumps(rows)); print(f"GDAXI 1m çekildi: {len(rows)} bar")

def demo(sym, label, n_windows=3):
    rows=json.loads((B/f"{sym}_1m.json").read_text())
    width=cfg.ZONE_WIDTH[sym]; med=cfg.SR_MAX_ENTRY_DIST[sym]; mintp=cfg.SR_MIN_TP_DIST[sym]
    print(f"\n{'='*72}\n{label}  ({sym})  width={width}  max_entry={med}  min_tp={mintp}  | {len(rows)} bar")
    print("="*72)
    # birkaç farklı pencere
    idxs=[len(rows)//4, len(rows)//2, 3*len(rows)//4]
    for k,ix in enumerate(idxs):
        win=rows[max(0,ix-100):ix]
        if len(win)<50: continue
        price=win[-1]["close"]
        zones=detect_zones(win, width=width, min_touch_candles=cfg.ZONE_MIN_TOUCH_CANDLES)
        sup=[z for z in zones if z.center<price]; res=[z for z in zones if z.center>price]
        print(f"\n  [{win[-1]['candle_time'][:16]}] fiyat={price:.2f} | {len(zones)} bölge "
              f"({len(sup)} destek, {len(res)} direnç)")
        for z in zones:
            tag='destek' if z.center<price else 'direnç'
            print(f"      {z.center:9.2f}  {z.touches:2d} dokunuş  {tag}")
        for d in ("BUY","SELL"):
            fixed_tp = price*0.0104 if sym=="USOIL.FOREX" else (67.0 if sym=="GDAXI.INDX" else 80.0)
            fixed_sl = price*0.0149 if sym=="USOIL.FOREX" else 119.0
            p=plan_sr_entry(zones,d,price,fixed_tp_dist=fixed_tp,fixed_sl_dist=fixed_sl,
                            max_entry_dist=med,min_tp_dist=mintp)
            print(f"      {d}: {p.reason if p else 'YOK (uygun S/R yok → açmaz)'}")

demo("GDAXI.INDX","DAX")
demo("USOIL.FOREX","PETROL")
