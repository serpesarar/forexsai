"""S07 — TEYİT BEKLEME (kullanıcı fikri: aşağıdaki destek de kırılsın)

Hipotez: 5m kırılımında hemen girme; X puan daha lehte hareket + kapanış
gelirse gir, gelmezse hiç açma.

NASDAQ: tarihsel +8.898$ vs baz +4.290$ görünüyor AMA ayrıştırınca:
  gecikmeli giriş yapılanlar  −7.131$ (giriş KAYBETTİRİYOR)
  hiç açılmayanlar           +19.562$ (kaçınılan)
→ Bu "daha iyi giriş" değil, "momentum devam etmezse açma" FİLTRESİ.

⚠️ BU HAFTA ÇÖKTÜ: +105$ → −2.020$. 4 SL'in hiçbirini engellemedi,
2 TP'yi zarara çevirdi. Mekanik sebep: SL MESAFESİ SABİT kalıyor; SELL'e
aşağıdan girince SL seviyesi de aşağı kayıp fiyata YAKLAŞIYOR.
Tarihsel doğrulama: 13 TP→SL çevrilme (−11.630$) vs 3 kurtarma (+2.570$).
→ ÇÜRÜDÜ.
"""
from bisect import bisect_right
from ortak import sim

ACIKLAMA = "Sinyalden sonra X puan lehte kapanış olursa gir, olmazsa açma"
IZGARA = [{"X": x, "bekle": b} for x in (5, 10, 15, 20, 30) for b in (10, 20, 30, 60)]
VERDIKT_NDX = "ÇÜRÜDÜ — dış-örneklemde −2.020$; giriş bozulması kazananı kesiyor"


def calistir(v, X: float = 5, bekle: int = 60) -> dict:
    out = {}
    for t in v.islemler:
        sgn = 1 if t["yon"] == "BUY" else -1
        teyit = t["o"] + sgn * X
        i = bisect_right(v.bar_ts, t["ts"])
        son = t["ts"] + bekle * 60
        girdi = None
        for k in range(i, len(v.barlar)):
            tt, o, h, l, c = v.barlar[k]
            if tt > son:
                break
            if (c > teyit) if sgn > 0 else (c < teyit):
                girdi = (tt, c)
                break
        if girdi is None:
            out[id(t)] = 0.0
            continue
        pnl, _ = sim.yaris(v, girdi[0], girdi[1], t["yon"], t["tp_d"], t["sl_d"])
        out[id(t)] = pnl * t["lot"]
    return out
