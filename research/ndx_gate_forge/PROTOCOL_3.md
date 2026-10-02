# Tur 3 — İki raporun karşılaştırmasından türeyen varyasyonlar (ön-kayıt, 2026-10-02)

Karşılaştırılan: `research/ndx_mechanism_round2_20260930/RAPOR.md` (diğer ajan) ↔ bu klasörün RAPOR.md'si.

## Karşılaştırmadan çıkan ortak mekanizma: KOVALAMA CEZASI
Hareket işlem yönünde ZATEN gerçekleşmişken girmek birden çok ölçekte kötü:
- diğer ajan: VIXREG'de M15'i zaten hizalı (aşağı) SELL 115 karar −5,86 p vs diğerleri +11,03 p;
  D3'ün değeri beklemeden değil "fiyatı kovalamama" sınırından geliyor (ablasyon).
- bu klasör: stres günü + önceki dip altında SELL en kötü hücre (−0,18R, 4/4); botun 5m kanal
  tepesinden (karşı-hareketten) SELL'leri iyi; teyit günlük ölçekte ters döner.
- ayrışma: diğer ajanın D4'ü (stres → teyitli BUY, M15↑ şartı) çöktü; bu klasörün T5'i (stres → teyitli SELL) ters döndü.
  İkisi de "teyit beklemek" günlük ölçekte zararlı → teyitsiz kapitülasyon alımı test edilmemiş tek kombinasyon.

## Varyasyonlar (parametreler sabit)

| # | Varyasyon | Tanım | Beklenen |
|---|---|---|---|
| V1 | **Çok-ölçekli kovalama endeksi** | işlem yönünde zaten gerçekleşmiş hareket sayısı (0–4): c1 5m kanal-z (50 bar) yönde ≥1σ; c2 M15 hizalı (kapanış>EMA20 & EMA20 3 bar yükselen, ayna SELL); c3 fiyat önceki RTH ucunun ötesinde (SELL<önceki dip, BUY>önceki tepe); c4 çok-günlük (SELL: dün≤−%1,5 veya 5g≤−%4; BUY: dün≥+%1,5 veya 5g≥+%4) | EV kovalama sayısıyla monoton düşer; SELL'de daha net (korku/coşku asimetrisi) |
| V1-TF | aynı endeks farklı zaman diliminde | c1 15m kanal, c2 M60 hizası | aynı yön |
| V2 | **M15 karşıtlığı** (diğer ajanın betimsel bulgusunun bağımsız sınaması) | botun kapı evreninde SELL: m15 zaten aşağı → yok | 2025 Dukascopy dahil 5 dönemde bloklanan < taban |
| V3 | **Teyitsiz kapitülasyon alımı** (yeni giriş kaynağı) | stres günü, NY 03:00–15:30 arası önceki RTH dibinin altındaki İLK 1m kapanışı → BUY | kontrollerden (stressiz gün aynı olay, aynı gün rastgele saat, aynı olayda SELL) iyi; 10 yıl 1h ile de |

V3 çıkışları: G80 (80/110), GS (1:1, 6×ATR70), GR (2:1), ve "15:55 NY'de kapat" (SL 2×GS mesafesi).
Kapı kriteri: bot kararları + bot-evreni genel + genel 1m (5 dönem) aynı yön; strateji kriteri: 5 dönemin
≥4'ünde EV>0, 10 yılda yılların ≥%60'ında pozitif, maliyet ×1,5'ta pozitif.
