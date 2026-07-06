"""
01 — MT5 işlem geçmişi rekonstrüksiyonu + ekonomi (FİYAT VERİSİ GEREKMEZ).

Girdi : sonislemler/mt5_islemler_*.csv  (deal-level, pozisyon_id ile)
Çıktı : bot_live_audit/positions.json   (round-trip pozisyon tablosu)
        + ekrana sembol / yön / model bazında ekonomi.

Semantik (ampirik doğrulandı):
  - 2 deal/pozisyon: erken=GİRİŞ (kar_zarar==0, yon=pozisyon yönü), geç=ÇIKIŞ.
  - GİRİŞ yorum  : 'ForexSAI_demo' | 'FX|<S/W>|<combo>|<conf>'  → sinyal metadata
  - ÇIKIŞ yorum  : '[tp X]' | '[sl X]' | 'dir_flip'            → kapanış sebebi + seviye
"""
from __future__ import annotations
import csv, json, re, statistics as st
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
CSV  = next((ROOT/"sonislemler").glob("mt5_islemler_*.csv"))
OUT  = ROOT/"bot_live_audit"/"positions.json"

SYMBOL_MAP = {"USTEC":"NDX.INDX","DE40":"GDAXI.INDX","XTIUSD":"USOIL.FOREX","XAUUSD":"XAUUSD"}

def parse_time(s:str)->datetime:
    return datetime.strptime(s.replace(" UTC",""), "%Y-%m-%d %H:%M:%S")

def parse_entry_comment(c:str):
    c=c.strip()
    if c.startswith("FX|"):
        p=c.split("|")
        strength = p[1] if len(p)>1 else None         # S / W
        combo    = p[2] if len(p)>2 else None          # flip / emel+pulse1 / emel+ml ...
        conf     = None
        if len(p)>3:
            try: conf=float(p[3])
            except: conf=None
        return {"combo":combo,"strength":strength,"conf":conf}
    if "demo" in c.lower():
        return {"combo":"legacy_demo","strength":None,"conf":None}
    return {"combo":c[:24],"strength":None,"conf":None}

def parse_exit_comment(c:str):
    c=c.strip()
    m=re.match(r"\[(tp|sl)\s+([\d.]+)\]", c)
    if m: return {"reason":m.group(1), "level":float(m.group(2))}
    if "flip" in c: return {"reason":"dir_flip","level":None}
    return {"reason":"other:"+c[:16],"level":None}

# ---- yükle + grupla ----
rows=[]
with open(CSV, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)
by_pos=defaultdict(list)
for r in rows:
    by_pos[r["pozisyon_id"]].append(r)

positions=[]; singles=0; anomalies=0
for pid, ds in by_pos.items():
    if len(ds)!=2:
        singles+=1; continue
    ds=sorted(ds, key=lambda x:x["zaman"])
    e,x = ds[0], ds[1]
    # giriş kar_zarar==0 olmalı; değilse zaman sıralamasına güven ama işaretle
    if float(e["kar_zarar"])!=0.0: anomalies+=1
    sym_mt5 = e["sembol"]
    sym     = SYMBOL_MAP.get(sym_mt5, sym_mt5)
    direction = e["yon"]                       # giriş yönü = pozisyon yönü
    entry_px = float(e["fiyat"]); exit_px=float(x["fiyat"])
    lot      = float(e["lot"])
    pnl      = float(x["kar_zarar"]) + float(x.get("swap",0) or 0)  # net realize
    pnl_raw  = float(x["kar_zarar"])
    em       = parse_entry_comment(e["yorum"])
    xm       = parse_exit_comment(x["yorum"])
    t_in     = parse_time(e["zaman"]); t_out=parse_time(x["zaman"])
    hold_min = (t_out - t_in).total_seconds()/60.0
    # tetiklenen seviyeye olan mesafe (puan cinsinden)
    trig_dist=None
    if xm["level"] is not None:
        trig_dist = abs(entry_px - xm["level"])
    positions.append({
        "pid":pid, "symbol":sym, "symbol_mt5":sym_mt5, "direction":direction,
        "entry_time":t_in.isoformat(), "exit_time":t_out.isoformat(),
        "entry_px":entry_px, "exit_px":exit_px, "lot":lot,
        "pnl":pnl_raw, "pnl_net":pnl, "pnl_per_lot": pnl_raw/lot if lot else 0,
        "close_reason":xm["reason"], "level":xm["level"], "trig_dist":trig_dist,
        "combo":em["combo"], "strength":em["strength"], "conf":em["conf"],
        "hold_min":round(hold_min,1),
    })

positions.sort(key=lambda p:p["entry_time"])
OUT.write_text(json.dumps(positions, indent=1))
print(f"CSV: {CSV.name}")
print(f"deal={len(rows)}  pozisyon_grubu={len(by_pos)}  round-trip={len(positions)}  tek-bacak={singles}  anomali(giriş kz!=0)={anomalies}")
print(f"yazıldı → {OUT}")

# ---- implied point value (çapraz kontrol) ----
print("\n=== IMPLIED POINT VALUE ($/1.0 fiyat / 1.0 lot) — tp/sl kapanışlardan ===")
pv=defaultdict(list)
for p in positions:
    if p["close_reason"] in ("tp","sl") and p["trig_dist"]:
        pv[p["symbol"]].append(abs(p["pnl"])/(p["trig_dist"]*p["lot"]))
for s in sorted(pv):
    print(f"  {s:12s} ~{st.median(pv[s]):.3f}   (n={len(pv[s])})")

def econ(rows, label):
    n=len(rows)
    if n==0: return
    wins=[r for r in rows if r["pnl"]>0]; losses=[r for r in rows if r["pnl"]<0]
    flat=[r for r in rows if r["pnl"]==0]
    wr = len(wins)/n*100
    aw = st.mean([r["pnl"] for r in wins]) if wins else 0
    al = st.mean([r["pnl"] for r in losses]) if losses else 0
    awl= st.mean([r["pnl_per_lot"] for r in wins]) if wins else 0
    all_=st.mean([r["pnl_per_lot"] for r in losses]) if losses else 0
    payoff = (awl/abs(all_)) if all_ else float('inf')
    be_wr  = 100/(1+payoff) if payoff not in (0,float('inf')) else float('nan')
    tot = sum(r["pnl"] for r in rows)
    exp = tot/n
    print(f"  {label:30s} n={n:4d} WR={wr:5.1f}% | avgW/lot={awl:8.1f} avgL/lot={all_:8.1f} "
          f"payoff={payoff:4.2f} beWR={be_wr:5.1f}% | netΣ={tot:10.1f} exp/trade={exp:7.1f}")

print("\n=== SEMBOL BAZINDA EKONOMİ (round-trip, net P/L) ===")
bysym=defaultdict(list)
for p in positions: bysym[p["symbol"]].append(p)
for s in sorted(bysym):
    econ(bysym[s], s)
econ(positions, "TÜMÜ")

print("\n=== SEMBOL × YÖN ===")
for s in sorted(bysym):
    for d in ("BUY","SELL"):
        sub=[p for p in bysym[s] if p["direction"]==d]
        if sub: econ(sub, f"{s} {d}")

print("\n=== KAPANIŞ SEBEBİ DAĞILIMI (sembol×reason) ===")
cr=defaultdict(lambda:defaultdict(int))
for p in positions: cr[p["symbol"]][p["close_reason"]]+=1
for s in sorted(cr):
    parts=" ".join(f"{k}={v}" for k,v in sorted(cr[s].items()))
    print(f"  {s:12s} {parts}")
