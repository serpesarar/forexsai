# Koşul ızgarası — giriş anı × tutuş × yön × (seans / gün / VIX / EMA-SMA) (ÖN KAYIT, 2026-11-17)

Kullanıcı: "Yeni bir şey bulana kadar işleme giriş yerlerini değiştir; seans, açılış, gün bazında, VIX belirli seviyelerin üstünde/altında,
EMA/SMA üstünde/altında koşullarını değerlendir, bu yerlerde işlem aç ve analiz et."
Veri: Dukascopy NDX BID 1m 2018-01 → 2026-11, ask = BID + spr; VIX yfinance (dünkü kapanış). Motor `research/ndx_10y_1m_20261116/src/lib.py`.
Defter: GF-01 (780 hücre, rastgele girişte durum kapısı X), GF-05 (34 gün koşulu, VIXREG yönü B ama ≈0,01R), SD-01 (koşulsuz saat/seans X),
QS-09 (günlük sıklık X), ORB×VIX, S4, KSG, C3b (bilinen). Yeni olan: giriş anı × tutuş × iki koşullu kesişim tek ızgarada, iki kör dönemle.

## Hücreler
- Giriş anı (NY saati, o dakikada açılan bar): A1 18:00 (Asya açılışı, önceki akşam), A2 20:00, A3 03:00 (Avrupa), A4 08:30, A5 09:30 (NY açılış),
  A6 10:00, A7 11:00, A8 12:00, A9 13:00, A10 14:00, A11 15:00, A12 15:30, A13 16:00.
- Tutuş: 60 dk, 120 dk, 240 dk, "seans sonu" (Asya/Avrupa girişleri → 09:30; NY girişleri → 15:55; 16:00 girişi → ertesi 09:30), 1 gün (ertesi gün aynı saat).
  16:15–18:00 boşluğuna düşen çıkış bir sonraki bara kayar.
- Yön: AL / SAT.
- Koşullar (girişten önce bilinen; günlük olanlar önceki kapanışlarla):
  VIX kovası {<15, 15–18,4, 18,4–25, ≥25}; dünkü NDX kapanışı EMA20/50/200 ve SMA20/50/200 üstü/altı; dünkü gün yukarı/aşağı;
  haftanın günü (Pzt…Cum); (09:30 ve sonrası) açılış boşluğu yukarı/aşağı; (10:00 ve sonrası) girişte fiyat günün açılışının üstü/altı.
  Tekli koşul + iki koşul kesişimi (aynı aileden ikili yok).
## Seçim ve doğrulama
- KEŞİF = 2018-01 → 2021-12; KÖR-1 = 2022-01 → 2023-12; KÖR-2 = 2024-01 → 2026-11.
- Ölçü: net bp/işlem (spread; tutuş ≥ 1 gece uzunsa finansman). Hücre şartı: KEŞİF n ≥ 60.
- Seçim: KEŞİF t ≥ T*, T* = koşul etiketlerini günler arasında karıştırarak (giriş/tutuş/yön sabit) 200 permütasyonda en büyük t'nin %95'i (maxT).
- **Geçer:** KÖR-1 ve KÖR-2'nin İKİSİNDE de ort > 0 ∧ ay-blok P ≥ 0,90 ∧ spr×1,5 ile > 0. Seçilenler arasında Holm (KÖR-1 ∪ KÖR-2 birleşik p).
- Geçen hücre "yeni" sayılmak için: ORB×VIX, S4, KSG, C3b, CAPREV, FOMC gecesi, ay sonu ile işlem günlerinin ≤ %50'si örtüşmeli; aksi hâlde
  "bilinen ailenin yeniden bulunuşu" diye raporlanır. Yeni ve geçen hücre için 2. KURAL kartı + mevcut kitaba katkı (aylık Sharpe, E110).

## EK-1 (2026-11-17, ilk tur sonucundan SONRA, koşulmadan önce yazıldı)
İlk tur: 23.994 hücre, KEŞİF (2018–21) maxT eşiği 4,81; en büyük t 3,94 (permütasyon max ort. 4,12) → seçilen 0. KÖR-2 (2024–26) hiç açılmadı.
Güç için iki değişiklik (ikisi de sonuç değil tasarım kararı): (1) KEŞİF = 2018-01 → 2023-12 (6 yıl), KÖR = 2024-01 → 2026-11;
(2) hücre ailesi daraltılır: tekli koşullar + yalnız VIX × diğer koşul ikilileri (gerekçe: defterdeki tek kanıtlı mekanizma korku/VIX, §3-21).
Seçim yine maxT %95 (200 permütasyon). Geçer: KÖR'de ort > 0 ∧ P ≥ 0,95 ∧ spr×1,5 > 0 ∧ KEŞİF'in iki yarısında (2018–20, 2021–23) da > 0.
Geçen hücre bilinen ailelerle (ORB×VIX, S4, KSG, C3b, CAPREV) örtüşme denetiminden geçer.

## EK-2 (2026-11-17, EK-1 sonucundan sonra, koşulmadan önce)
EK-1: 11.340 hücre, en büyük t 3,59 < maxT 4,25 → seçilen 0. Güç kontrolü: iki dönemde doğrulanmış S4 bu ızgarada t 1,3–1,6 → aile düzeyli
maxT, NDX'teki gerçek kenar büyüklüğünü (5–15 bp, σ ≫ 100 bp) göremez. Keşif amaçlı ikinci aşama:
- KEŞİF'in (2018–23) en iyi 30 hücresi (t'ye göre; aynı (giriş anı, yön, koşul) için tek tutuş — en yüksek t'li) → KÖR (2024–26).
- Tekrar = KÖR'de ort > 0 ∧ P ≥ 0,90. Şans beklentisi ≈ %10 → 3/30. Kontrol: en KÖTÜ 30 hücrenin "ters" tekrarı (KÖR'de ort < 0 ∧ P ≤ 0,10).
- Aday = tekrarlayan hücre ∧ KÖR P ≥ 0,95 ∧ spr×1,5 > 0 ∧ KEŞİF'in iki yarısında da > 0. Aday varsa: kart + bilinen ailelerle örtüşme + kitap katkısı.

## EK-3 (2026-11-17, EK-2 sonucundan sonra, koşulmadan önce) — adayların kontrolü
EK-2: 8/30 tekrar (beklenen 3, binom p 0,008). Adaylar iki aile: (1) Pazartesi 03:00/08:30/09:30 → +1 gün uzun; (2) VIX 18–25 ∧ fiyat
ortalama üstü → 16:00 AL, 60–120 dk (Dukascopy'de çıkış = 18:00 yeniden açılış barı).
- (1) Kural P1: Pazartesi 03:00 ET AL (ask) → Salı 03:00 SAT (bid), finansmanlı, haftada 1. Kontroller: aynı kuralın Sal/Çar/Per/Cum karşılığı
  (gün plasebosu), 1 dk geç giriş, yıl tablosu, spr×1,5, en iyi 5 hariç, yarılar; bilinen kurallarla gün örtüşmesi; kitaba 0,5 lot ekleme Sharpe'ı
  (ESKİ ≤ 2021-10 / YENİ). Ayrıca 08:30 ve 09:30 girişleri yan ölçüm. Kart 6 ölçütü (2. KURAL).
- (2) Yeniden açılış artefaktı (E97): aynı kural, çıkış 18:00 yerine 18:05 / 18:15 / 18:30 açılışı; kazanç ilk barda toplanıyorsa artefakt.
