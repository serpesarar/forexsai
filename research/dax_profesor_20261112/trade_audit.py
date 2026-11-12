"""DAX (GER40) bot işlemleri: aile / yön / saat / gün / tutma süresi dökümü.
R = gerçekleşen puan / ilk risk; ilk risk bilinmiyorsa yorum etiketindeki [sl] kapanış stopu kullanılır
(BE yönetimi stopu taşıdığı için R yalnız SL-kapanışlarında güvenilir -> ana ölçü puan ve $)."""
import json, collections, statistics as st
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
B = 52890969
FAM = {B: "MOM/SR (momentum)", B+1: "CHREV (kanal dönüşü)", B+2: "VIXREG", B+4: "DAYCOMBO", B+6: "REENTRY",
       B+7: "CAPREV", B+8: "C3b", B+9: "ORB×VIX", B+10: "ÇEKİÇ", 52890989: "DECIDER", 0: "elle"}
d = json.load(open("research/dax_profesor_20261112/data/dax_trades.json"))
BER = ZoneInfo("Europe/Berlin")
rows = []
for t in d:
    ot = datetime.fromisoformat(t["open_time"]); ct = datetime.fromisoformat(t["close_time"])
    sgn = 1 if t["direction"].upper().startswith("B") else -1
    pts = (t["close_price"] - t["open_price"]) * sgn
    net = t["profit"] + (t["commission"] or 0) + (t["swap"] or 0)
    how = (t["comment"] or "")[:3]
    rows.append(dict(fam=FAM.get(t["magic"], str(t["magic"])), dir=t["direction"], ot=ot, ct=ct, pts=pts, net=net,
                     vol=t["volume"], how=how, hold=(ct-ot).total_seconds()/60, op=t["open_price"], cp=t["close_price"]))
print("UYARI: open_time zaman dilimi denetimi -> ilk 5 açılış (UTC, Berlin):")
for r in rows[:5]: print(" ", r["ot"].isoformat(), r["ot"].astimezone(BER).strftime("%H:%M"), r["fam"])
def summ(g, title):
    print(f"\n== {title} ==")
    print(f"{'grup':34s} {'n':>3s} {'WR%':>5s} {'net$':>8s} {'ort puan':>8s} {'med tut dk':>10s} {'TP':>3s} {'SL':>3s}")
    for k, v in sorted(g.items(), key=lambda x: -len(x[1])):
        n = len(v); w = sum(r["pts"] > 0 for r in v)
        print(f"{str(k):34s} {n:3d} {100*w/n:5.1f} {sum(r['net'] for r in v):8.0f} {st.mean(r['pts'] for r in v):8.1f} "
              f"{st.median(r['hold'] for r in v):10.0f} {sum(r['how']=='[tp' for r in v):3d} {sum(r['how']=='[sl' for r in v):3d}")
def grp(key): 
    g = collections.defaultdict(list)
    for r in rows: g[key(r)].append(r)
    return g
summ(grp(lambda r: r["fam"]), "Aile")
summ(grp(lambda r: (r["fam"], r["dir"])), "Aile × yön")
summ(grp(lambda r: r["ot"].astimezone(BER).hour), "Açılış saati (Berlin)")
summ(grp(lambda r: r["ot"].astimezone(BER).strftime("%a")), "Gün")
summ(grp(lambda r: r["ot"].strftime("%Y-%m")), "Ay")
summ(grp(lambda r: "≤30dk" if r["hold"]<=30 else "30-120" if r["hold"]<=120 else "120-480" if r["hold"]<=480 else ">8sa"), "Tutma süresi")
# SL'lerde yön doğru muydu? (kapanıştan sonra fiyat lehte gitti mi bilinmiyor -> ayrı adım)
json.dump([{**r, "ot": r["ot"].isoformat(), "ct": r["ct"].isoformat()} for r in rows],
          open("research/dax_profesor_20261112/data/dax_trades_flat.json", "w"), default=str)
