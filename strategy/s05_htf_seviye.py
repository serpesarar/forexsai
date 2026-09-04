"""S05 — ÜST ZAMAN DİLİMİ SEVİYE FİLTRESİ (kullanıcı gözlemi)

Hipotez: bot 1m/5m kırılımıyla giriyor ama M15/M30/H1'deki eski destek/direnci
görmüyor; fiyat oraya çarpıp dönüyor. Yola engel olan seviye varsa açma.

⚠️ SİSTEM KÖRLÜĞÜ GERÇEK: giriş S/R tespiti YALNIZ 1m × 100 bar (~1,7 saat).
M15/M30/H1 pivotları giriş yolunda hiç kontrol edilmiyor.

NASDAQ verdikti: sinyal gerçek ama zayıf (SL'lerin önündeki seviye medyan
36,6 puan, TP'lerin 44,1). Rafine sürüm (≥2 dokunuş) İÇ-örneklemde MÜKEMMELDİ
(plato 9/9, hafta 9/9, permütasyon p=0,0033) ama BU HAFTA ters döndü:
engellediği 3 işlemin 3'ü de TP, 4 SL'in dördünü de geçirdi.
→ ÇÜRÜDÜ. Bu oturumun en net dersi: iç-örneklem dayanıklılığı yetmez.
"""
from ortak import sim

ACIKLAMA = "Giriş ile TP arasında >=dokunus dokunuşlu HTF seviyesi varsa açma"
IZGARA = [{"tf": tf, "geri": g, "dokunus": d}
          for tf in (15, 30, 60) for g in (30, 50, 100) for d in (1, 2, 3)]
VERDIKT_NDX = "ÇÜRÜDÜ — in-sample mükemmel, dış-örneklemde tam ters"


def calistir(v, tf: int = 15, geri: int = 50, dokunus: int = 2) -> dict:
    bars = v.resample(tf)
    out = {}
    for t in v.islemler:
        sgn = 1 if t["yon"] == "BUY" else -1
        hedef = t["o"] + sgn * t["tp_d"]
        engel = False
        for tip, p, n in sim.pivotlar(bars, f"tf{tf}", t["ts"], geri):
            if n < dokunus:
                continue
            if sgn < 0 and tip == "S" and hedef < p < t["o"]:
                engel = True
                break
            if sgn > 0 and tip == "R" and t["o"] < p < hedef:
                engel = True
                break
        out[id(t)] = 0.0 if engel else t["usd"]
    return out
