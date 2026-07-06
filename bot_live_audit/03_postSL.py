"""
03 — SL SONRASI FİYAT YOLU + İNVERSİYON SİMÜLASYONU.
Soru: SL olduktan sonra fiyat geri dönüp TP'yi vurur muydu? (SL çok dar = TP/SL sorunu)
      yoksa devam mı etti? (yön yanlış = model sorunu)
Fiyat kaynağı füzyonu (sembol bazında, en iyiden):
  1m bar (lo/hi) > 3-5dk snapshot close (XAU/USOIL) > temiz 1h (NDX/GDAXI) > işlem fill'leri (evrensel)
Muhafazakâr: sparse veride favorable-reach ALT SINIR; inversiyon first-touch'ta adverse önce sayılır.
"""
import json, statistics as st
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path("/Users/melihcanodacioglu/Desktop/panel"); B=ROOT/"bot_live_audit"/"bars"
P=json.loads((ROOT/"bot_live_audit"/"positions.json").read_text())
def ts(s): return datetime.fromisoformat(s).timestamp()

# ---- sembol bazında median tp/sl mesafe (would-be TP için) ----
tp_med=defaultdict(list); sl_med=defaultdict(list)
for p in P:
    if p["close_reason"]=="tp" and p["trig_dist"]: tp_med[p["symbol"]].append(p["trig_dist"])
    if p["close_reason"]=="sl" and p["trig_dist"]: sl_med[p["symbol"]].append(p["trig_dist"])
TPM={s:st.median(v) for s,v in tp_med.items()}
SLM={s:st.median(v) for s,v in sl_med.items()}

# ---- price marks füzyonu ----
def load_bars(sym):
    marks=[]  # (t, lo, hi)
    f1=B/f"{sym}_1m.json"
    if f1.exists():
        for b in json.loads(f1.read_text()):
            marks.append((ts(b["candle_time"]), b["low"], b["high"]))
    f2=B/f"{sym}_1h.json"
    if f2.exists():
        rows=json.loads(f2.read_text())
        tlist=[ts(r["candle_time"]) for r in rows]
        gap=st.median([tlist[i+1]-tlist[i] for i in range(min(300,len(tlist)-1))]) if len(rows)>2 else 3600
        if gap < 900:   # snapshot serisi → close'u nokta fiyat al
            for r in rows: marks.append((ts(r["candle_time"]), r["close"], r["close"]))
        else:           # temiz saatlik → lo/hi bant
            for r in rows: marks.append((ts(r["candle_time"]), r["low"], r["high"]))
    return marks

MARKS=defaultdict(list)
for sym in ["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]:
    MARKS[sym]+=load_bars(sym)
# işlem fill'leri (evrensel nokta fiyat) — entry & exit
for p in P:
    MARKS[p["symbol"]].append((ts(p["entry_time"]), p["entry_px"], p["entry_px"]))
    MARKS[p["symbol"]].append((ts(p["exit_time"]),  p["exit_px"],  p["exit_px"]))
for s in MARKS: MARKS[s].sort()

import bisect
def marks_between(sym, t0, t1):
    arr=MARKS[sym]; keys=[m[0] for m in arr]
    i=bisect.bisect_right(keys,t0); j=bisect.bisect_right(keys,t1)
    return arr[i:j]

# ======== SL SONRASI ANALİZ ========
print("="*78)
print("SL SONRASI: fiyat geri dönüp would-be TP'yi vurur muydu? (horizon dakika)")
print("  reachTP% = SL'den sonra entry yönünde median-TP mesafesine ulaşma (ALT SINIR)")
print("  recov%   = entry'ye geri dönme | advExt = SL ötesi ek ortalama gidiş (R)")
print("="*78)
H=[15,60,240]
for sym in ["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]:
    sl_tr=[p for p in P if p["symbol"]==sym and p["close_reason"]=="sl" and p["trig_dist"]]
    if not sl_tr: continue
    tpm=TPM.get(sym, st.median([p["trig_dist"] for p in sl_tr]))
    print(f"\n{sym}  (SL n={len(sl_tr)}, would-be TP mesafe={tpm:.3f}, SL mesafe med={st.median([p['trig_dist'] for p in sl_tr]):.3f})")
    for h in H:
        reach=recov=adv=0; advs=[]
        for p in sl_tr:
            D = 1 if p["direction"]=="BUY" else -1
            E=p["entry_px"]; sl_dist=p["trig_dist"]
            tp_lvl = E + D*tpm
            t0=ts(p["exit_time"]); mk=marks_between(sym, t0, t0+h*60)
            if not mk: continue
            fav=max(D*(m[2]-E) if D>0 else D*(m[1]-E) for m in mk)  # favorable max (BUY:hi, SELL:lo)
            advx=max(-D*(m[1]-E) if D>0 else -D*(m[2]-E) for m in mk) # adverse max beyond entry
            if (D>0 and any(m[2]>=tp_lvl for m in mk)) or (D<0 and any(m[1]<=tp_lvl for m in mk)): reach+=1
            if fav>=0: recov+=1
            advs.append((advx - sl_dist)/sl_dist)  # SL ötesi ek (R)
        nn=sum(1 for p in sl_tr if marks_between(sym, ts(p["exit_time"]), ts(p["exit_time"])+h*60))
        if nn:
            print(f"   +{h:4d}dk: reachTP={reach/nn*100:5.1f}%  recov={recov/nn*100:5.1f}%  "
                  f"advExt_med={st.median(advs):+.2f}R  (kapsanan {nn}/{len(sl_tr)})")

# ======== İNVERSİYON SİMÜLASYONU ========
# Aynı entry, aynı tp/sl MESAFE, ama yön TERS. İlk dokunan kazanır. Adverse-first (muhafazakâr).
print("\n"+"="*78)
print("İNVERSİYON SİM: her işlemin YÖNÜNÜ ters çevir (aynı tp/sl mesafe), ilk-dokunuş")
print("  orig→ şu an olan | inv→ ters çevirince. WR ve R-beklenti (maliyet hariç).")
print("="*78)
def first_touch(sym, t0, E, up_lvl, dn_lvl, maxmin=1440):
    """ up_lvl > E > dn_lvl. Hangi seviye önce dokunulur? 'up'/'dn'/None. Adverse-first muhafazakar:
        bir mark hem up hem dn'i kapsıyorsa, test edilen yönün aleyhine say (çağıran ayarlar)."""
    for t,lo,hi in marks_between(sym,t0,t0+maxmin*60):
        hit_up = hi>=up_lvl; hit_dn = lo<=dn_lvl
        if hit_up and hit_dn: return "both"
        if hit_up: return "up"
        if hit_dn: return "dn"
    return None
for sym in ["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]:
    trs=[p for p in P if p["symbol"]==sym and p["close_reason"] in ("tp","sl") and p["trig_dist"]]
    tpm=TPM.get(sym); slm=SLM.get(sym)
    if not trs or not tpm or not slm: continue
    inv_w=inv_l=cov=0; inv_R=[]
    for p in trs:
        D=1 if p["direction"]=="BUY" else -1
        E=p["entry_px"]; t0=ts(p["entry_time"])
        # INVERTED yön = -D. inv TP = E + (-D)*tpm ; inv SL = E + (-D)*slm... ama mesafeyi koruyoruz:
        # inverted trade kazanır eğer fiyat -D yönünde tpm kadar, +D yönünde slm'den ÖNCE giderse
        up_lvl = E + tpm if -D>0 else E + slm   # BUY-orig(D=1)→inv SELL: TP aşağıda(dn), SL yukarıda(up=slm)
        dn_lvl = E - slm if -D>0 else E - tpm
        # netleştir: inv yön = -D. favorable(inv)= -D.
        if -D>0:  # inverted BUY: TP yukarı tpm, SL aşağı slm
            up_lvl=E+tpm; dn_lvl=E-slm; fav="up"
        else:     # inverted SELL: TP aşağı tpm, SL yukarı slm
            up_lvl=E+slm; dn_lvl=E-tpm; fav="dn"
        ft=first_touch(sym,t0,E,up_lvl,dn_lvl)
        if ft is None: continue
        cov+=1
        if ft=="both": ft = "up" if fav=="dn" else "dn"  # adverse-first
        if ft==fav: inv_w+=1; inv_R.append(tpm/slm)       # +tp in R units (R=slm)
        else:       inv_l+=1; inv_R.append(-1.0)
    if cov:
        wr=inv_w/cov*100; exp=st.mean(inv_R)
        # mevcut (orig) gerçek
        ow=sum(1 for p in trs if p["pnl"]>0); o_wr=ow/len(trs)*100
        print(f"{sym:12s} orig WR={o_wr:5.1f}% | INV WR={wr:5.1f}% exp={exp:+.3f}R/işlem (kapsanan {cov}/{len(trs)})")
