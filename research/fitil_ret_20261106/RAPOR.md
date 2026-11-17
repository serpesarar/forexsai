# NDX 1h / 4h büyük fitil → ters yön (ret) — rapor (2026-11-06)

Ön kayıt: `PROTOCOL.md` (sonuçlardan önce). Kod: `engine.py` (tüm mumlar × yön × gecikme × SL × TP sonuç matrisi),
`run.py` (hüküm), `diag.py` (tanılar, post-hoc). Çıktılar: `results/hukum.json`, `results/tani.json`, `logs/*.log`.

## Soru
Büyük üst fitilli 1h/4h mum kapandıktan 0–20 dk sonra SAT, büyük alt fitilli mumdan sonra AL; TP/SL ızgarasıyla
kârlı bir kapı var mı? Kullanıcının gerekçesi: büyük hareketlerin sonunda fitiller büyür, yön kırılır, düzeltme gelir.

## Veri ve icra
- NDX 1m Dukascopy bid/ask, KEŞİF 2024-01 → 2025-06, TEST 2025-07 → 2026-11 (mühürlü). Saat ekseni denetlendi: aylık en
  oynak dakika 34 ayın 29'unda 09:30 ET.
- Giriş HTF kapanışından D dk sonraki 1m açılışı (SAT bid, AL ask), çıkış 1m'de ask/bid ile, aynı barda SL+TP → SL.
- BAĞIMSIZ: NDX 1h arşivi 2016-06 → 2023-12 (giriş sonraki 1h açılışı, spread 1,5).
- Motor iki bağımsız yoldan (matris ↔ tek işlem simülatörü) 5.129 rastgele işlemde birebir aynı sonucu verdi.

## 1. Ön-kayıtlı 8 hipotez (s ≥ 0,5, w ≥ 0,5 ATR, SL = fitil ucu + 0,1 ATR, TP 1R, D = 5 dk)

| ID | TF / yön / bağlam | KEŞİF n · R | TEST n · R · P | TEST ayna (devam) | BAĞIMSIZ 2016-23 | hüküm |
|---|---|---|---|---|---|---|
| H1 | 1h üst → SAT | 429 · −0,106 | 341 · **−0,127** · 0,008 | +0,028 | 2.305 · −0,128 | X |
| H2 | 1h alt → AL | 706 · −0,043 | 584 · **−0,095** · 0,007 | +0,014 | 3.182 · −0,081 | X |
| H3 | 4h üst → SAT | 59 · +0,002 | 51 · +0,129 · 0,84 | −0,172 | (4h, tanı) 337 · −0,185 | X |
| H4 | 4h alt → AL | 123 · −0,001 | 105 · −0,023 · 0,38 | −0,071 | (4h, tanı) 602 · +0,074 | X |
| H5 | 1h üst → SAT, ≥2 ATR yükseliş sonrası | 52 · −0,150 | 39 · +0,006 · 0,51 | −0,068 | 316 · −0,168 | X |
| H6 | 1h alt → AL, ≥2 ATR düşüş sonrası | 91 · +0,017 | 77 · −0,165 · 0,07 | −0,015 | 416 · −0,063 | X |
| H7 | 4h üst → SAT, yükseliş sonrası | 10 · +0,276 | 7 · −0,731 | +0,714 | (4h, tanı) 27 · −0,084 | X |
| H8 | 4h alt → AL, düşüş sonrası | 23 · +0,124 | 16 · −0,173 · 0,21 | −0,178 | (4h, tanı) 60 · **+0,288** · 0,994 | X (iz, aşağıda) |

1h'te iki yön de üç dönemde (2016-23, 2024-25, 2025-26) negatif. Ters yön (devam) sıfır civarında, yani fitilin
ret yönü devamdan kötü. 4h üst fitil SAT'ın TEST'teki +0,13'ü 2016-23'te −0,19 çıktı.

## 2. Deneme-yanılma ızgarası (14.400 hücre) ve seçim düzeltmesi

**Tuzak (E100):** Fitil-ucu stoplu kuralın tabanı "tüm mumlarda aynı kural" diye kurulursa yanıltır. Rastgele mumun ucu
kapanışa yapışık olduğundan stop dar kalır, spread R'yi eritir (taban −0,34R). Büyük fitilli mumda ise stop kendiliğinden
geniş. Bu yüzden ilk koşuda 1h hücreleri tabana göre +0,26R "fark" ve p_sel = 0,00 gösterdi, oysa mutlak R hep negatifti
(en iyi 1h hücresi TEST −0,093R, isabet %60, TP 0,5R). Tanı koşusu ızgarayı yalnız ATR stoplarıyla tekrarladı:

| TF / yön | t_max | boş %95 | p_sel | en iyi hücre TEST farkı | ilk-20 TEST farkı (pozitif) | KEŞİF R > 0,10 olan hücrelerin TEST R'si (pozitif oranı) |
|---|---|---|---|---|---|---|
| 1h üst → SAT | 2,79 | 3,79 | 0,44 | −0,040 | −0,027 (4/20) | 73 hücre → −0,091 (%22) |
| 1h alt → AL | 3,68 | 3,89 | 0,11 | −0,022 | −0,009 (6/20) | 495 → −0,051 (%29) |
| 4h üst → SAT | 3,42 | 3,45 | 0,055 | +0,053 (n 37) | +0,058 (15/20) | 236 → −0,036 (%38) |
| 4h alt → AL | 1,97 | 3,54 | 0,70 | −0,136 | −0,092 (2/20) | 442 → −0,103 (%13) |

Izgaranın en iyileri tesadüften ayırt edilemiyor. KEŞİF'te kârlı görünen yüzlerce TP/SL/gecikme kombinasyonu TEST'te
ortalama negatife dönüyor. 4h üst SAT'ın sınırdaki izini (p 0,055) 2016-23 bağımsız dönemi çürütüyor (−0,12…−0,19R).

## 3. Tanılar
- **Gecikme (5/10/15/20 dk):** etkisi yok. 1h SAT her D'de −0,01…−0,10. Hiçbir D iki dönemde birden artı değil.
- **Teyit** (girişte fiyat sinyal kapanışından ret yönüne gitmiş mi): 1h'te teyitli işlemler teyitsizlerden iyi değil
  (AL: teyitli −0,05/−0,08, teyitsiz +0,00/−0,02).
- **Yıl / seans:** H1 2024 −0,14, 2025 −0,07, 2026 −0,14. Hiçbir seans iki dönemde artı değil. En iyi 5 gün çıkınca H1 −106R, H2 −103R.
- **Tek pozisyon, spread ×1,5:** sonucu değiştirmiyor.

## 4. Tek iz: 4h alt fitil + öncesinde ≥ 2 ATR düşüş → AL ("korku döner")
- 2016-23 (1h icra): n 60, +0,29R (tip stop) / +0,33R (1 ATR stop), P %99,4–99,7, 8 yılın 5'i artı.
- 2024-26, aynı 1h icra: n 42, −0,01 / +0,10, P %47–75; 2026 −0,20…−0,33.
- 2024-26, 1m icra (ön-kayıtlı H8): KEŞİF +0,12 (23), TEST −0,17 (16).
- Sonuç: **C**. Mekanizma projenin tek sağlam ilkesiyle ("korku döner, coşku dönmez", §3-11; CAPREV, TR-C3) tutarlı.
  Ama son 3 yılda tutmuyor ve olay sayısı yılda ~10. Aynası (yükseliş sonrası üst fitil SAT) her dönemde negatif.

## Hüküm
**X.** NDX 1h/4h büyük fitilden sonra ters yönde (fitilin ret yönünde) gecikmeli girişin, 14.400 TP/SL/gecikme/eşik
kombinasyonunun hiçbirinde tesadüften ayırt edilebilen, bağımsız dönemde tutan bir kârı yok. Önceki bulgularla aynı yön:
fitil süpürmesi dönüş değil, devam eğilimli (MZ, §3-15). Üst fitil SAT ("coşku dönmez") her dönemde en kötü kol.
"Büyük hareketten sonra fitil" bağlamı (k = 1…3) da artıya çevirmiyor.

Canlıya ya da gölgeye bağlanacak bir kural yok. 4h düşüş sonrası alt fitil AL izi C olarak deftere yazıldı;
yeni veri birikirse (≥ 30 yeni olay) yeniden bakılabilir.

---

# 2. ve 3. tur — "her şeyi dene" (EK-1, EK-2, derin sınamalar)

Kullanıcı isteği: fitil büyüklüğünü, fitil sonrası giriş yerini, giriş zamanını ve TP/SL'yi sürekli değiştir, en kârlı
sonucu getir. Ön kayıtlar `PROTOCOL.md` EK-1/EK-2/EK-3. Kod: `engine2.py` (genel tensör motoru), `engine3.py` (yeni anatomi),
`build2.py`, `scan2.py`, `scan3.py`, `final2.py`, `final3.py`, `deep_l1h.py`, `cekic_bag.py`, `eslesik.py`, `ek3.py`.

## EK-1 — 4,4 milyon hücre
4 TF (30m/1h/2h/4h) × üst/alt fitil × RET/DEVAM × 360 fitil maskesi (baskınlık, fitil payı 0,3–0,7, fitil/ATR 0,2–1,5,
bağlam: yok/M1/M2/M3/uç20/son3) × 22 giriş (piyasa 0–60 dk, fitile geri çekilme limiti %25/50/75, gövde/kapanış/uç kırılım
stop'u) × 7 SL × 8 TP × 4 tutma. Motor tur 1 motoruyla 2.400 işlemde birebir tutuyor.

| aile | iki-dönem aday | şans ort. / %95 | hüküm |
|---|---|---|---|
| 30m üst fitil → DEVAM (AL) | 146 | 5,8 / 16 | şansı aşıyor → finalistler 2023'te −0,13…−0,55R |
| 30m alt fitil → RET (AL) | 24 | 8,5 / 17,8 | finalistler 2023'te −0,07…−0,19R |
| 4h üst fitil → RET (SAT) | 2 | 0,1 / 0,55 | n 46, 2023'te −0,09…−0,12R |
| kalan 13 aile | 0–43 | — | şans içinde |

TEST'te P %99 gösteren 30m DEVAM "son3" hücreleri (+0,47…+0,63R) hiç bakılmamış 2023'te çöktü. Tek bir mühürlü dönem yetmiyor.

## EK-2 — yeni anatomi
Çift fitil, fitil z-skoru (2/3), kapanış konumu, fitil büyümesi, gövde küçülmesi: hepsi şans içinde. **KORKU** (VIX ≥ 18,4
gününde alt fitil → AL) 2h'de 23 (şans 1,2 / %95 5), 4h'te 70 (1,7 / 11,8) aday.

| KORKU 4h STPkap SL 1,5 ATR TP 3R 8 mum | fitilli | fitilsiz eş (VIX ≥ 18,4 her 4h mum) |
|---|---|---|
| NDX 2024-26 (1m) | +0,31R (n 154, 24 korku dönemi, iki yarı +0,36 / +0,26) | +0,15R |
| NDX 2016-06 → 2023-02 (1h) | +0,072R (n 608) | +0,076R |
| DAX 2019-26 (1h) | +0,052R (n 826) | +0,063R |

İcra çözünürlüğü sebep değil (2024-26 1h icrayla da +0,29). **Sonuç:** kenar "korku rejiminde AL" (VIXREG/CAPREV/ORB×VIX'in
bildiği etki). Fitil yalnız 2024-26'da ek getiri veriyor, öncesinde ve DAX'ta vermiyor → **C**.

## Çekiç bulgusu (post-hoc, sonra bağımsız sınandı)
1h alt fitil adayının komşuluğunda fitil payı ≥ %70 kümesi üç dönemin üçünde tabanın üstündeydi. Hiç bakılmamış NDX 2016-23
ve DAX 2019-26'da sınandı. İki ölçüm tuzağı ayıklandı (E101):
1. TP'siz sürümde medyan işlem −1R; ortalama birkaç uç kazançla artı (R 3'te kırpılınca her sette eksi). Rastgele alt kümelerin
   ortalaması tüm kümenin 0,08–0,13 altında kaldı → ortalama kuyruk taşıyor.
2. TP 3R ile kuyruk sınırlanınca işlem başına eşli plasebo (aynı yıl + saat, aynı stop/ATR, aynı giriş kuralı, 10 rastgele mum)
   rastgele-olay sıfırında ≈ 0 (−0,06…+0,035) verdi, yani yöntem güvenilir.

| 1h fitil ≥ %70, gövde kırılımı girişi, stop fitil ucu, TP 3R, 16 mum | olay R | eşli plasebo | fark (P) |
|---|---|---|---|
| Çekiç AL — NDX 2016-23 | +0,008 | −0,108 | **+0,116 (0,997)** |
| Çekiç AL — DAX 2019-26 | +0,048 | −0,063 | **+0,111 (0,998)** |
| Çekiç AL — NDX 2024-26 | +0,185 | −0,025 | **+0,211 (0,999)** |
| Kayan yıldız SAT — NDX 2016-23 | −0,166 | −0,270 | +0,104 (0,98) |
| Kayan yıldız SAT — DAX 2019-26 | −0,128 | −0,210 | +0,082 (0,97) |
| Kayan yıldız SAT — NDX 2024-26 | −0,007 | −0,100 | +0,093 (0,88) |

**Kullanıcının sezgisi doğru çıktı:** uzun fitil ret yönünde gerçek bilgi taşıyor. İki piyasada, üç bağımsız dönemde, iki yönde
aynı geometrideki rastgele girişten ~+0,1R iyi. Ama aynı geometrideki rastgele giriş −0,03…−0,27R (dar stop + spread + SAT'ta
sürüklenme). Bu yüzden mutlak kâr yalnız AL tarafında ve küçük (2016-23 NDX'te ≈ 0).

## EK-3 — bilgiyi kâra çeviren geometri (144 kurgu × 3 bağımsız set, post-hoc)
Fitil ≥ %70 olayında TF {1h, 2h, 4h} × giriş {piyasa, gövde kırılımı} × SL {uç, uç ± 0,1 / 0,25 ATR} × TP {2, 3}R × tutma
{8, 16} × iki yön. Üç sette de R > 0 olan kurgu sayısı **17**; aynı sayıda rastgele mum "olay" sayıldığında 20 tekrarda 1–7
(ort. 3,8) → şansın üstünde. 92 kurguda olay R üç sette de rastgele ortalamanın üstünde. **SAT tarafında üç sette artı kurgu 0.**
Sıkı ölçütü (üç sette R > 0, en az ikisinde P ≥ 0,90) geçen 5 kurgunun beşi de **1h çekiç AL, TP 3R, 16 mum**.

### En kârlı sonuç: 1h çekiç
**Kural:** 1h mumda alt fitil ≥ aralığın %70'i ve ≥ 0,2 ATR14, alt fitil ≥ üst fitil → mum kapanınca piyasa AL (sonraki 1m
açılışı, ask) · stop fitil ucunun 0,1 ATR altı · TP 3R · 16 saat sonra kapanışta çık.

| set | n | ort.R | P | eşli plasebo farkı |
|---|---|---|---|---|
| NDX 2024-01 → 2026-11 (1m, bid/ask) | 690 | **+0,165** | 0,991 | +0,175 (P 0,994) |
| NDX 2016-06 → 2023-02 (1h) | 1.635 | +0,019 | 0,67 | +0,086 |
| DAX 2019 → 2026-10 (1h) | 1.842 | +0,054 | 0,91 | +0,095 |
| NDX 2023-03 → 12 (15m) | 173 | +0,101 | 0,75 | −0,03 (rastgele AL da kazandı) |

NDX 2024-26 kartı: spread ×1,5 +0,131, ×2 +0,103 · tek pozisyon +0,150 (n 568) · iki yarı +0,221 / +0,109 · ay %79 artı ·
isabet %37,4 (3R'de başabaş %25) · en iyi 5 gün hariç +74,6R · yıl 2024 +0,24, 2025 +0,13, 2026 +0,11 · stop medyanı 0,9 ATR.
Gövde-kırılımı girişli eşi (stop uç − 0,1 ATR) +0,178R, 2026 +0,12, aynı tablo.
**Giriş zamanı:** kapanış 0 dk +0,127 (uç − 0,25 ATR stoplu), 5 dk +0,146, 10–20 dk +0,09, 30 dk +0,12, 45–60 dk +0,07 →
beklemek kazandırmıyor, en iyisi ilk 5 dk.

### Sınıf ve sınırlar
**B−.** Seçim post-hoc; bağımsız setlerde işaret tutuyor ama eski NDX'te mutlak kâr ≈ 0 (+0,02R). Kârın çoğu 2024-26 ve AL
yönünden geliyor (yükselen piyasa + son yılların korku-dönüşleri). Canlı için önce gölge, sonra `go_live_gate.py` kartı gerekir
(2. KURAL). Bu oturumda bota bağlanmadı.

## Tüm turların "en kârlı" tablosu (dürüst etiketli)
| # | kural | 2024-26 R | eski veri R | etiket |
|---|---|---|---|---|
| 1 | 1h çekiç, piyasa AL, SL uç−0,1 ATR, TP 3R, 16 sa | +0,165 (n 690) | NDX16-23 +0,02 · DAX +0,05 | **B−**, fitil bilgisi gerçek (+0,1R plasebo üstü) |
| 2 | 4h alt fitil ∧ VIX ≥ 18,4, kapanış+0,1 ATR kırılımı AL, SL 1,5 ATR, TP 3R, 8 mum | +0,311 (n 154) | NDX16-23 +0,072 · DAX +0,052 | C — kâr VIX rejiminden, fitil eski veride katkısız |
| 3 | 30m üst fitil + son3 → DEVAM AL, SL 2 ATR, 8 sa | TEST +0,63 (n 118) | 2023 −0,13 | X — çöktü |
| 4 | 1h/4h üst fitil → SAT (kullanıcının ilk hipotezi) | −0,13 … +0,13 | hep negatif | X — fitil bilgisi var ama sürüklenme + maliyet yiyor |

## Yeni kanıt tuzağı (E101)
TP'siz / uzun tutmalı kuralda ortalama birkaç uç işlemle taşınır. Rastgele alt kümelerin ortalaması tüm kümenin sistematik olarak
altında kalır (NDX 1h: −0,08…−0,13). Medyan −1R iken ortalama artı olabilir. Önlem: kırpılmış ortalama (R ≤ 3) ve medyan raporla,
TP ile kuyruğu sınırla; işlem başına eşli plasebonun (aynı yıl/saat/stop-ATR/giriş kuralı) rastgele-olay sıfırında ≈ 0 verdiğini
ayrıca göster.

## Kart ve EK-4 (çekici iyileştirme denemesi)
**Yerel canlıya alma kartı** (`kart_cekic.py` → `backend/data/evolution/go_live_cards/ndx_cekic_1h_yerel.json`; MT5 kutu kartının
yerine geçmez):
| ölçüt | Dukascopy 2024-26 | broker NAS100 1m 2026-02→10 |
|---|---|---|
| 1 hacim | 690 ✓ | 173 ✓ |
| 2 beklenti | +0,165, P 0,992 ✓ | +0,062, P 0,68 ✗ |
| 3 iki yarı | +0,221 / +0,109 ✓ | +0,291 / **−0,164** ✗ |
| 4 spread ×1,5 | +0,131 ✓ | +0,037 ✓ |
| 5 icra (iyimser − gerçek ≤ R/2) | 0,075 ≤ 0,083 ✓ (sınırda) | 0,005 ✓ |
| 6 tek pozisyon | +0,150 ✓ | +0,150 ✓ |
| verdikt | LIVE-adayı | **SHADOW** |
2026'nın ikinci yarısında broker beslemesinde zayıflama var; Dukascopy 2026 +0,107 (n 195).

**EK-4** (720 hücre: 15 bağlam × 48 geometri; seçim yalnız KEŞİF'te, doğrulama TEST + NDX 2016-23 + DAX + broker 2026;
bağlam katkısı = bağlamlı − bağlamsız, boş = aynı büyüklükte rastgele çekiç alt kümesi): 86 KEŞİF adayından yalnız 1'i en az üç
doğrulama setinde boşun %90'ını aştı (şans düzeyi). **Bağlam (trend, düşüş sonrası, dip20, seans, VIX, oynaklık) çekici
iyileştirmiyor.** Beş setin beşinde artı kalan kurgular bağlamsız çekiçte uzak hedefli olanlar:

| SL uç − 0,1 ATR | KEŞİF | TEST | NDX 2016-23 | DAX | broker 2026 |
|---|---|---|---|---|---|
| TP 5R, 24 sa | +0,261 | +0,069 | +0,030 | +0,130 | +0,023 |
| TP 3R, 16 sa | +0,211 | +0,109 | +0,019 | +0,054 | +0,062 |
| TP 5R, 16 sa | +0,283 | +0,094 | +0,023 | +0,096 | +0,019 |

## Son hüküm
Bulunabilen en kârlı ve en sağlam kural **1h çekiç AL** (bağlamsız, SL uç − 0,1 ATR, TP 3–5R, 16–24 sa). Beş bağımsız sette artı,
ama eski NDX'te ve broker 2026'da işlem başı +0,02…+0,06R, yani maliyete yakın ince bir kenar. Kârın büyük kısmı 2024-25'ten. Sınıf
**B−**. Doğru sıradaki adım emirsiz gölge kaydı + kutuda MT5 kartı. Fitilin üst/SAT tarafı ve tüm bağlam/çift/z/korku türevleri kâra dönmüyor.

## EK-5 — çekiçte giriş yeri, zamanı, çıkış; XAU/USOIL (400 hücre × 6 set)
| giriş tipi (KEŞİF adayları içinde) | dört NDX doğrulama setinde artı oranı |
|---|---|
| fitilin %25 / 50 / 75'ine limit | %0 (dolum düşüş sürerken geliyor, ters seçilim) |
| piyasa +5 dk / 5m teyit mumu | %0 |
| piyasa 0 dk | %34 |
| mum tepesi kırılımı (240 dk) | %32 |
| gövde üstü kırılımı | %52 |
| kapanış + 0,1 ATR kırılımı | %65 |
XAU ve USOIL'de 400 kurgunun en iyileri de eksi → çekiç **endekse özgü** (MK-03/05 ile tutarlı).

### En kârlı kural: çekiç + tepe kırılımı
**Kural:** 1h mumda alt fitil ≥ aralığın %70'i ve ≥ 0,2 ATR (alt ≥ üst) → sonraki 4 saatte mumun **tepesi kırılırsa** AL (stop emri) ·
stop fitil ucu (mumun dibi) · TP 5R · 24 saat sonra kapanışta çık. Kullanıcının "yön tersine kırılıyor" tarifinin karşılığı.

| set | n | ort.R | P | eşli plasebo farkı | not |
|---|---|---|---|---|---|
| NDX Dukascopy 2024-26 | 633 | **+0,231** | 0,994 | K +0,20 / T +0,12 | kart 6/6 · yarılar +0,30 / +0,17 · sp×1,5 +0,21 · tek +0,27 · 2026 +0,10 · isabet %30 (başabaş %17) |
| broker NAS100 2026 | 158 | +0,175 | 0,84 | — | ikinci yarı −0,01 → SHADOW (kılpayı) |
| NDX 2016-23 (1h) | 1.541 | +0,031 | 0,73 | **+0,23 (P 1,00)** | 5/8 yıl artı, en iyi 5 gün hariç −7,6R |
| DAX 2019-26 (1h) | 1.681 | +0,090 | 0,96 | **+0,21 (P 1,00)** | 7/8 yıl artı, 2026 −0,15 |
Kapanış + 0,1 ATR kırılımlı eşi: Dukascopy +0,199 (6/6), broker 2026 +0,144, NDX 2016-23 +0,031, DAX +0,142.

**Sınıf B−.** Seçim EK-5 içinden (post-hoc). Fitilin bilgisi bağımsız setlerde çok güçlü (plasebo +0,21…+0,23R, P 1,00) ama eski
NDX'te mutlak kâr +0,03R ve en iyi 5 gün çıkınca sıfır. Para ağırlıkla 2024-26 NDX'ten ve DAX'tan geliyor. 2026'nın ikinci yarısında
iki piyasada da zayıflama var. Doğru adım emirsiz gölge kaydı + kutuda MT5 kartı.

## MT5 kutu sınaması — bağımsız broker beslemesi (2026-11-07, `remote.py ask`, betikler kutuda `research/fitil_ret_20261106/kutu/`, commit edilmedi)
Pepperstone-Demo 61628380, NAS100, `copy_rates_range`, sunucu = NY + 7 (`broker_time.rule_offset_sec`), bar spread'i (0 olanlar yıl
medyanı). H1 2018-01-02 → 2026-11-06 (52.193 bar), M1 yalnız 2026-07-28'den beri. H1 çözünürlükte giriş barında dibe değilse stop sayıldı
(muhafazakâr; aynı 85 olayda M1 +0,066 ↔ H1 −0,005 → H1 sonuçları ~0,07R aşağı yanlı).

| çekiç + tepe kırılımı AL (stop dip, TP 5R, 24 sa) | değer |
|---|---|
| n (sinyal / işlem) | 2.286 / 2.081 |
| ort. R · isabet · P(EV>0) | **+0,075** · %25,9 · **%93,9** |
| taban (aynı kural tüm H1 mumları, saat ağırlıklı) | −0,087 → fark **+0,16R** (yalnız boy koşullu taban −0,007) |
| spread ×1,5 | +0,061 (P %90,4); yıl medyanı ×1,5 +0,065 |
| kronolojik iki yarı | +0,088 / +0,062 |
| tek pozisyon | +0,083 (n 1.659, P %95,2) |
| en iyi 5 gün hariç | 155,9R → 90,3R (ort. +0,044) |
| yıl | 2018 −0,15 · 2019 +0,16 · 2020 +0,31 · 2021 +0,09 · 2022 −0,03 · 2023 −0,05 · 2024 +0,32 · 2025 −0,04 · 2026 +0,04 |
| M1 dönemi (icra ölçütü) | n 85, +0,066 — ölçüt için yetersiz |
Ayna (üst fitil → dip kırılımı SAT): −0,077R, P %8,5, spread ×1,5 −0,117 → **X**.

**Güncel sınıf: B.** Kural Dukascopy 2024-26'da (6/6), NDX 2016-23 arşivinde, DAX'ta ve şimdi bağımsız broker beslemesinde 9 yıl
boyunca (2.081 işlem, P %94, tabanın +0,16R üstü) artı. Zayıf yanlar: 9 yılın 4'ü hafif eksi, kâr birkaç yılda yoğun, işlem başı
beklenti broker'da +0,06…+0,08R (H1 yanlılığıyla belki +0,14). İcra ölçütü M1 geçmişi kısa olduğu için ölçülemedi → **gölge zorunlu**:
≥150 gölge olayla M1 icrası ölçülmeden canlıya alınmaz (2. KURAL).

## Birleşik canlıya alma kartı (`backend/data/evolution/go_live_cards/ndx_cekic_tepekir_1h.json`)
1 hacim MT5 H1 2.081 ✓ · 2 beklenti MT5 +0,075 P %93,9 / Dukascopy +0,231 P %99,4 ✓ · 3 iki yarı MT5 +0,088 / +0,062 ✓ ·
4 spread ×1,5 MT5 +0,061 (P %90,4) ✓ · 5 icra broker 1m 2026 n 158: iyimser +0,188 − gerçek +0,175 = 0,013 ≤ 0,088 ✓ (Dukascopy
n 633: 0,061 ≤ 0,115 ✓) · 6 tek pozisyon MT5 +0,083 ✓ → **6/6, LIVE-adayı, sınıf B**. 2. KURAL'a göre karar kullanıcıda. Zayıf
yanlar kartta yazılı (4/9 eksi yıl, kârın %42'si 5 günde, ince beklenti, post-hoc seçim). Önerilen sıra: emirsiz gölge → ≥150 canlı-fiyat olayı → küçük lot.

## Kör taşınma sınaması (MT5 H1 2018-26, kural değiştirilmeden; `remote.py ask`)
| sembol | ort. R | P | not |
|---|---|---|---|
| US500 | −0,029 | — | 2026 −0,30 |
| US30 | −0,006 | — | 2026 −0,20 |
| US2000 | −0,086 | 0,033 | anlamlı eksi |
| GER40 | +0,046 | 0,83 | iki yarı +, en iyi 5 gün hariç +0,012 |
| NAS100 | +0,072 | 0,93 | |
| **havuz (5)** | **−0,000** | 0,49 | spread ×1,5 −0,019 |
Olay her sembolde aynı kuralın tabanından +0,08…+0,16R iyi (fitilin ret bilgisi evrensel), ama tabanlar −0,09…−0,24 olduğundan
mutlak beklenti sıfır. **Kural taşınmıyor → genel bir "fitil kenarı" değil, NAS100'e (kısmen DAX'a) özgü.** TR-C3b'de aynı
kör sınama dört endeksin dördünde geçmişti; burada geçmedi. Sınıf **B'den B−'ye** indi: NAS100 kartı 6/6 ama tek-piyasa
sonucu, seçim etkisi dışlanamıyor. Canlı para önerilmez; olursa yalnız emirsiz gölge.

# EK-6 — farklı stratejiler (2026-11-07)
**A. Günlük çekiç AL** (`d1.py`, `d1_kontrol.py`; 1.920 hücre/yön, seçim QQQ 2000-14): ertesi açılışta AL, stop 1 ATR, TP 5R, 5 gün.
ETF RTH günlük mumlarında beş kör setin beşinde artı ve aynı kuralın tabanının üstünde: QQQ +0,161 (taban +0,073), SPY +0,085 (+0,051),
DIA +0,124 (+0,061), IWM +0,055 (+0,005), DAX +0,102 (+0,035); iki dönemde de artı. Rastgele gün sıfırının %95'ini yalnız QQQ/DIA açıkça
aşıyor. Kayan yıldız SAT: KEŞİF adayı 0. CFD finansmanı (yıllık %5–7) eklenince mutlak kâr yalnız QQQ'da kalıyor (+0,09…+0,11).
**Kutuda MT5 CFD D1 (gerçek swap_long −6,41 / −4,94 %, bar spread):** NAS100 +0,036 (fark −0,058), US500 −0,053, US30 −0,059,
US2000 −0,030, GER40 +0,030; havuz −0,004 (taban +0,037) → **CFD'de X**. ETF/RTH ile CFD/23 saat günlük mum tanımı ve veri dönemi
farklı; fitil üstünlüğü CFD mumunda yok. ETF nakit işlemi için C (bot kapsamı dışında).
**B. Kayan yıldızı uzun pozisyonda çıkış yapmak** (`d1_cikis.py`; SMA50 trend ve sürekli uzun tabanları, k = 3/5/10 gün ya da tepe aşılana
kadar nakit): beş piyasa × iki dönemde ΔSharpe çoğunlukla −0,05…−0,35 → **X** (coşku dönmez; çıkış da işe yaramıyor).
**C. 1h çekiç + günlük bağlam** (`ek6c.py`): dün günlük çekiç (+0,52 / 0,00 / −0,13 / +0,12), dünkü dibi süpürme (−0,42 / +0,27 /
+0,03 / −0,20), SMA50 üstü (≈ 0), gün içi sert düşüş (eksi) — setten sete işaret dönüyor → **X**.

## Güncel en iyi sonuç (değişmedi)
**1h çekiç + tepe kırılımı AL** (FR-10/11): MT5 NAS100 2018-26 +0,075R (P %94, taban −0,087), kart 6/6, ama başka endekslere
taşınmıyor (FR-12) → **B−, yalnız NAS100**. EK-6'nın yeni aileleri bunu geçemedi; günlük çekiç ETF'de güzel görünüp CFD'de çöktü.

# EK-7 — kombo, öncesi/sonrası anatomi, portföy (2026-11-07)
`ek7.py`, `portfoy.py`, `kart_teyit.py`; kutuda `research/fitil_ret_20261106/kutu/sonuc_varyant.md`.

**Kombo + öncesi** (FR-10 çekiç × 8 gün filtresi + 4 öncesi filtre, 5 yerel set, katkı = komboluk − taban, boş = rastgele alt küme):
ön-kayıtlı ölçütü (≥ 4/5 artı, ≥ 3'ünde boşun %90'ı üstü, her sette n ≥ 20) geçen yok. En yakını RSI2(D1) < 10 (TP 3R/16 sa:
NDX K +0,26, T −0,09, 2016-23 +0,34, DAX +0,17, broker +0,07 n 18). Kutuda 5 endekste (MT5 H1 2018-26): havuz katkı +0,096 (TP 3R),
ama US2000'de −0,195 ve TP 5R'de +0,027 → kararsız, **C**. 3 gün düşüş, boşluk, SMA200 rejimi, önceki kırmızı mumlar, alçalan dip,
sert gövde, gün içi dip: tutarsız → **X**. Çift çekiç ve inside-sonra-kırılım: tutarsız → **X**.

**Sonrası: TEYİTLİ ÇEKİÇ** (önceden yazılmış varyant) — **bu çalışmanın en iyi sonucu.**
**Kural:** 1h mumda alt fitil ≥ aralığın %70'i ve ≥ 0,2 ATR14 (alt ≥ üst) → **sonraki 1h mum çekicin tepesinin üstünde kapanırsa**
(ve çekicin dibini kırmadıysa) bir sonraki mumun açılışında AL · stop çekicin dibi · TP 5R · 24 saat.

| set | n | ort. R | P | not |
|---|---|---|---|---|
| NDX Dukascopy 2024-26 (1m bid/ask) | 281 | **+0,239** | 0,977 | yerel kart **6/6** (yarılar +0,20 / +0,28, sp×1,5 +0,22, tek +0,22, icra farkı 0,026) |
| NDX 2016-06 → 2023-02 (1h) | 611 | **+0,210** | 0,998 | 7/8 yıl artı (2022 −0,07) |
| DAX 2019 → 2026-10 (1h) | 701 | **+0,189** | 0,997 | 6/8 yıl artı (2019 −0,22, 2026 −0,06) |
| broker NAS100 2026 (1m) | 66 | +0,060 | 0,60 | küçük örneklem |
| **MT5 NAS100 2018-26** | 906 | **+0,124** | 0,98 | yarılar +0,13 / +0,12 |
| **MT5 US500** | 696 | +0,052 | 0,77 | |
| **MT5 US30** | 862 | +0,071 | 0,86 | |
| **MT5 US2000** | 767 | +0,029 | 0,67 | |
| **MT5 GER40** | 738 | **+0,144** | 0,99 | yarılar +0,13 / +0,16 |
| **MT5 havuz (5)** | 3.969 | **+0,085** | 0,98 | ham çekiçten +0,086 (P 1,00), sp×1,5 +0,061 (P 0,95), yarılar +0,088 / +0,083 |

**Sınıf B.** Önceden yazılmış bir varyant; 10 setin 10'unda mutlak artı, beş piyasaya kör taşınıyor (fitil kurallarında ilk kez),
spread stresine dayanıklı. Zayıf yanlar: 2026'da yavaşlama (Dukascopy NDX 0,00, DAX −0,06, broker +0,06); MT5 havuzunda endeksler aynı
günlerde hareket ettiği için bağımsız n daha küçük; US2000/US500 ince. İcra ölçütü Dukascopy'de geçti (kapanış-girişi ile fark 0,026 ≤ 0,12).

**Portföy (Dukascopy NDX 2024-26, örneklem içi):** FR-10 çekiç (işlem başı %0,5 risk) yıllık %28 / Sharpe 1,51 / maxDD −%16,7;
TR-C3 RSI2 (eş oynaklık) %34 / 1,76 / −%8,6; günlük korelasyon 0,10; 50/50 → %32 / **Sharpe 2,21 / maxDD −%7,0**. Fitil kuralı ile
korku-dönüşü kuralları birbirini tamamlıyor. MT5 geniş döneminde FR-10 beklentisi üçte biri olduğu için gerçek Sharpe daha düşük olur.

# EK-8 — teyit ilkesinin genellenmesi (2026-11-07)
| hücre | yerel 5 set (K / T / 2016-23 / DAX / broker) | MT5 H1 2018-26 havuz (5 endeks) | hüküm |
|---|---|---|---|
| teyitli kayan yıldız SAT 1h | +0,42 / −0,25 / −0,10 / −0,09 / −0,36 | −0,052 (P 0,12) | X |
| teyitli çekiç 30m | +0,29 / +0,15 / — / — / +0,34 | +0,011 (P 0,63); NAS100 +0,131, diğer dördü ≤ 0 | X (genel) |
| teyitli çekiç 2h / 4h | ≈ 0 / karışık | — | X |
| teyitli çekiç 1h fitil ≥ %60 | +0,22 / +0,12 / +0,08 / +0,16 / +0,11 | +0,027 (P 0,81), sp×1,5 +0,003 | C |
| teyitli çekiç 1h fitil ≥ %50 | +0,19 / +0,11 / +0,06 / +0,11 / +0,02 | +0,032 (P 0,88), sp×1,5 +0,011 | C |
| **referans FR-15 (≥ %70)** | +0,32 / +0,15 / +0,21 / +0,19 / +0,06 | **+0,085 (P 0,98)**, sp×1,5 +0,061 — birebir yeniden üretildi | **B** |

Teyit ilkesi yalnız 1h, fitil ≥ %70 ve AL yönünde çıtayı geçiyor; eşik gevşeyince ve TF değişince MT5'te sönüyor. Bu, FR-15'in dar bir
tepe olduğunu ve beklentinin ince kalacağını gösteriyor. Sembol deseni tüm hücrelerde aynı: NAS100 ve GER40 artı, US500 ≈ 0, US2000 eksi.
FR-15 sınıfı **B** kalıyor ama "komşulukta kırılgan" notuyla; gölgede yalnız NAS100 + GER40 izlenmesi mantıklı (post-hoc seçim, bunu da gölge ölçsün).

# Portföy — MT5 broker verisi 2018-01 → 2026-11 (kutu `portfoy_fr15_c3b.py`, commit edilmedi)
FR-15 teyitli çekiç (işlem başı risk %0,5) NAS100 + GER40 ve TR-C3b (NAS100 M30, `yeni deneme/c3b_shadow.py` çekirdeği; oynaklığı
FR-15'e eşitlendi, nominal 1,94×).
| seri | yıllık | Sharpe | maxDD | kârlı ay |
|---|---|---|---|---|
| FR-15 NAS100 | +%6,1 | 0,63 | −%13,4 | %46 |
| FR-15 GER40 | +%5,8 | 0,69 | −%10,6 | %50 |
| FR-15 ikisi | +%12,2 | 0,89 | −%17,5 | %56 |
| C3b | +%21,1 | 1,45 | −%15,1 | %54 |
| **üçü eşit ağırlık (1/3)** | **+%11,2** | **1,63** | **−%5,8** | **%67** |
| üçü tam boyut | +%35,8 | 1,63 | −%16,9 | %67 |
Günlük korelasyon FR NAS–GER 0,079, FR–C3b 0,02. Yıl: eşit ağırlık 2018 +2,1 · 2019 +4,0 · 2020 +23,9 · 2021 +11,7 · 2022 +4,7 ·
2023 +5,9 · 2024 +22,2 · 2025 +18,7 · 2026 +8,1 (9/9 yıl artı). En kötü ay 2022-01 −%4,6.
**Sınırlar:** C3b oynaklık ölçeği tüm örneklemden (ileriye bakan); FR-15'te çakışan pozisyonların marj yükü modellenmedi; sembol seçimi
(NAS100 + GER40) EK-8 sonrası post-hoc; FR-15 2026'da −%6,2. **Sonuç:** tek başına ince olan fitil kuralı, ilişkisiz korku-dönüşü kuralıyla
birlikte 9/9 yıl artı, Sharpe 1,6, düşüş −%6 bir portföy veriyor. Bu bulunan en kârlı **kombo**; canlı için gölge + kart gerekir.
