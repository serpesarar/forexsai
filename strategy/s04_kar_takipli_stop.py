"""S04 — KÂR TAKİPLİ STOP (kullanıcı fikri)

Hipotez: MFE ≥ tetik×TP_mesafesi olunca SL'i giriş + oran×zirve'ye çek, takip et.

NASDAQ verdikti: SL'lerin %33'ünü kurtarıyor (+21.630$) AMA kazananların
%67'sini kesiyor (−27.130$) → net −5.106$. WR %60→%73 ("kozmetik WR").
48 hücrenin 46'sı bazın altında; kullanıcının sorduğu gevşetme yönü en kötüsü.
⚠️ Sıkılaştırma (oran→0,99) monoton iyileşiyor = SINIR ARTEFAKTI ("tepeden sat").
→ ÇÜRÜDÜ. Tek kalıntı: %70 tetik/%90 oran maxDD'yi −8.538→−5.910 iyileştiriyor.
"""
from bisect import bisect_right
from ortak import sim

ACIKLAMA = "MFE >= tetik×TP olunca SL = giriş + oran×zirve (takipli)"
IZGARA = [{"tetik": a, "oran": b} for a in (0.3, 0.5, 0.7) for b in (0.3, 0.5, 0.7, 0.9)]
VERDIKT_NDX = "ÇÜRÜDÜ — WR +13pp ama para −5.106$; sıkılaştırma sınır artefaktı"


def calistir(v, tetik: float = 0.5, oran: float = 0.5, saat: int = 48) -> dict:
    out = {}
    for t in v.islemler:
        sgn = 1 if t["yon"] == "BUY" else -1
        sl, tp = t["o"] - sgn * t["sl_d"], t["o"] + sgn * t["tp_d"]
        mfe = 0.0
        i = bisect_right(v.bar_ts, t["ts"])
        end = t["ts"] + saat * 3600
        px = None
        for k in range(i, len(v.barlar)):
            tt, o, h, l, c = v.barlar[k]
            if tt > end:
                px = c
                break
            ters = l if sgn > 0 else h
            lehte = h if sgn > 0 else l
            if (ters <= sl) if sgn > 0 else (ters >= sl):
                px = sl
                break
            if (lehte >= tp) if sgn > 0 else (lehte <= tp):
                px = tp
                break
            yeni = sgn * (lehte - t["o"])
            if yeni > mfe:
                mfe = yeni
            if mfe >= tetik * t["tp_d"]:
                aday = t["o"] + sgn * oran * mfe
                if (aday > sl) if sgn > 0 else (aday < sl):
                    sl = aday
        if px is None:
            px = v.barlar[-1][4]
        out[id(t)] = (sgn * (px - t["o"]) - sim.SPREAD) * t["lot"]
    return out
