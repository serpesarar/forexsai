# HEKA kitabı → kapı/strateji denemesi — sonuç (2026-10-21)

**Sonuç: kitaptan kullanılabilir kapı veya strateji çıkmadı.** Ön kayıt `PROTOCOL.md` (+EK-1). Betikler bu klasörde,
çıktılar `results/` (`ozet.csv` ön-kayıtlı ölçüt tablosu).

## Kitap ne içeriyor
123 sayfalık genel TA ders kitabı (yazara göre %30'u yapay zekâyla yazılmış). Parametreli kural çok az. Fikirlerin
çoğu Kapı Kayıt Defteri'nde zaten sınanmış ve elenmişti: mum desenleri (MK-01/02/05), grafik/harmonik formasyonlar
(PATTERN_BONUS, PM), MACD (OLD-12), BB sıkışma (MK-07), retest/teyit girişi (fakeout lab), trailing/BE (M9),
yuvarlak sayı (GF-02), hacimli kırılım (T3). CVD için gerçek emir akışı verimiz yok, bu yüzden sınanamadı.
Defterde karşılığı olmayan dört fikir sınandı.

## Sonuçlar (4 sembol: NDX, DAX, XAU, OIL · 30m 2021→2026, 1h 2016/2019→2026 · sonraki bar açılışı + spread · eşli plasebo)

| ID | Fikir | Ana sonuç | Karar |
|---|---|---|---|
| HK-1 | 3 EMA 10/25/50 dizilim kesişimi (çıkışlar: kitabın EMA10/25 ters kesişimi · SL1,5/TP3 ATR · 20 bar) | 12 havuz hücresinin hiçbiri Holm'dan geçmedi. SELL'ler mutlak negatif. Sınırda kalan **30m BUY + kitap çıkışı**: +0,121R, plaseboya fark +0,096, p 0,002 (Holm eşiği 0,0014); iki dönemde de pozitif, 4/4 sembol, ×1,5 spread +0,107. Ama R'nin %76'sı en iyi 20 günden geliyor. Zaten dizilimde olan rastgele barlara karşı fark yalnız +0,061. **Görülmemiş ileri dönemde (broker 15m→30m, 07/09→10-21): 109 işlem, −0,247R, fark −0,210 (P 0,03); 4 sembolün 3'ünde negatif** | **X** |
| HK-2 | Değer alanı (AMT/Dalton "%80 kuralı"): değer alanı dışında açılış → VA'ya dönüş → karşı kenar | Karşı kenara ulaşma oranı %44–50 (iddia %80). R ≈ 0 (BUY −0,028, SELL −0,023), plaseboya fark ≈ 0 | **X** |
| HK-3 | "S/R ne kadar çok test edilirse kırılma o kadar olası" | Yaklaşınca kırılma olasılığı dokunuş sayısından bağımsız ≈ %77 (1h'de 2→4+ arası +1,3 puan, 30m'de sıfır). Kırılım yönünde ±1 ATR işlemler her kovada negatif (−0,05…−0,08R). 4+ dokunuş ile 2 dokunuş arasındaki fark 1h −0,003, 30m +0,02 (P 0,93) | **X** |
| HK-4 | RSI Sınıf A diverjansı giriş olarak (± aşırı alım/satım şartı) | 16 hücrenin hiçbiri geçmedi. Diverjansı olmayan aynı yeni-dip/tepe yapısına karşı fark −0,06…+0,045, hiçbiri P ≥ 0,95 değil. "Korku döner" öngörüsüne uygun olarak boğa > ayı, ama farkı RSI değil yapının kendisi yaratıyor | **X** |

## Sembol bazında (sonradan, `per_symbol.py` + `fwd_symbol.py`)
Karar havuzda verildi ama simülasyon her sembolde ayrı yapıldı. 144 sembol×hücre: düzeltmesiz P≥0,95 olan **11**
hücre var, tesadüfen beklenen ~7,2. Holm'dan **1** hücre geçti: HK-3 NDX 30m 4+ dokunuş kırılımı. O hücrede de mutlak
R negatif (−0,019): plasebodan "daha az kötü", ama işlem yapılacak bir strateji değil. Dönem ve maliyet ölçütlerini
geçen 4 hücrenin hepsi XAU'da çıktı ve hepsi ileri dönemde negatif:
XAU 30m EMA BUY (n 28, −0,59R), XAU 1h boğa diverjansı RSI<30 (n 1), XAU 30m ayı diverjansı (n 11, −0,19R).

## Notlar
- HK-1 ek kontrolü (`hk1_x1_check.py`) sonradan eklendi ve öyle işaretlendi. Bağlayıcı ileri sınama ise veri
  görülmeden önce EK-1 olarak yazıldı.
- İleri verinin zaman ekseni ana veriyle örtüşen barlarda doğrulandı: ofset 0'da medyan fark 0, ±60 dk'da büyüyor (E2/E3).
- Ders (E12/E23 tekrarı): 3.300 işlemli, iki dönemde de pozitif, 4/4 sembolde tutan bir hücre bile seçim düzeltmesinin
  sınırındaysa ileri dönemde çökebilir. Kuyruk payının yüksek olması (%76 en iyi 20 gün) uyarı işaretiydi.
