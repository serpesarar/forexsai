# Korku gecesi + XP: geçmiş haftanın desteklerine limit girişi — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı fikri
"Giriş noktalarını geçmiş haftanın, fiyatın altındaki destek noktalarına konuşlandır; korku gecesinden sonra o desteklerden tepki alıyor gibi."

## Defter kontrolü (3. KURAL)
- **XL-01 (§2.96):** aynı stratejide SABİT mesafeli limit (10–200 bp) X. Dolanlar iyileşti, ama kaçanların %96'sı kazanandı ve sinyal başı kâr düştü.
- **TL/KC (§2.6x):** çizgi ve seviyelerde gerçek = hayalet. **E105:** hayalet seviye kontrolü zorunlu. **E109:** seviye karar anında tek ve belli olmalı.
- **Yeniden açma gerekçesi:** mesafe sabit değil, yapısal (geçmiş günlerin dipleri ve salınım dipleri). Belirleyici soru, bu seviyelerin aynı uzaklıktaki hayalet seviyelerden daha çok tepki üretip üretmediği.

## Sinyal ve çıkış (değişmez)
K1: 16:00 NY fiyatı ≤ TWAP(09:30–16:00) −%0,5 ve 15:00→16:00 aşağı. XP çıkışı: ilk yükselen 16:00 kapanışı, en geç 5 işlem günü.
Çıkış zamanı ve fiyatı sinyale bağlıdır, piyasa sürümüyle aynıdır (XL-01 ile aynı). Finansman takvim günü × FIN.

## Destek seviyeleri (yalnız 16:00 öncesi bilgi; E109: her sinyalde aile başına TEK seviye)
Aday, 16:00 alış fiyatının (ask0) en az **15 bp** ve en çok **300 bp** altında olmalı; adaylar içinde ask0'a **en yakın** olan seçilir.
- **D5:** önceki 5 işlem gününün (giriş günü hariç) her birinin NY tarih dibi (tüm saatler).
- **D20:** aynı, önceki 20 işlem günü.
- **P5:** 1 saatlik mumlarda fraktal salınım dibi (iki yanda 3'er mum daha yüksek dip). Onay mumu 16:00'dan önce kapanmış olmalı. Pencere: önceki 5 işlem günü + giriş günü.
- **P20:** aynı, 20 işlem günü.
- **W8:** önceki 8 takvim haftasının (Pzt–Cum) hafta dipleri.
- **D5_2:** D5'te ask0'ın altındaki **ikinci** seviye ("altındaki destek").

## Emir
- Alım limiti L = seviye. Dolum: ask dibi ≤ L olan ilk mumda min(L, ask açılışı).
- Geçerlilik: **W2** = XP çıkışına kadar (ana), **W1** = ertesi 16:00'ya kadar.
- Seviye yoksa (aralıkta aday yok) iki kural var: **A** = o sinyalde işlem yok; **B** = piyasa girişi (ana).
- **YARIM:** ½ piyasa + ½ limit.

## Hayalet seviye (E105) ve tepki testi
- **Hayalet:** seviyesi olan sinyaller arasında, aynı dönem içinde, seviye uzaklıkları (bp) rastgele karıştırılır. Uzaklık dağılımı aynı kalır, yapıyla bağ kopar. 500 permütasyon.
- **Strateji farkı:** sinyal başı ort. bp (gerçek − hayalet). P = permütasyonların kaçında gerçek > hayalet.
- **Tepki:** seviyeye ilk dokunuştan sonra fiyat seviyenin **+50 bp üstüne** mi önce çıkıyor, yoksa **−50 bp altına** mı önce iniyor? Ufuk XP çıkışına kadar; çözülmeyenler dışarıda. Gerçek dönme oranı ile hayalet karşılaştırılır.

## Dönemler ve beslemeler
- KEŞİF ≤ 2021-10-31, TEST 2021-11 → 2026-11.
- Ana besleme Duka NDX 1m. Bağımsız: MT5 NAS100 M30. Kör: MT5 US500, US30, US2000 (M30).
- MT5'te 1 saatlik mumlar M30'dan, dipler M30'dan kurulur.

## Geçme ölçütleri (sonuçtan önce)
1. **Tepki B için:** Duka KEŞİF ve TEST'in ikisinde gerçek dönme oranı − hayalet ≥ +5 puan ve P ≥ 0,90. Ayrıca MT5 4 beslemenin en az 3'ünde aynı işaret.
2. **Strateji B için:** (a) TEST'te sinyal başı ort. ≥ piyasa sürümü, Duka ve MT5 4 beslemenin en az 3'ünde; (b) en kötü %10 veya maksDD iyileşir; (c) gerçek > hayalet, P ≥ 0,90 (seviyenin kendisi katkı yapmalı).
3. Yalnız (b) ve kârda ≤ %5 kayıp: **C** (risk takası). Hiçbiri: **X**.
4. Aile × pencere × A/B/YARIM hücre sayısı raporlanır. En iyi hücre seçilmez; aile başına ana hücre **W2 + B**.
