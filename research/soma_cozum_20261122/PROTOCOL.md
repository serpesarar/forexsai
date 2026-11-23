# SC — Soma PureGold (MQL5 2268766) altın stratejisini çözüp geliştirme — ÖN KAYIT

## Kullanıcı isteği (2026-11-22)
"Bir hesaptan başla, stratejisini çözümle, kâr getirene kadar defalarca araştır. Kusursuz bir altyapı kur ki hiçbir hata çıkmasın."

## Neden Soma (seçim, sonuçlar görülmeden önce hesap düzeyinde)
- Diskteki 6 hesap içinde en uzun ve en kârlı yönlü hesap: XAU 2.132 pozisyon / 450 sinyal, 2024-11 → 2026-11, +42.150 $ (hesabın tüm kârı ≈ altın).
- Scalper değil (BreakZone/AI Wall Street saniye altı icrada → KH-10 X). Kopya kârın %81'ini taşıyor (KH-09) → 1m'de ölçülebilir.
- CWDT (2347514) altın girişlerinin %82'si Soma ile ortak (KH-06) → **aynı sinyal kaynağının ikinci örneği** (tekrar ölçümü, bağımsız kanıt değil).
- Önceki turların kaçırdığı yapı (bu oturumda history'den görüldü, betimleyici): sinyal başına medyan 3 bacak (en çok 34); sonraki bacaklar **lehte**
  fiyattan eklenir (medyan +2,3 $ — piramit, ızgara değil); bacaklar kademeli TP'lerle kapanır, son bacak iz süren stopla; ters giden bacak
  medyan 4 dk'da küçük zararla bot tarafından kapatılır. KH-12 klonu bunun yerine tek SL/TP kullanmıştı.

## Defter kontrolü (3. KURAL)
- KH-01…14 (§2.111): kopya zamanlama kenarı X; giriş tarzı (60 dk aralık ucu ∧ günlük trend) çözüldü ama AKK klonu her dönemde eksi (KH-12);
  seçimi öğrenen AKK-S bağımsız dönemde eksi (KH-14). **Tekrar edilmeyecek:** aynı AKK sinyali + tek SL/TP; aynı HistGB seçim modeli.
- MK-04/07 (XAU kırılım + trend): SHADOW / taban altı. be-lock (BE/kilit çıkışları X, 487 işlem).
- **Yeni olan:** (1) P&L ayrıştırma merdiveni (giriş zamanı, yön, çıkış yönetimi, piramit ayrı ayrı plasebolu); (2) çok bacaklı yönetimin
  (piramit + kademeli TP + iz) yeniden kurulması; (3) hiç kullanılmamış **2010–2017 kilitli KASA**; (4) yıl × saat spread modeli (bp).

## SC-00 — altyapı ve oyun kuralları (donduruldu)
**Kod:** `src/sc_veri.py` (tek veri kaynağı), `src/sc_kernel.c` + `src/sc_sim.py` (pozisyon motoru), `src/sc_degerlendir.py` (özet, defter, kasa kilidi),
`src/sc_duka.py` (indirici), `tests/` (pytest). Ham sağlayıcı verisi `research/kopya_hesap_20261122/data/` (gitignore), barlar `data/` (gitignore).

**Veri:** Dukascopy XAUUSD 1m BID. 2018-01 → 2026-11-13 mevcut; 2010–2017 indiriliyor. ASK her yılın her Çarşambası → (yıl, UTC saati) medyan spread bp;
eksik yılda en yakın yılın profili. Komisyon 0,08 $/ons gidiş-dönüş (Soma'nın kendi komisyonu).

**İcra (E7):** karar yalnız kapanmış barlarla; dolum karar anından SONRA açılan ilk 1m barın açılışı. Alış ask, satış bid; çıkışlar karşı taraf.
Aynı barda stop ve TP → stop. Açılış boşluğu stopu geçtiyse açılışta dolum. İz/başabaş güncellemesi bir sonraki bardan geçerli.
Zaman çıkışı en az bir bar sonra.

**Saat ekseni (E2/E150):** sağlayıcı zamanı → UTC, aday modeller ny7 / eet / sabit −5…+5 içinden giriş+çıkış barda-olma oranıyla seçilir;
fiyat tabanı ay ay (denetim ölçüsü). Ölçüm (2026-11-22): Soma ny7 %96,9, CWDT ny7 %89,6.

**Dönemler:**
| Dönem | Aralık | Kullanım |
|---|---|---|
| HESAP | 2024-11-01 → 2026-11-14 | çözümleme; burada seçilen kural burada sınanırsa bağımsız sayılmaz |
| GELISTIRME | 2018-01-01 → 2022-01-01 | sınırsız iterasyon, hepsi deftere |
| DOGRULAMA | 2022-01-01 → 2024-11-01 | aday başına bir koşu; Bonferroni N = o güne kadarki aday sayısı |
| KASA | 2010-01-01 → 2018-01-01 | kilitli; yalnız aşağıda `KASA ADAYI:` satırıyla yazılmış kimlik, kimlik başına bir kez (kodda zorlanır) |

**Geçme ölçütü (bir aday "kârlı strateji" sayılır ancak):** DOGRULAMA'da ort. bp > 0 ∧ gün bloklu P ≥ 1 − 0,05/N ∧ iki yarı > 0 ∧ spread ×1,5'te > 0 ∧
tek pozisyon kısıtıyla > 0 ∧ GELISTIRME'de > 0; ardından KASA'da ort. > 0 ∧ P ≥ 0,95 ∧ 2010–13 ve 2014–17 yarılarının ikisi > 0.
Hepsi geçerse kutuda `go_live_gate` (2. KURAL); canlıya alınmaz, karar kullanıcıda.

**Deneme sayımı:** her koşu `results/deneme_defteri.jsonl`'a (bar sürümü + git hash + parametre). Raporda toplam deneme sayısı yazılır.

## SC-01 — P&L ayrıştırma merdiveni (betimleyici + ön kayıtlı yorum)
Birim: **sinyal** (≤ 5 dk arayla aynı yönde açılan bacaklar; E9). Sinyal bp = bacakların lot ağırlıklı ort. bp'si. Soma ana, CWDT tekrar.
Dönem HESAP. Plasebolar 200 tekrar, tohum 20261122.
- **L0 kendi:** sağlayıcının broker fiyatlarıyla bp'si (komisyon dahil değil).
- **L1 kopya:** her bacak, girişinden sonraki ilk 1m açılışında (+spread) girer, çıkışından sonraki ilk 1m açılışında çıkar.
- **L2 çıkış plasebosu:** L1 girişleri; bacak tutuş süreleri tüm bacaklar arasında karıştırılır. L1 − L2 > 0 → çıkış zamanlamasında bilgi var.
- **L3 giriş kaydırma:** L1 sinyalinin tamamı Δ ∈ {−60, −15, −5, +5, +15, +60, +240 dk, +1 gün, +7 gün} kaydırılır (tutuş ve yön aynı).
  Kenarın Δ ile sönüm eğrisi; +1 gün ≈ L1 ise kâr "o günün/haftanın yönü"nden gelir, dakika seçiminden değil.
- **L4 yön:** L1 zamanları ve tutuşları; yön = hep AL / EMA240 / EMA1440 işareti (kapanmış barla) / rastgele.
- **L5 becerisiz trend izleyici:** dönemin rastgele işlem dakikaları (sinyal sayısının 20 katı), yön EMA1440 işareti, tutuş sağlayıcı tutuş
  dağılımından çekilir; HESAP ve GELISTIRME'de. HESAP'ta L1 ≈ L5 ve GELISTIRME'de L5 ≤ 0 → kâr dönemin altın boğası primidir.
- **Yorum kuralları (sonuçlardan önce):** fark P ≥ 0,95 (gün bloklu, eşleşmiş) "taşıyor"; < 0,95 "ayırt edilemiyor".
  Bir sonraki tur (SC-02) yalnız "taşıyor" çıkan bileşen(ler) üzerine kurulur. Hiçbiri taşımıyorsa sonraki tur yönetimin (piramit + kademeli TP + iz)
  kendisini sabit bir sinyal ailesine uygular (çıkış yönetimi bağımsız bir kenar olabilir mi) ve bunu açıkça yazar.

## Sonuçlar
(yukarısı değiştirilmez)

### SC-01 sonucu (2026-11-22, değiştirilmez) — `results/sc01_tablo.md`
Soma 448 sinyal: L0 +7,97 / **L1 kopya +6,16 bp (P 0,99)**, stres +5,31; sadakat kor 0,98; yön = EMA240/1440 işareti %100.
- L2 çıkış plasebosu +2,69 → fark +3,47, P 0,945 (**ayırt edilemiyor**, sınırda; CWDT +6,35 P 0,946 aynı).
- L3: −5/−15/−60 dk +21,6/+23,6/+24,2 (giriş öncesi hareket; kullanılamaz — sinyal o hareketin sonucudur); +5/+15/+60 dk +6,0/+5,4/+5,3 (fark P 0,59–0,76);
  +240 dk +2,2; +1 gün −0,01 (fark P 0,92); +7 gün −1,39 (**fark P 0,973, taşıyor**).
- L4: hep AL +0,73 (fark P 0,955 **taşıyor**), rastgele yön −2,23 (P 1,0 **taşıyor**), EMA yönü = L1.
- L5 becerisiz trend izleyici (rastgele dakika, EMA1440, Soma'nın bacak yapısı): HESAP +0,08 (P 0,52), GELISTIRME −1,75 (P 0,0006).
- CWDT tekrar: L1 +3,61 (P 0,76), aynı desen (L3 +5…+60 dk ≈ L1, +240 dk +1,8; L5 HESAP −1,1).
**Okuma:** kâr, dakika değil **saat ölçeğinde an seçiminden** (sert itkiden sonraki 1–4 saat) ve trend yönünden geliyor; rastgele anda trend izlemek kârsız.
Çıkış yönetimi sınırda. SC-02 an seçimini betimler.

### SC-02 betimleyici (sonuç gördükten sonra, hüküm değil)
Giriş anı (Soma 448 / CWDT 268 ilk bacak, rastgele EMA1440-yönlü dakika ile kıyas): r60 = yönlü 60 dk getiri / ATR14(1m) medyan 6,6 / 6,5 (rastgele 1,4);
r15 3,3; r5 2,0; ATR14 / 1 gün medyanı 1,7 (rastgele 1,0); 60 dk aralık konumu 0,96 (rastgele 0,60). Giriş sonrası yönlü sürüklenme (bp, sonraki dakika açılışından):
Soma +3,9 (60 dk) / +8,6 (240) / +12,8 (480); CWDT −1,5 / +6,0 / +10,3; rastgele trend dakikası +0,5 / +1,9 / +3,8.

## SC-03 — "itki devamı" kuralı sağlayıcısız genelleşiyor mu? (ÖN KAYIT, sonuçlardan ÖNCE)
**Kural IT(a)** (k kapanmış 1m barında; dolum k+1 açılışı + spread):
y = işaret(c_k − EMA1440_k); EMA240 aynı işaret; r60 = y·(c_k − c_{k−60}) / ATR14_k ≥ a; 60 dk aralık konumu (yöne göre) ≥ 0,90;
ATR14_k / ATR14'ün son 1440 bar medyanı ≥ 1,2; t_k − t_{k−60} ≤ 90 dk (seans boşluğu yok). Aynı yönde sinyalden sonra 60 dk soğuma.
**Çıkış:** yalnız zaman, T ∈ {60, 240, 480} dk. **Birincil hücre: a = 6, T = 240** (Soma medyanı ve hesabın sürüklenmesinin olgunlaştığı ufuk).
Izgara a ∈ {4, 6, 8} betimleyici.
**Taban:** aynı sayıda rastgele dakika, kuralın sinyallerinin UTC saat dağılımıyla, yön EMA1440, aynı T (taban × 5 tekrar ortalaması).
**Dönemler:** HESAP (kuralın sağlayıcıyı yeniden üretip üretmediği; ayrıca sağlayıcı sinyallerinin kaçı ±30 dk içinde yakalanıyor) ve GELISTIRME.
**Hüküm (birincil hücre, GELISTIRME):** IT ort. > 0 ∧ IT − taban > 0 ∧ gün bloklu fark P ≥ 0,95 ∧ iki yarı > 0 → **B: SC-04'te çıkış yönetimi
(piramit + kademeli TP + iz) bu kurala kurulur.** Aksi X: itki devamı bağımsız dönemde taşınmıyor, sağlayıcının an seçimi bu özelliklerle açıklanmıyor.
DOGRULAMA ve KASA bu turda açılmaz.

### SC-03 sonucu (2026-11-22, değiştirilmez): **X** — `results/sc03_tablo.md`
Birincil a 6 / T 240: GELISTIRME n 4.828, −1,94 bp, taban −1,94, fark −0,00 (P 0,50); HESAP +1,32 vs taban −0,32 (fark P 0,84).
Izgaranın 18 hücresinde GELISTIRME farkı hiçbir yerde P ≥ 0,95 değil. Kural Soma sinyallerinin %65'ini ±30 dk'da yakalıyor ama kural sinyallerinin
yalnız %9'u Soma'nın → Soma itkilerin ~1/10'unu seçiyor; seçilmeyenler HESAP'ta bile ≈ +0,6 bp.

### SC-04 (yöntem denetimi, sonuç gördükten sonra): KH-03/09 "aynı hafta" plasebosu SIZINTILI
Plasebo, sağlayıcının yönünü aynı haftanın rastgele bir gününe taşıyordu. Giriş ÖNCESİ günlere bu, haftanın sonradan gerçekleşen yönünü verir.
Ölçüm (Soma / CWDT, aynı tutuş): plasebo günü girişten önce +14,94 / +6,06 bp, girişten sonra **−5,91 / −5,16 bp**; gün kaydırma −1 g +15,4 / +12,7,
+1 g −0,01 / −10,5, +2 g −7,1 / −4,0. KH-09'un +7,1 plasebosu bu iki yarının karışımıydı. Dürüst (nedensel) plaseboya göre kopya ~+12 bp üstte →
**KH-03/09'un "zamanlama kenarı yok" hükmü bu sızıntıdan; Soma'nın an seçimi örneklem içinde gerçek.** Kopya iki yönde de artı (satış +5,2 n 170,
alış +6,7 n 278), 9/9 çeyrek artı.

### SC-05 (betimleyici, HESAP, örneklem içi): kopya kart ölçütleri — `results/sc05_kopya_kart.json`
Soma, gecikme 1 / 5 / 15 dk: +6,26 / +5,96 / +5,17 bp/sinyal, P 0,991 / 0,987 / 0,968, yarılar 4,1|8,4 / 5,2|6,7 / 2,3|8,0, spread ×1,5 +5,4 / +5,1 / +4,3,
tek pozisyon (n 236) +5,9 / +5,0 / +4,6, günlük Sharpe 2,6 / 2,4 / 2,0, maks. düşüş 442 / 388 / 471 bp. CWDT (aynı kaynak) +4,4 / +3,3 / +4,1, P 0,81 / 0,73 / 0,80.
**Uyarı:** Soma, 30 hesap içinden kârlı olduğu için seçildi (seçim yanlılığı); KH-02'de yönlü hesapların sıralaması ileriyi taşımadı (ρ −0,12).
Bu sayılar bağımsız kanıt değildir.

## SC-07 — Soma kopyası İLERİ GÖLGE (ÖN KAYIT, yeni işlemler görülmeden, 2026-11-22)
- **Kesim:** ilk bacağı 2026-11-21 00:00 UTC ve sonrası açılan sinyaller (eldeki export'un son işlemi 2026-11-20). Veri: kullanıcının MQL5'ten elle aldığı
  yeni positions + history export'u (otomatik toplama yok, PROTOCOL KH "Veri kaynağı ve hukuk"); barlar Dukascopy (`sc_duka.py guncel`).
- **Kopya kuralı:** her bacak, sağlayıcı girişinden 5 dk sonra açılan ilk 1m barın açılışında (+spread) girer; sağlayıcı çıkışından 5 dk sonra açılan
  ilk barda çıkar. Komisyon 0,08 $/ons. Birim sinyal (lot ağırlıklı).
- **Kart (hepsi):** n ≥ 100 sinyal; ort > 0 ∧ gün bloklu P ≥ 0,90; kronolojik iki yarı ≥ 0; spread ×1,5'te > 0; tek pozisyon kısıtıyla > 0;
  (sağlayıcı kendi bp − kopya bp) < kopya bp / 2. Ara bakışlar raporlanır ama hüküm yalnız n ≥ 100'de.
- Geçerse: canlı kopya yolu (MQL5 aboneliği ya da kutu köprüsü) kullanıcı kararıdır; 2. KURAL kartı `go_live_cards/soma_kopya.json`.
- Betik: `src/sc07_ileri_golge.py`.

## SC-08 — Soma'nın giriş sistemini çözme: çok zaman dilimli gösterge / seviye / hacim taraması (ÖN KAYIT, 2026-11-22, sonuçlardan ÖNCE)
Kullanıcı: "indikatörleri ayır, trendleri, destek-direnç noktalarını, o anki hacmi, EMA'ları, farklı zaman dilimlerini incele; nasıl, neye göre açıldığını bul."
- **Pozitif:** Soma sinyallerinin ilk bacağı (giriş saniyesi, UTC; fiyat broker → Duka bid: − ay tabanı, alışta − spread). Tekrar seti: CWDT.
- **Karşı küme:** HESAP döneminin rastgele 200.000 dakikası; yön = EMA1440 işareti (Soma'nın yönü %100 bununla aynı — bilinen bileşen koşullanır).
- **Özellikler (nedensel):** tamamlanmış 1m barlar + anlık fiyat. Zaman dilimleri M1, M5, M15, M30, H1, H4, D1; her birinde tamamlanmış bar ve oluşan (anlık) bar:
  EMA 9/20/50/100/200 (konum, eğim, sıralanış), RSI14, MACD(12,26,9), Bollinger(20,2) %b, Stokastik %K, ADX/DI, ATR, Donchian 20/55 konumu,
  son mum gövdesi/rengi/ardışık renk, tick hacmi / 20 bar ortalaması; seviyeler: önceki gün H/L/C, gün açılışı, Asya seansı H/L, hafta H/L,
  klasik pivot P/R1/S1, yuvarlak sayılar; saat/dakika/gün. Yöne hizalı (y ile çarpılmış).
- **Yöntem:** (1) tek değişkenli: AUC, pozitiflerin %95'inin geçtiği eşikte karşı kümenin geçme oranı ("zorunlu koşul" adayı);
  (2) tetik: ikili koşulların son 1/3/5 dk'da yanlıştan doğruya dönme oranı; (3) seviye: giriş fiyatının aday seviyelere uzaklığı (bekleyen emir izi);
  (4) zorunlu koşulların açgözlü birleşimi + tetik → kural.
- **Kronolojik bölünme:** kural Soma sinyallerinin ilk %60'ından (≈ 2024-11 → 2025-12) türetilir; son %40 ve CWDT yalnız sınama.
- **Başarı ölçütü (çözüldü):** ileri %40'ta kural ±10 dk içinde Soma girişlerinin ≥ %50'sini yakalar ∧ kural ateşlemelerinin ≥ %50'si Soma girişidir.
  Kısmen: yakalama ≥ %50 ∧ kesinlik %20–50. Aksi: çözülemedi (bilgi gözlediğimiz bar verisinde yok → tick / haber / dış veri gerekir).
- Kârlılık bu turda SINANMAZ; çözülürse klon ayrı turda GELISTIRME → DOGRULAMA → KASA'ya gider.

### SC-08 ara sonuç (dakika BAŞI ölçümü, 2026-11-22) — `results/sc08_*.json|csv`
- Tek değişkenli (KEŞİF 268 Soma / 100.159 karşı): en ayırıcı koşullar fiyatın H1 son 55 mum tepesine yakınlığı (AUC 0,92; pozitiflerin %95'inin
  geçtiği eşiği karşı kümenin %17'si geçer), H1/H4 stokastik ≥ 90, gün içi aralığın tepesinde (medyan konum 0,98), M15/M30 RSI ~70.
  Dakika başında fiyat 55 dk tepesinin hemen altında (%95'i altında) → kırılım giriş dakikasının İÇİNDE. Giriş fiyatı tek bir seviyede kümelenmiyor
  (bekleyen emir izi yok; son 5 dk tepesinin medyan 0,7 $ ötesinde piyasa girişi). Diğer enstrümanlarla eş zamanlılık yok; 09:30/10:00 ET payı %7 (4×).
- Açgözlü 5 koşul (M30 55 mum kırılımına yakınlık, M1 Donchian20 tepesi, H4 20 mum kırılımına yakınlık, H4 ADX ≤ 43, M30 mumu yönde): İLERİ yakalama %47,
  kesinlik %12. HistGB (300 özellik): İLERİ AUC 0,971 (CWDT 0,968); en önemli H1_a_kir55, H4_a_kir20. KEŞİF'te seçilen eşik/soğuma (q 0,998, 0 dk):
  İLERİ yakalama %30 / kesinlik %39 (CWDT %30 / %53). Gün düzeyinde: Soma günlerinin %90'ında ateşliyor, ateşlenen günlerin %60'ı Soma günü.
  60 dk soğuma ilk teması ateşleyip Soma'nın sonraki girişini bastırıyordu (ateşleme medyan 6,7 dk erken).
- **Ek (sonuç gördükten sonra, gerekçeli):** ölçüm giriş dakikasının KAPANIŞINDA (k = giriş dakikası barı, p = kapanış). Bu 1 dk gecikmeli klon demektir
  (dolum sonraki dakika); SC-01'de +1…+15 dk gecikme kenarı koruyor. Aynı başarı ölçütü, aynı bölünme; KEŞİF'te seçilen eşik/soğuma İLERİ'de raporlanır.

### SC-08 sonucu (dakika KAPANIŞI ölçümü, 2026-11-22, değiştirilmez): **KISMEN ÇÖZÜLDÜ**
- HistGB 300 özellik: İLERİ AUC 0,971→ (kapanış ölçümü) Soma yakalama/kesinlik KEŞİF'te seçilen eşikle (q 0,998, soğuma 0) **%40 / %37**, CWDT %38 / %45.
  Sıkı eşik (q 0,999) %24 / %56; gevşek (q 0,995) %69 / %25. Ölçüt (≥ %50 / ≥ %50) karşılanmadı; yakalama ≥ %50 ∧ kesinlik %20–50 hücresi var → kısmen.
- **Giriş anatomisi** (Soma / CWDT / rastgele): H4 20 mum kanal sınırının ±0,25 ATR'si içinde %63 / %64 / %11; H1 55 mum sınırının ±0,25 ATR'si %55 / %48 / %6;
  günün uç %5'i %77 / %74 / %10; M1 mum gövdesi yönde ≥ %50 %65 / %65 / %26; D1 stokastik ≥ 95 %56 / %51 / %12; yön EMA1440 ∧ EMA240 %100.
- Okunabilir kural (KEŞİF p20/p90 eşikleri, 8 koşul + trend, 30 dk soğuma): İLERİ yakalama %40, kesinlik %16, günde 1,5 ateşleme (Soma ~0,6).
- Yönetim: ek bacakların %66'sı ilk bacakla ≤ 2 sn (paket giriş), kalanlar medyan +0,12 $ lehte; TP'ler kademeli (en uzak / en yakın 1,66×);
  TP ve stop mesafesi hiçbir birimde sabit değil (CV 0,8–1,1: $, %, M15/H1/H4/D1 ATR); kapanış seviyesi giriş anı yapısal seviyesine oturmuyor (%7 vs plasebo %3) →
  stop sonradan taşınıyor, ilk stop export'ta yok. Botun kapattıkları (264) medyan 3,7 dk, −0,29 H1 ATR; o anda fiyat H4 20 kanal sınırında (medyan −0,05 ATR) → kırılım başarısızlığı çıkışı.

## SC-10 — çözülen giriş sistemi (model ateşlemeleri) Soma'sız kâr üretiyor mu? (ÖN KAYIT, sonuçlardan ÖNCE)
- Giriş: SC-08 HistGB (KEŞİF'te eğitilmiş, aynı tohum), dakika kapanışı ölçümü, mutlak eşik = KEŞİF q 0,998 skoru, soğuma 0, yükselen kenar. Dolum sonraki 1m açılışı + spread.
- Çıkış: birincil yalnız zaman T = 240 dk; betimleyici T = 60 / 480.
- Dönemler: (a) HESAP İLERİ (2025-11-07 → 2026-11-13; model eğitimi görmedi ama Soma'nın kârlı dönemi), (b) **GELISTIRME 2018–2021 (bağımsız; hüküm)**.
- Taban: aynı sayıda, aynı UTC saat dağılımında rastgele dakika, yön EMA1440, aynı T (×5).
- **B (GELISTIRME, T 240):** ort > 0 ∧ fark > 0 ∧ gün bloklu fark P ≥ 0,95 ∧ iki yarı > 0 ∧ spread ×1,5 > 0. Aksi X. DOGRULAMA/KASA açılmaz.

### SC-10 sonucu (2026-11-22, değiştirilmez): **X** — `results/sc10_sonuc.json`
Model ateşlemeleri (eşik 0,998 KEŞİF, günde ~1,0–1,1):
| Dönem | T | n | ort bp | taban | fark (P) | yarılar | stres |
|---|---|---|---|---|---|---|---|
| HESAP İLERİ | 240 | 295 | +7,29 | −1,65 | +8,94 (0,85) | +17,2 / −2,6 | +6,45 |
| HESAP İLERİ | 480 | 295 | +20,03 | +1,24 | +18,79 (0,94) | +35,0 / +5,1 | +19,17 |
| GELISTIRME | 240 | 1.054 | **−2,69** | −0,84 | −1,85 (0,25) | +2,0 / −7,4 | −3,53 |
| GELISTIRME | 480 | 1.054 | −1,00 | −0,80 | −0,20 (0,47) | +5,0 / −7,0 | −1,86 |
GELISTIRME yıllık (T240): 2018 −1,3 / 2019 −4,1 / 2020 −2,4 / 2021 −3,0. Çözülen giriş tarzı Soma'nın döneminde (2024–26 altın boğası) taşıyor, 2018–21'de taşımıyor.

## SC-11 — son seçim tik düzeyinde mi? (ÖN KAYIT, 2026-11-22, tik verisi indirilmeden ve hiçbir tik özelliği görülmeden ÖNCE)
Soru: SC-08 modeli koşulların sağlandığı anları buluyor, Soma bunların ~1/6'sında giriyor. Bu son seçimi saniye düzeyindeki fiyat akışı açıklıyor mu?
Ön bilgi (yalnız export saati, tik yok): ilk bacak saniyesi dakikaya neredeyse düzgün dağılmış (sn ≤ 5 payı %15,6, düzgünde %10; M5 sınır dakikası
%25,8 vs %20) → bot ağırlıkla tik tetikli, küçük bir "yeni mum" bileşeni var.

**Veri.** Dukascopy XAUUSD saatlik tik (`{saat}h_ticks.bi5`; ms, ask, bid, ask hacmi, bid hacmi). Kapsanan saatler: her olay için [t − 3.600 sn, t + 600 sn].
Olaylar: (P) Soma ve CWDT ilk bacakları (HESAP); (N) SC-08 modelinin dakika kapanışı ateşlemeleri (eşik 0,968 = KEŞİF q 0,998, soğuma 0, yükselen kenar),
±30 dk içinde aynı yönde Soma **ve** CWDT girişi olmayanlar ("ıska": koşul var, Soma girmedi).
**Bütünlük testi (geçmezse analiz yok):** tikten kurulan 1m BID OHLC, Dukascopy 1m mumlarıyla dakikaların ≥ %99'unda 0,001 $ içinde eşit; ms monoton; ask ≥ bid.

**Aşama 0 — saniye düzeyi saat hizası.** Ay başına gecikme L ∈ [−120, +120] sn: her bacak için hata = giriş fiyatı − Duka (alışta ask, satışta bid)(t + L).
Skor = hatanın medyan mutlak sapması (taban serbest). Seçilen L'nin skoru L ± 60 sn'ninkinden ≥ %20 düşük değilse saniye hizası **tanımsız** sayılır ve
analizde yalnız ≥ 60 sn geriye bakan özellikler kullanılır.

**Özellikler (s saniyesinde, yalnız ≤ s tikleri; seviyeler son tamamlanmış 1m bardan; hepsi yön y ile işaretli).** Getiri son 5/15/30/60/120/300 sn
(ATR birimi = son 60 adet 1m barın ortalama aralığı); tik sayısı son 10/30/60/300 sn ÷ son 60 dk ortalaması; spread ÷ son 60 dk medyanı; son 60 sn aralığı;
yönde ardışık tik sayısı ve son 30 sn yükselen tik payı; fiyatın H4 20 mum / H1 55 mum / günün uç seviyesine uzaklığı (ATR) ve o seviyeyi kaç sn önce geçtiği;
günün yeni ucunun kaç sn önce yapıldığı; dakika içindeki saniye; tik hacmi son 60 sn ÷ son 60 dk.

**Karşılaştırma kümeleri.** P = Soma ilk bacak saniyesi (Aşama 0 L'siyle). N1 = her ıskanın [ateşleme − 10 dk, + 10 dk] aralığından 5 rastgele saniye.
N2 = Soma'nın kendi sinyalinden önceki [giriş − 10 dk, giriş − 60 sn] aralığından 5 rastgele saniye ("neden şimdi, 3 dk önce değil").
Bölünme SC-08 ile aynı (KEŞİF < 2025-11-07 16:34:58 ≤ İLERİ). Özellik seçimi ve kural yalnız KEŞİF'te.

**Tetik taraması (hüküm).** KEŞİF'te açgözlü ≤ 4 koşul (P'nin ≥ %80'ini kapsayan eşikler) → İLERİ'de her model penceresinin (ateşleme ± 10 dk) tüm saniyelerinde
ilk tetik saniyesi. Model + tik tetiği birlikte, ±10 dk ve aynı yönde:
- **Çözüldü:** İLERİ Soma yakalama ≥ %50 ∧ kesinlik ≥ %50 ∧ CWDT İLERİ ikisi de ≥ %40.
- **İlerleme:** aynı yakalamada kesinlik model-tek başına (SC-08 eşik ızgarası) değerinden ≥ 10 puan yüksek.
- Aksi: **son seçim tik akışında bulunamadı** (kamuya açık fiyatta değil).
Zamanlama betimleyici: eşleşenlerde medyan |t_tetik − t_Soma|.
Kâr sınaması bu turda yok: tetik "çözüldü" ya da "ilerleme" verirse ayrı ön kayıtla GELISTIRME 2018–21 pencereleri için tik indirilip SC-10 düzeninde sınanır.
- **Ek (aynı gün, tik verisi indirilmeden):** tik tetiği yalnız model pencereleri İÇİNDE süzer, yakalamayı artıramaz. q 0,998 penceresinin İLERİ yakalaması %40
  olduğundan "çözüldü" ölçütü o pencereyle yapısal olarak ulaşılamaz. **Hüküm pencereleri q 0,995 (KEŞİF eşiği, soğuma 0; İLERİ model-tek başına %69 / %25).**
  N ıskaları da bu eşikle tanımlanır. q 0,998 betimleyici raporlanır. "İlerleme" kıyası: model-tek başına eğrisi (q 0,995 → 0,9995: %69/25, %54/31, %40/37,
  %24/56, %17/63), tik tetiğinin yakalamasında doğrusal ara değerle.
- **Ek 2 (aynı gün, tik özelliği hiç hesaplanmadan):** (i) "ateşleme ± 10 dk" penceresi ateşlemeden ÖNCEKİ saniyeleri de tarar → modelin
  ileride ateşleyeceği bilgisini kullanır, klon için nedensel değil. **Hüküm penceresi [ateşleme, ateşleme + 10 dk]** (ateşleme sonrası tik tetiği bekle);
  ± 10 dk betimleyici. (ii) Açgözlü kuralın negatif kümesi N1 ∪ N2 (ikisi birlikte); aday özellik KEŞİF AUC ≥ 0,60; eşikler KEŞİF P'nin %2/5/10/15/20
  yüzdeliklerinden; toplam P kapsaması ≥ %80. (iii) Betimleyici ikinci yöntem: tik özellikleri + model skoru üzerinde HistGB (KEŞİF P vs N1 ∪ N2),
  tarama eşiği KEŞİF taramasında min(yakalama, kesinlik) en büyük olan. (iv) Her ateşleme en çok bir tetik verir; kesinlik tetikler üzerinden.

### SC-11 sonucu (2026-11-23, değiştirilmez): **son seçim tik akışında bulunamadı** — `results/sc11_sonuc.json`, `sc11_tekli.csv`, `sc11_saat.json`
- Bütünlük: 1.585 saat, 91.958 dakika, tik→1m eşitliği %99,995; ms monoton; ask ≥ bid. 50 test geçiyor.
- Aşama 0: saniye hizası her ayda tanımlı (keskinlik 0,33–0,93). Soma L = 0/−1 sn (2026-09 +7, 2026-10 +35 sn sapma), CWDT −3…+3 sn;
  erken aylarda giriş fiyatı Duka ask/bid'inden MAD 0,08–0,25 $ → sağlayıcının fiyat akışı Dukascopy'ye çok yakın.
- Ayrım (KEŞİF, P 293 vs N 4.035): son 5/15/30 sn yönde getiri AUC 0,86 (P medyan r30 0,72 ATR1 vs 0,05), günün ucuna uzaklık 0,85 (0,12 vs 1,25 ATR1),
  günün yeni ucundan bu yana saniye 0,76 (**P medyan 0 sn**). N1 ve N2'ye karşı aynı güç → özellikler "pencere içinde hangi saniye"yi açıklıyor.
- Açgözlü kural: r30 ≥ 0,322 ∧ r5 ≥ 0,017. Nedensel tarama İLERİ **%68,9 / %25,5** (model tek başına %68,9 / %25,4), CWDT %65,4 / %31,3 → kesinlik artışı 0.
  ± 10 dk betimleyici %61,1 / %20,7. HistGB (tik + skor) İLERİ AUC 0,921 ama tarama %58,3 / %27,2 (model eğrisi o yakalamada ≈ %29,3) → ilerleme yok.
- Betimleyici: Soma ilk bacaklarının %63'ü günün yeni ucunun ≤ 2 sn içinde (%60'ı ayrıca r30 ≥ 0,32); ıska pencerelerinde saniye başına aynı koşul %4.
  Ama ıska pencerelerinin %84'ü, Soma pencerelerinin %87'si bu koşulu en az bir kez (ortalama ~25 sn) içeriyor.
  **Okuma:** Soma'nın tetik anı = koşullar varken fiyat itkiyle günün yeni ucunu yaptığı saniye. Hangi pencerede gireceği bu akışta yok.

### SC-10b (yöntem düzeltmesi, 2026-11-23): yıl × saat spread modeliyle yeniden kurulan barlarda (bar sürümü 613a0a31be; eski küp `data/xau_1m_v1_2018spread2025.parquet`)
SC-10 aynen yeniden koşuldu: GELISTIRME T240 −3,24 bp (taban −0,94, fark P 0,19), 4/4 yıl eksi; HESAP İLERİ T240 +7,51. **Hüküm değişmedi: X.**
(Spread bp yıllar arasında 1,4–2,2 bp; 2018–21 eski profilden ~0,2 bp pahalı.)

## SC-12 — fırsat seçimini HESAP DURUMU açıklıyor mu? (ÖN KAYIT, 2026-11-23, durum özellikleri hesaplanmadan ÖNCE)
Olaylar: SC-11 aday ateşlemeleri (q 0,995, dakika kapanışı). Etiket: ±10 dk aynı yönde Soma ilk bacağı var (eşleşen) / yok (ıska).
Karar anı: ıskada ateşleme anı t; eşleşende Soma'nın giriş anı − 1 sn (eşleşen sinyalin kendisi durumdan çıkarılır).
Durum (yalnız Soma geçmişinden, karar anından önce açılmış/kapanmış pozisyonlar): açık pozisyon var mı (herhangi / aynı yön), açık bacak sayısı,
son kapanıştan / son sinyalden bu yana saniye, sunucu gününde o ana kadarki sinyal sayısı, günün gerçekleşmiş net $'ı, son tamamlanan sinyalin net işareti,
son 5 sinyalin net toplamı, haftanın gerçekleşmiş net $'ı.
Ayrım KEŞİF'te (AUC), kural açgözlü ≤ 3 koşul (eşleşenlerin ≥ %80'ini kapsar). İLERİ: model + durum filtresi. Ölçütler SC-11 ile aynı
(çözüldü %50/%50 ∧ CWDT ≥ %40; ilerleme = aynı yakalamada model eğrisinden ≥ 10 puan kesinlik). CWDT'ye kendi geçmişiyle uygulanır.

### SC-12 sonucu (2026-11-23, değiştirilmez): **X** — `results/sc12_sonuc.json`, `sc12_tekli.csv`
Durum özelliklerinin hiçbiri ayırmıyor (KEŞİF AUC ≤ 0,58: son sinyalden bu yana süre 0,58, gün içi sinyal sayısı 0,56, son sinyal kârı 0,53, açık pozisyon 0,51).
Açık pozisyon medyanı iki kümede de 1 → "zaten pozisyonda olduğu için girmedi" değil. Kural (son sinyal ≤ 79 sa) İLERİ %51,1 / %24,1 (model eğrisi o yakalamada ≈ %31) → ilerleme yok.
Fiyat (bar + tik) ve hesap durumu birlikte de Soma'nın fırsat seçimini açıklamıyor; tavan İLERİ ~%40 / %37.

## SC-13 — çözülen tarzdan türeyen kendi strateji ailesi: bağımsız dönemde kâr var mı? (ÖN KAYIT, 2026-11-23, hiçbir hücre koşulmadan ÖNCE)
Defter kontrolü: XAU 1h yeni 20-bar tepesi BUY (MK-04/06 R0B_G1) B+, XAU günlük Golden Donchian (XS-01) B, braketli (TP'li) gün içi kırılımlar X (MK-07),
SC-10 (model ateşlemesi + zaman çıkışı) X. Yeni olan: Soma'nın çözülen giriş anı (H4 kanal sınırı ∧ günün yeni ucu ∧ güçlü 1m mum ∧ trend) ve Soma tarzı
çıkışlar (kırılım bozulunca hızlı kes / kazananı taşı). Bu aile bu tanımlarla daha önce sınanmadı.
**Girişler** (dakika kapanışı karar, sonraki 1m açılışında dolum + spread, komisyon):
- E1: SC-08 modeli ateşlemesi (KEŞİF q 0,998 eşiği, soğuma 0), iki yön. E2: E1 yalnız ALIŞ.
- E3: modelsiz Soma tetiği — EMA1440 ve EMA240 aynı yönde ∧ bu 1m bar sunucu gününün yeni ucunu yapar ∧ kapanış H4 son 20 tamamlanmış mumun ucunun
  0,25 ATR_H4 yakınında ya da ötesinde ∧ 1m gövde yönde ≥ %50 aralık; sunucu günü × yön başına ilk olay. E4: E3 yalnız ALIŞ.
**Çıkışlar** (ATR_H1 = son tamamlanmış H1 ATR14, $): X1 zaman 240 dk; X2 zaman 480 dk; X3 stop 1,0 ATR_H1 + zaman 480 dk;
X4 stop 1,5 ATR_H1 + iz süren stop (kâr +1,0 ATR_H1'de etkin, mesafe 1,0 ATR_H1) + zaman 1.200 dk. TP yok (MK-07: braketler taban altı).
**Taban:** her olay için aynı dönemden aynı UTC saatinde rastgele dakika (×5), aynı çıkış geometrisi (kendi ATR'siyle); yön: iki yönlü ailede EMA1440, alış ailesinde ALIŞ.
**Dönemler:** GELISTIRME 2018-01→2022-01 keşif (16 hücre). DOGRULAMA 2022-01→2024-11 tek atış. KASA 2010–2017 yalnız DOGRULAMA'yı geçen tek hücre için.
HESAP 2024-11→2026-11 betimleyici (E1/E2 modelin eğitim dönemini içerir).
**GELISTIRME geçişi:** ort > 0 ∧ fark > 0 ∧ gün bloklu fark P ≥ 0,95 ∧ iki yarı > 0 ∧ spread ×1,5 > 0 ∧ 4 yılın ≥ 3'ü > 0.
Birden çok hücre geçerse yalnız GELISTIRME farkı en büyük olan DOGRULAMA'ya gider. Hiçbiri geçmezse aile **X**, DOGRULAMA açılmaz.
**DOGRULAMA geçişi (B):** ort > 0 ∧ fark > 0 ∧ fark P ≥ 0,95 (Bonferroni: tek aday) ∧ iki yarı > 0 ∧ stres > 0 ∧ tek pozisyon > 0.
**KASA (B+):** ort > 0 ∧ fark > 0 ∧ fark P ≥ 0,90 ∧ stres > 0. Canlıya alma yine 2. KURAL kartına bağlı (bu kural kartı değildir).

### SC-13 GELISTIRME sonucu (2026-11-23, değiştirilmez) — `results/sc13_GELISTIRME.json`
16 hücreden yalnız **E2X3** (model ateşlemesi, yalnız ALIŞ, stop 1,0 ATR_H1, 480 dk) geçti: n 629 (~0,6/gün), +6,28 bp vs taban −1,73 (fark +8,0, P 0,987),
yarılar +8,1 / +4,4, stres +5,1, tek pozisyon +4,2, yıllar 2018 +0,02 / 2019 +8,6 / 2020 +7,4 / 2021 +6,7. Yakın kaçan: E1X3 (iki yön) +2,8, fark P 0,953, 2. yarı −0,7.
Modelsiz tetik E3/E4'ün hiçbir çıkışı geçmedi (en iyisi E4X2 fark P 0,955 ama 2/4 yıl). Uyarı: 16 hücrede P ≥ 0,95 tesadüfen ~0,8 hücre beklenir → GELISTIRME tek başına kanıt değil.
**DOGRULAMA ADAYI: E2X3** (tek atış, ölçütler yukarıda donduruldu).

### SC-13 DOGRULAMA sonucu (2026-11-23, değiştirilmez): **X** (ön kayıtlı P ölçütü) → uygulamada **C** — `results/sc13_DOGRULAMA.json`
E2X3 2022-01→2024-11: n 500, **+4,72 bp vs taban +0,73 (fark +4,0, P 0,886 < 0,95)**, yarılar +4,4 / +5,0, stres +3,8, tek pozisyon +6,8, yıllar 2022 −0,8 / 2023 +9,0 / 2024 +4,7.
Ölçüt P ≥ 0,95 tutmadı → KASA **açılmadı** (protokol). Betimleyici: HESAP 2024-11→2026-11 +8,19 bp vs −0,47 (P 0,96; model eğitimini içerir).
Ortalama R: GELISTIRME +0,245 / DOGRULAMA +0,154 / HESAP +0,301; isabet %35–42; stopla kapanan %54–57 (medyan −21…−27 bp); maks. düşüş 715–1.528 bp.
Mekanizma okuması: aynı girişte 1 ATR_H1 stop (Soma'nın "kırılım bozulunca hızlı çık"ı) zaman çıkışının yerine geçince fark büyüyor (E2: X2 +1,6 → X3 +6,3; E1: −1,7 → +2,8).
Modelsiz tetik (E3/E4) hiçbir çıkışla çalışmıyor → değer kaba anatomide değil, 300 özellikli modelin seçtiği anlarda.

## SC-14 — farklı bakış açılarıyla E2X3'ten daha iyisi var mı? (ÖN KAYIT, 2026-11-23, hiçbir hücre koşulmadan ÖNCE)
Kullanıcı: "daha derin ve farklı bakış açılarıyla araştır, daha iyisini bul". Keşif YALNIZ GELISTIRME 2018–21. Başvuru noktası E2X3 (GELISTIRME +6,28 bp,
fark +8,0). **Kirlilik beyanı:** E2X3'ün DOGRULAMA toplamını ve yıllarını (2022 −0,8 / 2023 +9,0 / 2024 +4,7) gördüm; E2 türevleri için DOGRULAMA
yarı kirli. Temiz tek sınav KASA 2010–17.
**Açılar (hepsi E2 girişi = SC-08 modeli ALIŞ ateşlemesi, sonraki 1m açılışı; taban aynı UTC saatinde rastgele ALIŞ, aynı geometri, ×5):**
- **A — stop × süre platosu:** stop k ∈ {0,5, 0,75, 1,0, 1,5, 2,0} ATR_H1 × T ∈ {240, 480, 960} dk (15 hücre). Aday = geçidi geçen hücreler arasında
  kendisi + 4-komşusunun fark ortalaması en büyük olan (tepe değil plato seçimi).
- **B — yapısal stop (kırılım bozulması):** stop = H4 son 20 mum tepesi − m·ATR_H1 (fiyat kanala geri girince çık), m ∈ {0, 0,25, 0,5};
  mesafe [0,25, 3,0] ATR_H1'e kırpılır; T 480 (3 hücre).
- **C — rejim (E2X3 üstüne filtre, son tamamlanmış D1'den):** R1 D1 kapanış > D1 EMA200; R2 D1 ATR14 / kapanış > son 250 D1'in medyanı;
  R3 D1 kapanış ≥ son 252 D1 tepesinin %97'si (3 hücre).
- **D — başarısızlığı tersine çevir:** E2X3'te ilk 60 dk içinde STOP olan işlemde stopun ertesi 1m açılışında SATIŞ, stop 1 ATR_H1, T 240;
  taban rastgele SATIŞ aynı geometri (1 hücre).
- **E — piramit (Soma sepeti):** E2X3 + fiyat girişin +1,0 ATR_H1 üstüne dokunduktan sonraki 1m açılışında 2. birim (kendi stopu 1 ATR_H1, aynı bitiş);
  ölçüt birim başına bp ve sinyal başına toplam (1 hücre).
- **F — piyasadan öğrenilmiş seçim:** aday = modelin q 0,99 ALIŞ ateşlemeleri; hedef = X3 sonucu bp > 0; 300 özellikle HistGB, iki katlı kronolojik
  (2018–19 ↔ 2020–21) katman-dışı skor; her katta eğitim katının skor üst üçte biri eşiği. Katman-dışı seçilenler değerlendirilir (1 hücre).
**Geçit (her hücre, GELISTIRME):** SC-13 geçidi (ort > 0 ∧ fark > 0 ∧ fark P ≥ 0,95 ∧ iki yarı > 0 ∧ stres > 0 ∧ ≥ 3/4 yıl > 0)
**∧ tüm iş günlerine yayılmış günlük Sharpe > E2X3'ün GELISTIRME değeri** ("daha iyi" tanımı). Geçen yoksa E2X3 en iyi kalır.
Birden çoksa en yüksek Sharpe → **DOGRULAMA** tek atış, Bonferroni N = 2 (bu çalışmanın ikinci adayı) → fark P ≥ 0,975, iki yarı > 0, stres > 0, tek pozisyon > 0.
Geçerse **KASA 2010–17** tek atış (ort > 0 ∧ fark > 0 ∧ fark P ≥ 0,90 ∧ stres > 0), `KASA ADAYI` satırı o an yazılır.

### SC-14 GELISTIRME sonucu (2026-11-23, değiştirilmez): **geçen yok → E2X3 en iyi kalır** — `results/sc14_GELISTIRME.json`
Ref E2X3 Sharpe (tüm iş günleri) 0,896. A platosu: k 0,75–1,0 × T 480–960 dört hücrenin dördü fark +6,8…+8,9 (P 0,98–0,99), k 0,5 ve T 240 zayıf,
k 2,0 bozuluyor → E2X3 tepe değil plato üstünde. B yapısal stop +3,0…+4,8 (Sharpe ≤ 0,71). C rejim: R1 EMA200 +5,1 ama 2. yarı −4,6; R2/R3 X.
D tersine çevirme +3,2 (n 182, P 0,92) X. E piramit sinyal başı +9,3 (fark +12,8, P 0,994) ama Sharpe 0,85 < 0,896 ve 3/4 yıl. F öğrenilmiş seçim +5,7, 2/4 yıl X.

## SC-15 — E2X3 başka piyasalara DONDURULMUŞ taşınıyor mu? (ÖN KAYIT, 2026-11-23, koşulmadan ÖNCE)
Amaç: KASA'yı harcamadan bağımsız kanıt. Model, eşik (altın KEŞİF q 0,998 mutlak skoru), yalnız ALIŞ, stop 1 ATR_H1, 480 dk — hiçbir şey değişmez.
Piyasalar: Dukascopy 1m DAX, CAC, STOXX50 2018-01 → 2026-11 (model hiç görmedi). Spread: o piyasanın ASK Çarşambalarından yıl × saat bp modeli; komisyon 0.
Taban: aynı piyasada aynı UTC saatinde rastgele ALIŞ, aynı geometri (×5).
**Hüküm "taşınıyor" (B):** havuz (üç piyasa) fark > 0 ∧ gün bloklu fark P ≥ 0,95 ∧ havuz iki yarı > 0 ∧ havuz stres > 0 ∧ piyasaların ≥ 2/3'ünde fark > 0.
Aksi X. Ateşleme sıklığı farklı olabilir; raporlanır, eşik değiştirilmez.

### SC-15 sonucu (2026-11-23, değiştirilmez): **B (havuz, sınırda)** — `results/sc15_sonuc.json`
Havuz n 3.119 +2,30 bp vs taban −0,98 (fark +3,28, P 0,952), yarılar +2,7 / +1,9, stres +1,4. **DAX +7,78 vs −0,04 (P 0,997, 9/9 yıl > 0)**,
CAC −1,32 vs +0,21 (X), STOXX −1,94 vs −3,98 (fark +2,0, P 0,73; spread 4,3 bp). Taşımayı DAX taşıyor.

## SC-16 — DAX dondurulmuş E2X3 sağlamlık (ÖN KAYIT, 2026-11-23, koşulmadan ÖNCE; DAX SC-15'te 3 piyasadan sonradan seçildi → Bonferroni N 3: P ≥ 0,983 ✓ 0,997)
Hiçbiri kuralı değiştirmez; hepsi "kırılır mı?" sınaması:
(a) kart benzeri: n ≥ 150, ort > 0 ∧ bootstrap P(EV>0) ≥ 0,90, iki yarı ≥ 0, stres ×1,5 > 0, tek pozisyon > 0, icra = sonraki 1m açılışı + spread (zaten).
(b) plato: k ∈ {0,75, 1,0, 1,5} × T ∈ {240, 480, 960} — merkezdeki 2×2'nin (k 0,75–1,0 × T 480–960) ≥ 3'ünde fark > 0 ∧ P ≥ 0,90.
(c) ayna: aynı model SATIŞ ateşlemeleri (betimleyici; DAX'ta uzun sürüklenme beklenir).
(d) eşik: q 0,997 / 0,999 (yoğunluk) — ikisinde de fark > 0.
(e) gece taşıma: 480 dk penceresi seans kapanışını aşan işlemler ayrı raporlanır; yalnız aynı gün içinde kapananlar da fark > 0 olmalı.
(f) en iyi 10 gün çıkarılınca ort > 0.
**Sağlam (B+):** (a) ∧ (b) ∧ (d) ∧ (e) ∧ (f). Biri düşerse C. Canlı için yine 2. KURAL kartı (kutuda GER40 MT5 verisiyle) gerekir.

### SC-16 sonucu (2026-11-23, değiştirilmez): **B+** — `results/sc16_dax.json`
(a) kart: n 1.297, +7,78 bp, P(EV>0) 0,997, yarılar +10,0 / +5,6, stres +7,5, tek pozisyon +6,8, 9/9 yıl > 0, Sharpe 0,86 ✓.
(b) plato: 9 hücrenin 9'u fark +5,4…+11,9, P 0,993–0,999 ✓ (uzun tutuş daha iyi: T 960 +11,6). (c) ayna SATIŞ −1,74 (fark −1,0) → yalnız alış.
(d) q 0,997 +6,9 (n 2.279, P 0,998), q 0,999 +6,5 (n 477, P 0,935) ✓. (e) aynı gün kapanan 1.035 işlem +4,56 vs taban −0,08 ✓; geceye taşan 262 işlem +20,5.
(f) en iyi 10 gün hariç **+0,77** ✓ (ince: ortalamanın ~%90'ı en iyi 10 günde → kuyruk taşıyor, E101).
Uyarı: aynı modelle CAC X (SC-15) — yüksek korelasyonlu komşu piyasada tutmaması mekanizma anlatısını zayıflatır.

## SC-17 — DAX E2X3 bağımsız DÖNEM: Dukascopy DEUIDXEUR 2018 öncesi (ÖN KAYIT, 2026-11-23, veri indirilmeden ÖNCE)
Kural dondurulmuş (SC-16 ile birebir). Dönem: Dukascopy'de bulunan ilk aydan 2017-12-31'e (2011 yok; ilk ay indirmede belirlenir).
Taban ve spread SC-15 gibi (o dönemin ASK Çarşambaları). **B:** ort > 0 ∧ fark > 0 ∧ fark P ≥ 0,95 ∧ iki yarı > 0 ∧ stres > 0 ∧ yılların ≥ yarısı > 0.
Aksi X. Geçerse DAX adayı **gölgeye (GER40, emirsiz)** ve 2. KURAL kartına aday olur.

## SC-18 — kullanıcı ölçütü değişti (2026-11-23): "son 3–4 yılda her yıl artı yeterli, eski dönem eksiliği elemez"
Betimleyici yeniden okuma (yeni koşu yok, yalnız SC-13 16 hücresi 2022-01→2026-11 yıl yıl + modelsiz tetik DAX/CAC/STOXX). `results/sc13_son_yillar.json`
Ölçüt: 2023, 2024, 2025, 2026 her biri > 0 ∧ iki son dönemde (2022–24, 2024–26) rastgele alışa fark > 0.
- **Altın E4X3 (MODELSİZ: trend ∧ günün yeni ucu ∧ H4 20 kanal sınırı ∧ 1m gövde ≥ %50, yalnız ALIŞ, gün başına ilk, 1 ATR_H1 stop, 480 dk):**
  2023 +6,97 / 2024 +4,41 & +7,40 / 2025 +5,79 / 2026 +7,69; fark 2022–24 +5,26 (P 0,974), 2024–26 +8,81 (P 0,975). Model ve Soma'ya bağımsız → eğitim kirliliği yok.
- **Altın E2 ailesi (model ALIŞ):** E2X3 2023 +9,0 / 2024 +4,7 & +3,1 / 2025 +7,8 / 2026 +10,5; E2X1, E2X2 de dört yıl artı. 2025 model eğitimini kısmen içerir; 2026 temiz.
- **DAX E2X3 (model, dondurulmuş):** 2022 +12,4 / 2023 +1,3 / 2024 +2,8 / 2025 +6,4 / 2026 +9,4 (model DAX görmedi → temiz).
- Elenenler: E1X2 (2023 −0,8), E3X3 (2026 −2,5), E3X4, E4X2; modelsiz tetik DAX/CAC/STOXX'ta (DAX E4X3 2024 −0,5), CAC/STOXX E2X3, tüm SATIŞ aynaları.
Uyarı: 16 hücreye yeni ölçüt uygulandı (seçim); ama geçenler aynı ailede kümeleniyor (alış + kanal kırılımı, 8 sa). Canlı için 2. KURAL kartı (kutuda MT5) şart.

### SC-17 sonucu (2026-11-23, değiştirilmez): **X** — `results/sc17_dax.json`
DAX 2014-01-28 → 2017-12 (veri 2013-09'dan): n 297, **−4,61 bp vs taban +2,73 (fark −7,3, P 0,01)**, yıllar 2014 −3,8 / 2015 −4,5 / 2016 −12,1 / 2017 +2,0.
Kullanıcının SC-18 ölçütüyle eski dönem tek başına elemez; ama DAX kenarının 2018 sonrası rejime özgü olduğunu açıkça gösterir (ayrıca ateşleme sıklığı ~0,3/gün, 2018+ döneminin yarısı).

## SC-19 — canlıya alma kartı (2. KURAL) + NASDAQ ve diğer endekslere dondurulmuş taşıma (2026-11-23, kullanıcı: "canlıya al direk … nasdaq'ta özellikle")
Hücreler dondurulmuş: E4X3 (modelsiz AL) ve E2X3 (model AL), SL 1×ATR_H1, 480 dk. Kart penceresi **son 4 yıl 2022-11-14 → 2026-11-14** (SC-18 kullanıcı ölçütü).
6 ölçüt: n ≥ 150; ort R > 0 ∧ P(EV>0) ≥ 0,90; iki yarı ≥ 0; spread ×1,5 > 0; icra (iyimser − gerçek ≤ ort R / 2); tek pozisyon > 0. Ek: 2023–26 her yıl R > 0.
**LIVE = 6/6 ∧ son 4 yılın her yılı artı.** Piyasalar: XAU (kendi küpü), NDX (Dukascopy, hacim bi5'ten, kapsam %100), DAX/CAC/STOXX (fibo önbelleği), UK100/JPN225 (korku_kuresel; tek medyan spread).

### SC-19 sonucu (değiştirilmez) — `results/sc19_kart.json`, kartlar `backend/data/evolution/go_live_cards/soma_*.json`
| piyasa | hücre | kart | son 4 yıl R (2023/24/25/26) | ort R | rastgele alışa fark | verdikt |
|---|---|---|---|---|---|---|
| XAU | E4X3 | 6/6 | +0,32 / +0,16 / +0,24 / +0,22 | +0,199 (n 421) | +6,5 bp P 0,991 | **LIVE** |
| XAU | E2X3 | 6/6 | +0,37 / +0,12 / +0,33 / +0,26 | +0,269 (n 945) | +6,0 bp P 0,966 | **LIVE** (2025 eğitim kirli) |
| **NDX** | **E2X3** | 6/6 | +0,38 / +0,34 / +0,17 / +0,11 | +0,272 (n 589) | +7,8 bp P 0,977 | **LIVE** — 2018–26 dokuz yılın dokuzu artı |
| NDX | E4X3 | 5/6 (icra ✗) | +0,11 / +0,32 / +0,04 / −0,02 | +0,114 | +1,7 P 0,76 | SHADOW |
| DAX | E2X3 | 4/6 | −0,01 / +0,08 / +0,23 / +0,18 | — | +4,8 P 0,937 | SHADOW |
| JPN225 | E2X3 | 6/6 | +0,25 / +0,58 / −0,10 / +0,88 | — | +8,7 P 0,940 | SHADOW (2025 eksi) |
| CAC / STOXX / UK100 | ikisi | 1/6 | eksi yıllar | <0 | ≈0 | RED |
Okuma: modelin öğrendiği "trend içi kanal tavanında güçlü alış dakikası" ABD endeksine (NDX) ve Nikkei'ye taşınıyor, Avrupa'nın küçük endekslerine taşınmıyor.

### SC-19b/c — canlı yapım paritesi (`results/sc19_parite.json`, `sc19_e4_parite.json`)
E2: canlı yapım (son 99.000 gerçek 1m + öncesi H1'den sentetik dakika + `yeni deneme/soma_motor.py`) ile tam geçmişli araştırma Motor'u son 30 günde
skor korelasyonu 1,0000, medyan fark 0, ateşlemeler XAU 6/6, NDX 1/1 birebir. E4: canlı `evaluate` ile araştırma koşulu 494/494 aynı karar (94 pozitif).
Açık kalan: broker tick hacmi ↔ Dukascopy hacmi ve broker fiyatı farkı → kutuda `soma_kontrol.py` ile geriye dönük ateşleme listesi; ilk 60 canlı işlem karnesi.
