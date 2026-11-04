# Ön-kayıt — Zaman Makinesi kalibrasyonu (TM-01)

2026-11-04, sonuç görülmeden. Kullanıcı github.com/jakeschincariol/day-trader-skill reposunu getirdi ("mum eşleştirme
algoritması varmış"). İnceleme: repoda grafik benzerliği/mum eşleştirme YOK; en yakın bileşen trader-timemachine — bir işlem
planının (giriş/stop/hedef) olasılığını, son 60 seansın AYNI GÜN-SAATİNDEKİ 5m mumlarından Monte Carlo ile verir.
`backend/services/time_machine_service.py` bu yöntemin CFD'ye uyarlanmış birebir taşıması (simulate orijinalle tohum-
eşit sayılar üretiyor). Bu sınama aracın iddiasını ölçer: verdiği olasılıklar GERÇEKLEŞEN sıklıklarla tutuyor mu?

- Veri: `backend/data/candle_history/{NDX,XAUUSD,USOIL}_5m.npz` (broker, UTC). DAX 5m arşivde yok → kapsam dışı.
- Sorgular: her sembolde ilk 65 broker gününden sonra her 97 barda bir (≈8 saat) kapanmış bar; plan: buy ve sell,
  stop = 1×ATR14(5m), hedef 1R, ufuk 24 bar (2 saat, broker günü sonunda kesilir). Havuz: sorgu gününden ÖNCEKİ son 60
  dolu seans (sızıntı yok). 1.000 simülasyon, tohum 19.
- Gerçekleşen: sorgudan sonraki gerçek barlarda aynı stop-önce kuralıyla hedef önce / stop önce / hiçbiri.
- Kıyas: iklim tabanı = TÜM sorguların gerçekleşen hedef-önce oranı (sabit; bu taban geleceği bildiği için iyimser).
- Ölçütler (birincil hedef-önce olayı): (1) Brier(araç) ≤ Brier(iklim tabanı); (2) tahmin ondalık kovalarında
  |tahmin − gerçekleşen| ortalaması ≤ 5 puan; (3) aynı ikisi stop-önce olayı için. Geçerse: "olasılıklar kalibre" —
  bu bir yön/kenar iddiası DEĞİL; yalnız aracın verdiği sayıların dürüst olduğunu gösterir.

## Ek (sonradan, birincil sonuç görüldükten sonra eklendi — TM-01b)
Aracın ikinci yazılı iddiası: "ufuk sonunda fiyatın %90'ı p5–p95 arasında". Aynı sorgularda gerçekleşen ufuk-sonu kapanışın
p5–p95 (hedef %90) ve p25–p75 (hedef %50) aralığına düşme oranı ölçülür; kıyas: aynı genişlikte, girişte ortalanmış ama
yalnız son 60 seansın TÜM saatlerinden kurulan (saat koşulsuz) aralık. Ölçüt: kapsama hedefin ±5 puanı içinde.
