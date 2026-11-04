# NDX harfiyen mum eşleştirme (X = 10–50 mum, mum başına ±%0,015 gövde + fitil) — ileri yön sınaması ve ayar ailesi

Kapsam: yalnız yerel hesaplama (web araması yapılmadı; gerek görülmedi). Bütün betik ve çıktılar
`research/mum_derin_tarama_20261013/literal/` altında. Ön-kayıt: [PROTOCOL.md](research/mum_derin_tarama_20261013/literal/PROTOCOL.md)
(sonuçlara bakılmadan önce yazıldı). **Dokunulmaz dönem kuralına uyuldu:** her TF'de `ts + TF < 2025-12-01 00:00 UTC`
olmayan bar yüklemede atılıyor ve assert ile denetleniyor ([_lit.py](research/mum_derin_tarama_20261013/literal/_lit.py) `load`);
hiçbir sonuç penceresi bu tarihi geçmiyor. Başka dosya değiştirilmedi, commit yok. Toplam deney duvar süresi ≈ 35 dk
(numba 2 iş parçacığı, `nice`; en fazla 2 süreç).

**Önceki işlere göre yeni olan:** PM (NAS100 atlası) yalnız tekrar *sayısı* ve "sonraki 10 mum" yön bilgisi verdi; ME-02/ME-03
en çok 2 mumluk İkiz eşleşmeyi ve 7/33 boyutlu kNN'yi sınadı. Bu çalışma (i) kullanıcının tam payı **%0,015**'i, (ii) **X = 10, 15,
20, 25, 30, 40, 50** uzun birebir dizileri, (iii) %90/80/70 **kısmi** eşleşmenin (son 1–3 mum zorunlu) **ileri yönünü**, (iv) saat
cinsinden **+15 dk / +1 sa / +1 gün** ufuklarını, (v) uygunluk ve seans kısıtını aynı ailede, (vi) ailenin **tamamı** üzerinde
hafta-kaydırmalı seçim düzeltmesini ilk kez ölçüyor.

**Yöntem özeti:** mum özelliği `(H−O)/O, (L−O)/O, (C−O)/O` (%); eşleşme = penceredeki hizalı her mumda üç farkın da ≤ pay.
ATR varyantı: aynı farklar / pencere-sonu ATR14. Kütüphane nedensel (adayın sonuç barı kapanışı ≤ sorgu kapanışı), kayan 5 yıl
(1m/5m/15m'de mevcut tümü). Tahmin, **bağımsız** komşulardan (pencere + sonuç aralıkları çakışmayan, kronolojik açgözlü)
çoğunluk oyu. Tabanlar: o anki kütüphane yukarı oranıyla "hep çoğunluk", aynı UTC saatinin yukarı oranı, aynı uygun havuzdan aynı
sayıda rastgele komşu (plasebo, 20 tekrar). Sorgu ızgarası: 1m her 50 bar (5.049 sorgu, 2025-02→11), 5m her 10 (5.042), 15m her 8
(5.843, 2023-12→2025-11), 1h her 8 (6.140, 2017-06→2025-11). Çekirdek kaba-kuvvet sayımla birebir doğrulandı (bağımsızlık ve
yukarı/aşağı sayıları dahil). Kapasite koruması (inceltme) gerekmedi: φ = 1 her hücrede (tam sayım).

## 1. Fizibilite — harfiyen tanım kaç eşleşme veriyor?

### Takeaway
Harfiyen tanım (%0,015, X ≥ 10 birebir) **1h ve 15m'de hiç, 5m'de neredeyse hiç eşleşme bulmuyor**; yalnız 1m'de buluyor ve
oradaki eşleşmelerin **tamamı** mum boyunun payın altında kaldığı sessiz pencereler ("minik mum her şeyle eşleşir" tuzağı) —
uygunluk kuralı (medyan mum ≥ 3 × pay) açılınca her TF'de ve her X'te eşleşme **sıfır**.

### Cited Findings
- Tek mum eşleşme olasılığı p₁ (%0,015, son mum): 1h %0,35 · 15m %3,0 · 5m %6,9 · 1m %29,5 — [pilot_phi.json](research/mum_derin_tarama_20261013/literal/results/pilot_phi.json)
- 300 rastgele sorguda (inceltmesiz) %0,015 birebir, ufuk 1 sa, bağımsız eşleşme: **1h ve 15m: X = 10…50'nin hepsinde medyan/P75/P90 = 0, ≥1 eşleşmeli sorgu payı %0**; **5m:** yalnız X = 10'da sorguların %2,7'sinde ≥1, X ≥ 15'te %0 — [ozet_fiz_harfiyen_uyg0.csv](research/mum_derin_tarama_20261013/literal/results/ozet_fiz_harfiyen_uyg0.csv), [fizibilite.csv](research/mum_derin_tarama_20261013/literal/results/fizibilite.csv)
- **1m** (%0,015 birebir): X = 10 → medyan 0, P75 45, P90 473 bağımsız (ham P90 1.562); ≥1 eşleşmeli sorgu %41,7, ≥30 bağımsızlı %27,0. X = 20 → ≥1 %15,7, ≥30 %7,0; X = 50 → ≥1 %2,3, ≥30 %0,7 — [ozet_fiz_harfiyen_uyg0.csv](research/mum_derin_tarama_20261013/literal/results/ozet_fiz_harfiyen_uyg0.csv)
- Uygunluk kuralı açıkken (medyan mum boyu ≥ 3 × %0,015 = %0,045) **dört TF'nin hepsinde, her X'te, ≥1 eşleşmeli sorgu payı %0**; 1m sorgularının yalnız %25'i (Faz B) / %24'ü (Faz A, 73/300) bu eşiği zaten geçiyor — [ozet_fiz_harfiyen_uyg1.csv](research/mum_derin_tarama_20261013/literal/results/ozet_fiz_harfiyen_uyg1.csv), [harfiyen_1m_tani.csv](research/mum_derin_tarama_20261013/literal/results/harfiyen_1m_tani.csv)
- 1m'de eşleşme bulan sorguların 10 mumluk medyan mum boyu **%0,0083–0,0152** (X'e göre) — yani payın (%0,015) altında; eşleşme bulmayanlarınki %0,027–0,043. Eşleşmeli sorguların Asya seansı (23–07 UTC) payı X = 10'da %54, X = 50'de %89 (tüm sorgularda %36); uygun-olan payı %0 — [harfiyen_1m_tani.csv](research/mum_derin_tarama_20261013/literal/results/harfiyen_1m_tani.csv)
- Gevşek ayarlarda bile (uygunluk kapalı) "sorguların ≥ %50'sinde ≥30 bağımsız eşleşme" veren en uzun X: 1m %0,015 → birebir yok, %80 kısmi 10, %70 kısmi 15; 1m %0,03 → birebir 15, %90 kısmi 40; 1m %0,05 → birebir 50; 5m yalnız %0,05 kısmide (10–50); **15m ve 1h'te hiçbir pay/kuralda yok** — [ozet_fiz_xmax.csv](research/mum_derin_tarama_20261013/literal/results/ozet_fiz_xmax.csv)
- ATR-göreli payda (0,1/0,2/0,3 ATR) birebir X ≥ 10 eşleşme her TF'de medyan 0; %70 kısmi 0,3 ATR'de bile 1m X = 10 medyan 3, diğer TF'ler 0 — [fizibilite.csv](research/mum_derin_tarama_20261013/literal/results/fizibilite.csv)

### Inferences
- Sonuç ME-00/E25'in formülüyle (X_max ≈ ln(N/30)/ln(1/p₁)) tutarlı: 1h'te p₁ = 0,0035 ile X = 10'da beklenen eşleşme ~N·p₁¹⁰ ≈ 0. 1m'deki "uzun eşleşmeler" mum boyu dağılımından kendiliğinden doğuyor: pay mum boyunu aştığında 10–50 mum birbirine "eşit" görünüyor.
- Kullanıcının %0,015 payı yalnız tek bir TF'de (1m) ve yalnız anlamsız (sessiz) pencerelerde sonuç üretiyor; anlamlı mum boyuna sahip pencerelerde hiçbir TF'de 10+ mumluk birebir tekrar yok. PM'nin "en uzun birebir tekrar 8–9 mum" bulgusunu nedensel kütüphanede ve dört TF'de doğruluyor.

### Gaps
- 1m/5m kütüphanesi en çok ~10 ay (2025-01→11, dokunulmaz dönem nedeniyle); 5 yıllık 1m olsaydı 5m'de X = 10 birkaç eşleşme daha çıkabilirdi ama uygunluk kuralı altında sonucu değiştirmesi beklenmez (p₁¹⁰ ölçeği). Ölçülmedi.

## 2. Eşleşmeler +15 dk / +1 sa / +1 gün yönünü tabanlardan iyi tahmin ediyor mu?

### Takeaway
Hayır. Harfiyen tanımın tahmin üretebildiği tek yer olan 1m'de yön isabeti **%47–53**, her X ve her ufukta hep-çoğunluk / aynı-saat
tabanının **0,2–6,5 puan altında**; tahmin yönündeki ortalama hareket 15 dk / 1 sa'te −0,6…+0,8 puan (spread 1,5'in altında).
1 günlük ufukta pozitif hareket (+0,6…+11 puan) yalnız NDX sürüklenmesi — "hep yukarı" tabanı aynı sorgularda daha isabetli.

### Cited Findings
- 1m, %0,015 birebir, uygunluk/seans kapalı, n_min = 1: **+15 dk** X = 10: 2.104 çağrı, isabet %49,71 ↔ hep-çoğunluk %51,19 / aynı-saat %52,59 (fark −2,88 puan), hareket −0,23 puan; X = 25: %48,60 (−3,78); X = 50: 224 çağrı %47,77 (−4,02) — [ozet_harfiyen_ileri.csv](research/mum_derin_tarama_20261013/literal/results/ozet_harfiyen_ileri.csv)
- Aynı tanım **+1 sa**: X = 10: 1.193 bağımsız olay, %51,49 ↔ %53,13 (−1,64), hareket −0,41; X = 40: %49,12 ↔ %55,59 (−6,47) — [ozet_harfiyen_ileri.csv](research/mum_derin_tarama_20261013/literal/results/ozet_harfiyen_ileri.csv)
- Aynı tanım **+1 gün**: X = 10: 1.909 çağrı ama yalnız **170 bağımsız olay** (< 200 kapasite eşiği), %52,91 ↔ %56,10 (−3,27), hareket +2,81; X = 30: 92 bağımsız, hareket +11,39 ama fark −3,08 — [ozet_harfiyen_ileri.csv](research/mum_derin_tarama_20261013/literal/results/ozet_harfiyen_ileri.csv)
- 5m'de harfiyen tanım X = 10'da 163 çağrı (%50,92 ↔ taban %48,47, +2,45 puan, hareket +0,19) ve X = 15'te 15 çağrı; ikisi de 200 bağımsız olay eşiğinin altında. 15m'de tüm dönemde tek çağrı, 1h'te sıfır — [ozet_harfiyen_ileri.csv](research/mum_derin_tarama_20261013/literal/results/ozet_harfiyen_ileri.csv)
- Ailenin aktif (≥200 bağımsız olay) yapılandırmalarında ufuk bazında ortalama isabet ↔ hep-çoğunluk tabanı: 1d 15m-TF %53,8 ↔ %56,4, 1h-TF %51,5 ↔ %54,5; 1 gün ufkunda tahmin yönündeki ortalama hareket 15m-TF'de +10,7 puan (yapılandırmaların %93'ünde > 1,5) ama isabet tabanın altında — [aile.csv](research/mum_derin_tarama_20261013/literal/results/aile.csv), [ozet.txt](research/mum_derin_tarama_20261013/literal/results/ozet.txt)
- Kıyas için (aileye dahil değil) yalnız son mum gövdesinin dönüş/devam kuralı: 22 kural-hücresinin 20'sinde tabanın altında, en iyi 1h/1h dönüş +0,37 ve 5m/15m dönüş +0,69 puan — [tani_son_mum.csv](research/mum_derin_tarama_20261013/literal/results/tani_son_mum.csv)

### Inferences
- ME-02'nin "eşleşmelerin yön isabeti rastgele komşu düzeyinde, hep-çoğunluğun altında" sonucu X = 10–50 uzun birebir dizilerde de aynen geçerli; uzun dizi eşleştirmesi kısa İkiz/kNN'ye bilgi eklemiyor.
- 1 günlük ufukta "tahmin yönünde > 1,5 puan" ölçütü sürüklenme yüzünden kolay geçiliyor; bu yüzden ölçüt tek başına anlamsız, taban farkıyla birlikte okunmalı (E13).

### Gaps
- 1m/5m'de 1 gün ufku için ≥200 bağımsız olay yapısal olarak imkânsız (~10 aylık dönem ≈ 200 işlem günü); bu hücreler aday olamazdı. Daha uzun 1m geçmişi olmadan ölçülemez.

## 3. Ayar ailesinin herhangi bir üyesi aday ölçütlerini geçiyor mu?

### Takeaway
**Hayır — aday YOK.** 166.320 yapılandırmanın 9.166'sı ≥200 bağımsız olaya ulaştı; ön-kayıtlı ölçütlerin seçim düzeltmesi
dışındaki hepsini 8 yapılandırma geçti, ama ailenin en iyisi (fazla +13,94 puan) hafta-kaydırmalı null'un en-iyi dağılımının %95'ini
(15,20) aşamıyor (p = 0,15) ve 8 ön-adayın 8'i de çakışmayan kaydırılmış sorgu ızgarasında tabanın altına düşüyor.

### Cited Findings
- Aile boyutu: 4 TF × 9 pay (6 % + 3 ATR) × 7 X × 10 kural (birebir + %90/80/70 × son 1/2/3 zorunlu) × uygunluk aç/kapa × seans aç/kapa × ufuk (1m/5m/15m'de 3, 1h'te 2) × n_min {1, 5, 30} × güçlü oy (≥%70) aç/kapa = **166.320**; ≥1 çağrılı 32.372; ≥200 bağımsız olaylı (aktif) **9.166**. Tam aile tek tek kayıtlı — [aile.csv](research/mum_derin_tarama_20261013/literal/results/aile.csv)
- Aktiflerde "isabet − max(hep-çoğunluk, aynı-saat)" ortalaması **−1,48 puan** (medyan −1,24); ölçüt merdiveni: fazla ≥ +2 → 394; + iki kronolojik yarı > 0 → 236; + tahmin yönünde hareket > 1,5 puan → 53; + plaseboyu geçer + gün-blok bootstrap P ≥ 0,975 → **8**; + seçim düzeltmesi → **0** — [ozet.txt](research/mum_derin_tarama_20261013/literal/results/ozet.txt), [aday_eleme.csv](research/mum_derin_tarama_20261013/literal/results/aday_eleme.csv)
- Seçim düzeltmesi (200 tekrar; sorgu sonuçları bütün haftalarla dairesel kaydırılır → saat/gün korunur; çağrılar ve tabanların çağrıları sabit; tüm aktif aile yeniden puanlanır): null en-iyi fazla medyan 11,49 / %95 **15,20** / %99 16,05; gerçek en iyi 13,94 → **p = 0,150**. z-ölçeğinde gerçek en iyi 4,40 ↔ null %95 4,64 → p = 0,150. TF bazında (yalnız o TF'nin ailesi): 1m p = 0,065 · 5m 0,875 · 15m 0,020 · 1h 0,505 — [null_max.csv](research/mum_derin_tarama_20261013/literal/results/null_max.csv), [ozet.txt](research/mum_derin_tarama_20261013/literal/results/ozet.txt)
- Bootstrap P ≥ 0,975: ön-elekten geçen 1.751 yapılandırmanın 34'ü — tüm 9.166 aktif yapılandırmada tesadüfen beklenen ~229'un çok altında — [aday_eleme.csv](research/mum_derin_tarama_20261013/literal/results/aday_eleme.csv)
- 8 ön-aday (seçim düzeltmesi öncesi): 15m %0,05 X = 15 birebir (1 sa, n_min 30) +5,24; 1m %0,01 X = 10 %90 son2/son3 (seans, güçlü oy, 1 sa) +8,24/+8,73; 1m %0,03 X = 25 %90 son1/2/3 (seans, güçlü oy, 15 dk) +13,94/+12,61/+11,78; 5m 0,3 ATR X = 10 %70 son3 (uygunluk, 15 dk) +7,17; 5m %0,02 X = 10 %80 son2 (seans, güçlü oy, 1 sa) +6,43. Biri hariç (15m birebir, ort. 88 komşu) ortalama komşu 1–5; 208–420 çağrı — [aday_eleme.csv](research/mum_derin_tarama_20261013/literal/results/aday_eleme.csv)
- Bu 8 ön-adayın büyük farkı çoğunlukla **tabanın o alt kümede çökmesinden** geliyor: ör. 1m %0,03 X = 25 kümesinde hep-çoğunluk isabeti %41,2 (alt kümenin yukarı oranı %41,2), model %56,6; 8'inin 7'sinde sorgu uygunluk payı %0 (minik mumlar) — [tani_adaylar.csv](research/mum_derin_tarama_20261013/literal/results/tani_adaylar.csv)
- **Sonradan (post-hoc) kontrol**, aynı dönem ama orijinal sorgularla çakışmayan yarım-adım kaydırılmış ızgara: 8 ön-adayın fazlası −10,75 … −0,96 puan; isabet %46,3–53,4; taban %54–60 — [ofset_kontrol.csv](research/mum_derin_tarama_20261013/literal/results/ofset_kontrol.csv)
- En güçlü yön kümesi (aday DEĞİL): 15m TF, %0,02, X = 10, %80 kısmi son 2 zorunlu, uygunluk/seans kapalı, n_min 5, +15 dk: isabet %65,35 (228 olay), taban %51,32, iki yarı +10,6/+15,6, ama tahmin yönünde hareket **0,98 puan < 1,5** ve 15m-ailesinin en iyisi seçildiği için tek-yapılandırma null'u (p < 0,01) geçerli değil; olayların %86'sı Asya seansı; kaydırılmış ızgarada **%55,12 (205 olay), fazla +3,9, hareket 0,50 puan** — [aile.csv](research/mum_derin_tarama_20261013/literal/results/aile.csv), [ofset_kontrol.csv](research/mum_derin_tarama_20261013/literal/results/ofset_kontrol.csv)
- Null kalibrasyonu (20 kaydırma, tüm aktifler): gerçek ↔ null ortalama fazla çoğu hücrede yakın (ör. 1m/15m −1,14 ↔ −1,49; 5m/1h −1,83 ↔ −2,28); istisna 15m/15m −0,10 ↔ −1,63 — kaynak modelin değil tabanın farkı (model isabeti gerçek %50,16 ↔ null %50,35; hep-çoğunluk %49,90 ↔ %52,25) — [null_kalibrasyon.csv](research/mum_derin_tarama_20261013/literal/results/null_kalibrasyon.csv)

### Inferences
- Sabit-çağrılı hafta-kaydırma null'u, eşleşmenin seçtiği alt kümede (sessiz/Asya) tabanın gerçekte zayıf kalmasını taklit etmiyor; bu yüzden "isabet − taban" ölçütü için bu null, özellikle 15m/15m'de, hafif **serbest** (gerçeği iyi gösterme yönünde). Buna rağmen hiçbir yapılandırma geçmedi — sonuç sağlam negatif.
- 8 ön-aday klasik seçim gürültüsü: küçük komşu sayısı (1–5), tabanın tesadüfen düştüğü 200–400 olaylık alt kümeler; kaydırılmış ızgarada işaret değiştiriyor (E12, E24).
- 15m/%0,02/X = 10 kümesi ailedeki tek "kaydırılmış ızgarada da pozitif kalan" küme (+0,2…+4,3 puan), ama etki ~%55'e iniyor, hareket spread'in üçte biri ve Asya-sessiz. Ön-kayıtlı ölçütlerle aday değil; tutulacaksa yalnız yön bilgisi olarak ve yeni bir ön-kayıtla.

### Donmuş tanım (aday yok → yalnız en güçlü yakın-ıska; dokunulmaz dönemde sınanması ÖNERİLMEZ, kayıt için)
- TF 15m (`research/ndx_pattern_motifs/data/bars_15m.parquet`), özellik %, pay 0,02 puan, X = 10, kural "%80 kısmi" (10 mumdan ≥8'i payda) + son 2 mum zorunlu, uygunluk KAPALI, seans KAPALI, kütüphane nedensel tüm geçmiş (sonuç barı kapanışı ≤ karar), bağımsız komşular (pencere başı ≥ önceki seçilenin sonuç sonu), n_min = 5 bağımsız komşu (y ≠ 0), karar: yukarı payı > 0,5 → AL, < 0,5 → SAT, = 0,5 → çağrı yok; ufuk +15 dk (sonraki 15m barının kapanışı − sorgu kapanışı); sorgu ızgarası her 8. bar.
- Betik/komut: `cd research/mum_derin_tarama_20261013/literal && nice -n 10 /opt/homebrew/bin/python3.13 run_lit.py pilot && … run_lit.py scan 15m && … evaluate.py family` → `results/aile.csv` satırı `tf=15m, rep=pct, tol=0.02, X=10, kural=%80_son2, uygunluk=False, seans=False, ufuk=15m, n_min=5, guclu_oy=False`. Dokunulmaz dönem testi için `_lit.HOLDOUT` kesimi değiştirilmeli ve kütüphane yalnız 2025-12-01 öncesi + sorgular sonrası olmalı — bu kod YAZILMADI.
- Neden aday değil: hareket 0,98 < 1,5 puan; ailenin seçim düzeltmesini geçmiyor (13,60 < 15,20); kaydırılmış ızgarada etki %65 → %55.

### Gaps
- Tam "her iki tarafın sonucunu da kaydıran" null (komşu sonuçları da kaydırılıp çağrılar yeniden üretilerek) hesaplanmadı; yerine çağrılar sabit, sorgu sonuçları kaydırıldı (PROTOCOL.md'de önceden belirtildi). Kalibrasyon kontrolü bu sapmanın sonucu değiştirmediğini gösteriyor (null zaten serbest yönde).
- Kart ölçütü 5 (sonraki M1 açılışı + gerçek spread) burada uygulanmadı; yön/hareket karar barı kapanışından ölçüldü ve 1,5 puan sabit spread eşiğiyle kıyaslandı. Aday çıkmadığı için ayrıca koşulmadı.

## 4. İsabet X, sıkı pay veya güçlü komşu uyumuyla artıyor mu? Görünen kenar sessiz minik mumdan ya da sürüklenmeden mi?

### Takeaway
Hiçbir ayar yönü isabeti artırmıyor: X büyüdükçe fazla hafif kötüleşiyor, pay sıkılaştıkça iyileşmiyor, ≥%70 komşu uyumu eşli
kıyasta ortalama −1,24 puan kötü. Görülen tek tük pozitifler sessiz-seans minik mumlarına (uygunluk payı %0) ve tabanın tesadüfen
çöktüğü alt kümelere, 1 günlük hareket ise sürüklenmeye dayanıyor.

### Cited Findings
- X'e göre aktif yapılandırmaların ortalama fazlası: X = 10 −1,37 · 15 −1,46 · 20 −1,57 · 25 −1,42 · 30 −1,52 · 40 −1,65 · 50 −1,52 puan; fazla ≥ 2 payı %6,7 → %1,9 (X = 10 → 50) — [ozet.txt](research/mum_derin_tarama_20261013/literal/results/ozet.txt)
- Paya göre: %0,005 −1,92 · %0,01 −1,77 · %0,015 −1,82 · %0,02 −1,68 · %0,03 −1,36 · %0,05 −1,19 · 0,2 ATR −2,70 · 0,3 ATR −2,25 (0,1 ATR'de aktif yapılandırma yok) — sıkılaştıkça iyileşme yok — [ozet.txt](research/mum_derin_tarama_20261013/literal/results/ozet.txt)
- Güçlü oy (≥%70 aynı yön) − düz oy, aynı yapılandırma çiftleri (ikisinde de ≥100 çağrı, n = 4.600 çift): fazla farkı ortalama −1,24 (medyan −0,97), isabet farkı −1,08 puan — [ozet.txt](research/mum_derin_tarama_20261013/literal/results/ozet.txt)
- n_min: 1 → −1,75, 5 → −1,34, 30 → −1,11 (daha çok komşu = tabana daha yakın, üstüne değil); seans kısıtı açık −1,83 ↔ kapalı −1,15; uygunluk açık yalnız 38 aktif yapılandırma (−1,12) — [ozet.txt](research/mum_derin_tarama_20261013/literal/results/ozet.txt)
- Harfiyen tanımda eşleşmeli 1m sorgularının mum boyu payın altında (%0,008–0,015) ve %54–89'u Asya seansında; uygunluk kuralı açılınca eşleşme kalmıyor — [harfiyen_1m_tani.csv](research/mum_derin_tarama_20261013/literal/results/harfiyen_1m_tani.csv)
- 8 ön-adayın 7'sinde sorguların uygunluk payı %0; 1m ön-adaylarında isabet Asya'da (%63–65) diğer seanslardan yüksek, 15m/5m ön-adaylarında tersine; çağrıların yukarı payı 0,45–0,77; hep-çoğunluk isabeti alt kümede %41–52 — yani "kenar" büyük ölçüde tabanın o sorgularda yanılması — [tani_adaylar.csv](research/mum_derin_tarama_20261013/literal/results/tani_adaylar.csv)
- Çağrılar son mumun dönüşüyle uyumlu değil (15m/15m aktiflerde uyum 0,50; fazla ile korelasyon 0,08) → 15m kümesi 1-gecikme dönüş etkisi değil — [tanilar.py çıktısı / tani_son_mum.csv](research/mum_derin_tarama_20261013/literal/results/tani_son_mum.csv)

### Inferences
- "Daha uzun ve daha birebir = daha öngörücü" sezgisi verilerde tersine: uzun/sıkı eşleşme yalnız sessiz pencerelerde var ve az komşu verdiği için gürültüyü artırıyor. PM (gerçek/plasebo tekrar oranı medyan 1,0) ve ME-02 (güçlü oy tabandan farksız) ile tutarlı; kapı defterine **X** sınıfı olarak girmeli.
- Kayıt defteri için önerilen satır (koordinatör ekler; bu ajan başka dosyaya dokunmadı): `ME-04 | 2026-10-13 | Harfiyen mum eşleştirme: X 10–50, ±%0,015 (+%0,005–0,05, 0,1–0,3 ATR), birebir + %90/80/70 kısmi (son 1–3 zorunlu), uygunluk/seans, +15dk/+1sa/+1g, NDX 1m/5m/15m/1h, 2025-12-01 öncesi | Harfiyen tanım 15m/1h'te 0, 5m'de ~0, 1m'de yalnız payın altındaki sessiz pencerelerde eşleşme (uygunlukla 0); 1m isabet tabanın 0,2–6,5 puan altında. 166.320 yapılandırma, 9.166 aktif, 8 ön-aday, hafta-kaydırmalı aile null'u en iyi 13,94 < %95 15,20 (p=0,15), ön-adaylar kaydırılmış ızgarada negatif | X` — yeni kanıt hatası adayı (§1): "isabet − taban" ölçütünde sabit-çağrılı zaman-kaydırma null'u, eşleşmenin seçtiği alt kümede tabanın gerçek zayıflığını taklit etmez (serbest kalır); alt-küme tabanını da raporla.

### Gaps
- Evrim Paneli oturum notu (1. KURAL) ve deftere satır ekleme bu görevde "başka dosyaya dokunma" kısıtı nedeniyle yapılmadı; koordinatöre bırakıldı.
- Dokunulmaz dönem (2025-12-01 →) bilinçli olarak hiç yüklenmedi; doğrulama yapılmadı.
