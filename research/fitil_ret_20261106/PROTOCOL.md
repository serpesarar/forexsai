# NDX 1h / 4h büyük fitil → ters yön (ret) — ön kayıt (2026-11-06, HİÇBİR sonuç görülmeden yazıldı)

## İstek (kullanıcı)
NDX 1h veya 4h mumlarında fitili büyük olan mumlar: üst fitil büyükse ayrı, alt fitil büyükse ayrı incelenir.
Mum kapandıktan 5 / 10 / 15 / 20 dk sonra **fitilin ters yönüne** (üst fitil → SAT, alt fitil → AL) işlem açılır;
TP/SL deneme-yanılmayla oynatılır, bir kâr kapısı aranır. Gerekçe: büyük yükseliş/düşüşlerde fitiller büyür,
yön kırılır, düzeltme gelir.

## Defter kontrolü (3. KURAL)
| kayıt | ne | sonuç |
|---|---|---|
| MK-01/02 | pin bar @20-mum tepesi (üst fitil ≥ 2/3), NDX 1h 10y, 20 mum tut | ret (SAT) yönü MK-01'de negatif; TERS (AL, devam) bile 10y'da tabanın −0,076 altı → X |
| MZ-01/03 | 1H/4H fitil süpürmesi (fraktal / önceki mum ucu) → dönüş | −0,15R civarı, devam yönü hafif artı → X |
| FC-05 | açılışta fitil-fade | −0,14 / −0,22 → X |
| IO-17 | alt fitil / kapanış konumu SL ayrımı | AUC 0,41 zayıf |
| §3-15 | süpürme tek başına dönüş değil | — |
| §3-11 | "korku döner, coşku dönmez" | önsel: alt fitil AL (korku sonrası) > üst fitil SAT (coşku sonrası) |

**Yeni olan:** (i) konum şartı yok — genel büyük fitil (fitil payı + ATR büyüklüğü), (ii) 0–20 dk gecikmeli giriş,
(iii) "büyük hareketten sonra" bağlamı (kullanıcının mekanizması), (iv) geniş TP/SL ızgarası ve seçim düzeltmesi,
(v) Dukascopy bid/ask 1m ile 2024-01 → 2026-11 (MK-02'de M1 icra yalnız kısa dönemdeydi).
**Önsel beklenti:** üst fitil SAT ≤ 0 (coşku dönmez, MZ); alt fitil AL hafif artı ama tabana (sürüklenme) göre ~0.

## Veri
- NDX 1m Dukascopy (`haber_derin_20261105/data/NDX_1m.parquet`): bid OHLC + ask_open/ask_close, 2024-01-01 → 2026-11-03
  (2026-01 eksik). Spread = ask − bid bar bazında.
- **KEŞİF:** 2024-01-01 → 2025-06-30. **TEST:** 2025-07-01 → 2026-11-03 (mühürlü; yalnız ön-kayıtlı hipotezler + KEŞİF'te seçilen tek hücre).
- **BAĞIMSIZ (mekanizma):** `ndx_gate_forge/data/long_1h_utc.parquet` 2016-06 → 2023-12, 1h çözünürlük; giriş = sonraki 1h açılışı
  (D = 60 dk yaklaşımı), çıkış 1h barlarda, aynı barda SL+TP → SL, sabit spread 1,5. Yalnız 1h hipotezleri.

## Mumlar
- 1h: UTC saat başı kovaları. 4h: **17:00 ET çapası** (17-21-01-05-09-13 NY), MZ ile aynı.
- Bir HTF mumu son 1m barı kapanınca bilinir; mum içinde > 30 dk veri yoksa mum atılır (eksik mum).
- ATR14 = son 14 HTF mumunun (sinyal mumu DAHİL, hepsi kapanmış) gerçek aralık ortalaması.

## Olay tanımı
- Aralık R = H − L; üst fitil UW = H − max(O, C); alt fitil LW = min(O, C) − L.
- **Üst fitil olayı:** UW/R ≥ s, UW/ATR ≥ w, UW ≥ 2·LW. → **SAT**. Alt fitil: ayna → **AL**.
- **Bağlam (kullanıcı mekanizması):** önceki hareket M = (C_sinyal − C_{6 mum önce}) / ATR. Üst fitil için M ≥ k (yükseliş
  sonrası), alt fitil için M ≤ −k. k = 0 → bağlam yok.

## Giriş / çıkış / icra
- Giriş: HTF kapanışından D dk sonraki ilk 1m barının açılışı. SAT bid'den, AL ask'tan.
- SL seçenekleri: **fitil ucu + 0,1·ATR** (SAT: H + 0,1 ATR, AL: L − 0,1 ATR; giriş fitil ucunun ötesindeyse işlem yok),
  0,5 / 1,0 / 1,5 ·ATR (girişten).
- TP: SL mesafesinin r katı, r ∈ {0,5, 1, 1,5, 2, 3}.
- Zaman stopu: 1h → 8 mum (8 sa), 4h → 6 mum (24 sa); > 3 sa veri boşluğundan önceki son barın kapanışında çık.
- SAT stopu ask ile tetiklenir (bid high + spread), AL TP'si bid ile. Aynı 1m barında SL+TP → SL. Bar stopun ötesinde açılırsa açılıştan çık.
- R = net (spread dahil) kâr / SL mesafesi.

## Birincil hipotezler (8, Holm)
Ortak: s = 0,5, w = 0,5, SL = fitil ucu + 0,1·ATR, TP = 1R, D = 5 dk.
| ID | TF | yön | bağlam |
|---|---|---|---|
| H1 | 1h | üst fitil → SAT | k = 0 |
| H2 | 1h | alt fitil → AL | k = 0 |
| H3 | 4h | üst fitil → SAT | k = 0 |
| H4 | 4h | alt fitil → AL | k = 0 |
| H5 | 1h | üst fitil → SAT | k = 2 (yükseliş sonrası) |
| H6 | 1h | alt fitil → AL | k = 2 (düşüş sonrası) |
| H7 | 4h | üst fitil → SAT | k = 2 |
| H8 | 4h | alt fitil → AL | k = 2 |

## Keşif ızgarası (kullanıcının "deneme yanılma"sı)
s ∈ {0,4, 0,5, 0,6} × w ∈ {0,3, 0,5, 0,8} × k ∈ {0, 1, 2, 3} × D ∈ {0, 5, 10, 15, 20} × SL 4 × TP 5, her TF × yön.
= 3·3·4·5·4·5 = 3.600 hücre / (TF, yön), toplam 14.400. Hücre n_KEŞİF ≥ 40 değilse sayılmaz.
- **Seçim:** her (TF, yön) için KEŞİF'te tabana göre fark t-istatistiği en yüksek hücre → TEST'te bir kez.
- **Seçim düzeltmesi (E24):** saat-içi permütasyon — aynı saat dilimindeki mumlar arasında olay özellik vektörü (s, w, M)
  karıştırılır, ızgaranın tamamı yeniden koşulur, en yüksek t alınır; 200 tekrar. Gerçek en iyi t, boş dağılımın %95'ini geçmezse
  ızgara "bulunamadı" sayılır.
- İyi↔kötü simetrisi (E26/E28): |t| ≥ 2 iyi ve kötü hücre sayıları boş dağılımla birlikte raporlanır.

## Taban ve kontroller
- **Taban (E13/E15):** aynı dönem, aynı yön, aynı D/SL/TP ile TÜM HTF mumlarında aynı işlem; olayların UTC saat dağılımına göre
  ağırlıklı. Fark = olay ort.R − taban ort.R. (Fitil ucu SL'i için taban mumun kendi ucu kullanılır.)
- **Ayna:** aynı an ters yön (devam), aynı SL mesafesi ve r.
- Spread × 1,5; tek pozisyon (aynı TF+yönde açık işlem varken yenisi yok); gün-blok bootstrap (NY günü, 17:00 ET sınırı).

## Hüküm ölçütleri (her birincil hipotez ve seçilen hücre)
1. TEST ort.R > 0 ve gün-blok bootstrap P(EV > 0) ≥ 0,90.
2. TEST fark (olay − saat-ağırlıklı taban) > 0.
3. KEŞİF ort.R > 0 (seçilen hücrede bu otomatik; onun yerine seçim düzeltmesi p < 0,05).
4. BAĞIMSIZ 1h (yalnız 1h): ort.R ≥ 0 ve fark ≥ 0.
5. TEST spread × 1,5 ort.R > 0.
6. n (KEŞİF + TEST) ≥ 150.
7. TEST tek-pozisyon ort.R > 0.
8. TEST'te aynadan iyi.

Sınıf: **B** hepsi + Holm (birincil) · **B−** hepsi Holm'suz · **C** 1 sağlanır, biri düşer · **X** 1 düşer.
B bile yalnız gölge adayıdır (2. KURAL kartı ayrıca).

## Tanı kırılımları (hüküm dışı)
Yıl, seans (Asya 18–02, Londra 02–08:30, NY sabah 08:30–11, NY öğle 11–17 ET), RTH/ETH, gecikme eğrisi (D),
TP eğrisi, "teyit" (girişte fiyat sinyal kapanışının ret yönünde mi), en büyük 5 günü çıkararak toplam.

---

# EK-1 — Geniş tarama (2. tur, 2026-11-06, tur 1 sonuçları görüldükten SONRA ama EK-1 hücrelerinin hiçbiri görülmeden)

Kullanıcı isteği: fitil büyüklüğü, fitil sonrası giriş yeri, giriş zamanı, TP/SL — hepsini oynat, en kârlı sonucu getir.
Tur 1 bilgisi (açıkça kayıtlı): 1h ret yönü negatif, devam ≈ 0, fitil-ucu stop tabanı yanıltıcı (E100) → EK-1 hükmü
**mutlak R** ve **aynı kuralın rastgele mumlardaki ATR-stoplu eşi** ile verilir.

## Boyutlar
- **TF:** 30m, 1h, 2h, 4h (2h ve 4h 17:00 ET çapalı; 30m/1h saat başı).
- **Olay (fitil anatomisi):** baskın fitil oranı (fitil ≥ ρ × karşı fitil), ρ ∈ {1, 2}; fitil payı s = fitil/aralık ∈ {0,3 0,4 0,5 0,6 0,7};
  fitil büyüklüğü w = fitil/ATR14 ∈ {0,2 0,35 0,5 0,75 1,0 1,5};
  bağlam ∈ {yok, M ≥ 1, M ≥ 2, M ≥ 3 (6 mumda fitil yönünde hareket, ATR), uç20 (fitil ucu son 20 mumun en uç noktası),
  sön3 (önceki 3 mumun aralığı sırayla küçülüyor + M ≥ 1: "hareket yavaşlıyor")}.
  → 2 × 5 × 6 × 6 = 360 maske / (TF, olay yönü).
- **İşlem yönü:** RET (fitilin tersi: üst fitil → SAT) ve DEVAM (fitil yönü). İkisi ayrı aile.
- **Giriş (RET):** PİYASA D ∈ {0, 5, 10, 15, 20, 30, 45, 60} dk; LİMİT fitile geri çekilme q ∈ {0,25 0,5 0,75}
  (SAT limiti gövde üstü + q × fitil, kapanıştan sonra 60 dk geçerli); STOP-KIRILIM: sinyal mumunun gövde altı / kapanış − 0,1 ATR
  kırılınca SAT (120 dk geçerli). **Giriş (DEVAM):** PİYASA D (aynı 8) + STOP fitil ucu + 0,05 ATR kırılımı (120 dk).
- **SL:** fitil ucu (ters uç) + p·ATR, p ∈ {0, 0,1, 0,25}; girişten 0,5 / 1 / 1,5 / 2 ATR. (DEVAM için "uç" = mumun karşı ucu.)
- **TP:** {0,5 0,75 1 1,5 2 3} R; yapı = mumun karşı ucu (RET SAT için mum dibi); yok (yalnız zaman).
- **Tutma:** {2, 4, 8, 16} HTF mum (boşluk > 3 sa öncesi kapanış).
- **İcra:** tur 1 ile aynı (1m bid/ask, aynı barda SL+TP → SL). Limit dolumu: bid high ≥ seviye (SAT) — dolum barında SL'e de
  dokunulmuşsa SL sayılır. Stop-giriş: seviye ya da boşluklu açılış. Risk < 2 × spread olan işlem yok.

## Dönemler
KEŞİF 2024-01 → 2025-06 (seçim), TEST 2025-07 → 2026-11 (tur 1'de yalnız tur-1 hücrelerine bakıldı), **BAĞIMSIZ-A**
NDX 15m 2023-03-08 → 2023-12-31 (`long_15m_utc`, spread 1,5, giriş/çıkış 15m çözünürlükte, D yukarı yuvarlanır),
**BAĞIMSIZ-B** NDX 1h 2016-06 → 2023-02 (yalnız TF ≥ 2h, D ≥ 60 dk; 1h çözünürlük).

## Seçim ve hüküm
1. Hücre: n_KEŞİF ≥ 60, n_TEST ≥ 40.
2. **İki-dönem adayı:** KEŞİF ort.R > 0 ve t ≥ 2,5; TEST ort.R > 0 ve gün-blok P ≥ 0,90.
3. **Şans sayısı (E98):** aynı aramayı saat-içi özellik permütasyonuyla 30 kez tekrarla; aday sayısı boşun %95'ini geçmeli.
4. **Finalist:** iki-dönem adaylarından her (TF, aile) için KEŞİF t'si en yüksek 5'i (ve TEST R'si en yüksek 5'i, ayrıca işaretli)
   → BAĞIMSIZ-A ort.R ≥ 0 (ve TF ≥ 2h ise BAĞIMSIZ-B ≥ 0), TEST spread × 1,5 > 0, TEST tek pozisyon > 0,
   TEST'te aynı kuralın rastgele mum eşinden (aynı saat, aynı giriş/SL/TP/tutma, ATR stoplu sürümle) iyi.
5. Sınıf: **B** = finalist ölçütlerinin hepsi + 3 geçer · **C** = 2 + bağımsız dönemlerin biri · **X** aksi.
"En kârlı" tablo ayrıca verilir ama hangi satırın örneklem-içi olduğu açıkça yazılır; B olmadan canlı/gölge önerilmez.

---

# EK-2 — Fitil anatomisi 3. tur (2026-11-06; EK-1 aday listesi görüldü, finalist sonuçları GÖRÜLMEDEN yazıldı)

EK-1 adaylarının neredeyse tamamı AL yönlü, geniş stop + TP'siz uzun tutma idi (sürüklenme şüphesi). EK-2 yeni anatomi
tanımları ekler; hüküm EK-1 ile aynı ölçütler + **zorunlu fitilsiz eş** (aynı bağlam/giriş/çıkış, fitil şartı yok) ile verilir:
bir aile ancak fitilli sürüm fitilsiz eşini TEST ve BAĞIMSIZ-A'da geçerse "fitil kenarı" sayılır.

## Yeni olay tanımları (her biri üst/alt fitil aynası)
- **CIFT:** ardışık iki mumun ikisinde de aynı tarafta fitil (s ≥ 0,4, w ≥ 0,3); ikinci mum sinyal.
- **ZSK z:** fitil / son 20 mumun aynı taraf fitil ortalaması ≥ z, z ∈ {2, 3}; ayrıca s ≥ 0,4.
- **KAP:** üst fitilde kapanış aralığın alt üçte birinde (ayı pin), alt fitilde üst üçte birinde; s ≥ 0,4, w ≥ 0,3.
- **BUYU:** son 3 mumda aynı taraf fitil sırayla büyüyor + M ≥ 2 (fitil yönünde hareket) — "baskı geliyor".
- **GOVK:** son 3 mumun gövdesi sırayla küçülüyor + M ≥ 2 + sinyal mumunda s ≥ 0,3 — "hareket yavaşlıyor, fitil uzuyor".
- **KORKU:** alt fitil (s ≥ 0,4, w ≥ 0,3) ∧ önceki NY kapanışı VIX ≥ 18,4 (`ndx_gate_forge/data/macro_daily_patched.csv`, gün
  kapanmış olmalı). Ayna: üst fitil ∧ VIX < 14 ("coşku").

## Yeni girişler (RET)
- **STPkarsi:** sinyal mumunun karşı ucu (alt fitil için tepe) kırılınca ret yönünde gir, 240 dk geçerli — "yön tersine kırılıyor".
- **LTF5:** kapanıştan sonraki 120 dk içinde ilk 5m mumu ret yönünde kapanır VE kapanışı sinyal kapanışının ötesindeyse → sonraki 1m açılışı.
- EK-1 girişleri de (MKT0/15/30/60, LIM50, STPkap) her olayla koşulur.
SL/TP/tutma ızgarası EK-1 ile aynı. TF 30m/1h/2h/4h. Şans sayısı aynı permütasyonla (30).

---

# EK-3 — Çekiç / kayan yıldız geometri taraması (2026-11-06; çekiç bulgusu GÖRÜLDÜKTEN SONRA, açıkça post-hoc)
Olay: fitil payı ≥ 0,7, w ≥ 0,2 ATR, baskın fitil (ρ ≥ 1). TF {1h, 2h, 4h} × giriş {STPgovde, MKT0} × SL {u0, u0.1, u0.25} × TP {2, 3}R ×
tutma {8, 16} mum × yön {alt→AL, üst→SAT} = 144 kurgu. Üç bağımsız set: NDX 2016-06→2023-02 (1h), DAX 2019-01→2026-10 (1h, spread 1,2),
NDX 2024-01→2026-11 (1m Dukascopy). Ölçüt: **üç sette de mutlak ort.R > 0** ve en az ikisinde gün-blok P ≥ 0,90. Şans sayısı:
aynı ölçütü rastgele mumlar "olay" sayılarak 20 tekrar (aynı sayıda olay, aynı saat dağılımı değil, tüm mumlar). Sonra en iyi 3 kurguya
işlem başına eşli plasebo. Hüküm sınıfı en fazla **B−** (post-hoc seçim); canlı için 2. KURAL kartı + gölge.

---

# EK-4 — Çekicin bağlamla iyileştirilmesi (2026-11-06; çekiç kartı görüldükten sonra, EK-4 hücreleri görülmeden)
Olay: 1h çekiç (alt fitil ≥ %70, ≥ 0,2 ATR, alt ≥ üst). Bağlam (13): yok · M ≤ −1 · M ≤ −2 (düşüş sonrası) · M ≥ 1 (yükselişte
geri çekilme) · dip20 · EMA50 üstü · EMA50 altı · Asya (18–02 ET) · Londra (02–08:30) · NY sabah (08:30–11) · NY öğle (11–17) ·
VIX ≥ 18,4 · VIX < 18,4 · ATR14/ATR100 > 1,2 · < 0,8 (15 bağlam). Geometri: giriş {MKT0, MKT5} × SL {uç−0,1, uç−0,25 ATR} ×
TP {2, 3, 4, 5}R × tutma {8, 16, 24} = 48. Toplam 720 hücre.
**Seçim yalnız KEŞİF'te** (Dukascopy 2024-01→2025-06): R > 0, t ≥ 2, n ≥ 40. Doğrulama: TEST (2025-07→2026-11), NDX 2016-06→2023-02,
DAX 2019→2026-10, broker NAS100 2026. **Bağlamın katkısı** = aynı geometride bağlamlı ort. R − bağlamsız çekiç ort. R; boş dağılım:
çekiç olaylarından aynı büyüklükte rastgele alt küme (20 tekrar). Bir bağlam ancak dört doğrulama setinin en az üçünde katkı > 0 ve
boşun %90'ını geçerse "iyileştirme" sayılır. Sınıf en fazla B− (aynı veriye 4. bakış, E23).

---

# EK-5 — Çekiçte giriş yeri / zamanı / çıkış + başka piyasalar (2026-11-06; EK-4 görüldükten sonra, EK-5 hücreleri görülmeden)
Olay sabit: 1h çekiç (alt fitil ≥ %70, ≥ 0,2 ATR, alt ≥ üst), AL. Giriş (10): piyasa 0 / 5 dk · fitilin %25 / %50 / %75'ine
limit (60 dk geçerli) · %50 limit 240 dk · gövde üstü kırılımı · kapanış + 0,1 ATR kırılımı · mum tepesi kırılımı (240 dk) ·
5m teyit mumu (yalnız 1m setleri). SL: uç, uç − 0,1 / 0,25 / 0,5 ATR. TP: 2 / 3 / 4 / 5R, yapı (mum tepesi). Tutma 16 / 24 saat. = 400 hücre.
Setler: NDX Dukascopy KEŞİF (seçim) / TEST, NDX 2016-23, DAX 2019-26, broker NAS100 2026 (doğrulama); XAU ve USOIL 1h
2016-06 → 2026-10 (taşınma; XAU'da 2026-09-03 sonrası Yahoo dikişi hariç, spread 0,25 / 0,03).
Ölçüt: KEŞİF R > 0, t ≥ 2, n ≥ 40 → dört NDX doğrulama setinde R > 0 ve **taban çekice** (piyasa 0, uç − 0,1, TP 3R, 16 sa) göre
en az üçünde daha iyi. Taşınma bilgi amaçlı (hüküm NDX'te). Sınıf en fazla B−.

---

# EK-6 — Farklı stratejiler (2026-11-07; kullanıcı: "daha özel, daha detaylı, daha çok oynaklık, farklı stratejiler")
Önceki turların dersi: fitilin ret bilgisi evrensel (+0,08…+0,16R aynı kuralın tabanı üstü) ama dar stop + spread tabanı eksiye
çekiyor. EK-6 bilgiyi maliyetin küçük olduğu yerde veya açığa satmadan kullanır. **Veri:** günlük ETF'ler QQQ/SPY/DIA/IWM
(1999-2026, gerçek açılış) + ^GDAXI; maliyet gidiş-dönüş 2 bp (×2 duyarlılık). **KEŞİF = QQQ 2000-2014** (seçim yalnız burada);
**doğrulama = QQQ 2015-2026 + SPY/DIA/IWM/GDAXI 2000-2026 (kör)**.

**A — D1 çekiç / kayan yıldız.** Olay: fitil/aralık ≥ s ∈ {0,5 0,6 0,7}, fitil/ATR14 ≥ w ∈ {0,2 0,4}, baskın. Giriş: ertesi açılış ·
tepe (SAT'ta dip) kırılımı stop emri 1 / 3 gün geçerli · fitilin %50'sine limit (ertesi gün). SL: mum ucu − 0 / 0,1 ATR, 1 / 1,5 ATR.
TP 1 / 2 / 3 / 5R, yok. Tutma 1 / 3 / 5 / 10 gün. Günlük çözünürlük: aynı günde SL+TP → SL; dolum günü TP sayılmaz (açılış dolumu hariç).
Ölçüt: KEŞİF R > 0 ∧ t ≥ 2 → doğrulama 5 setin ≥ 4'ünde R > 0 ve havuz P ≥ 0,90; ayrıca aynı kuralın tüm günlerdeki tabanı ve şans
sayısı (rastgele gün "olay", 20 tekrar).
**B — Fitil çıkışı (açığa satmadan).** Taban strateji: kapanış > SMA50 ise ertesi açılışta uzun, değilse nakit. Varyant: kayan yıldız
(üst fitil/aralık ≥ 0,6 ∧ ≥ 0,4 ATR) gelince ertesi açılışta çık, k ∈ {3, 5, 10} gün ya da kapanış yıldızın tepesini aşana kadar
nakit kal. Ölçüt: Sharpe ve toplam getiri tabanı ≥ 4/5 sette ve iki dönemde geçmeli; zamanın yüzde kaçı nakit raporlanır.
**C — 1h çekiç + günlük bağlam** (NDX Dukascopy + NDX 2016-23 + DAX): FR-10 kuralı yalnız (i) dün D1 çekiç, (ii) fiyat dünkü dibin
altında süpürüp geri dönmüş (1h çekiç dibi < dünkü dip), (iii) D1 kapanış > SMA50. Bağlamsız FR-10'a göre katkı, EK-4 boşu ile.
Sınıf en fazla B (kör doğrulama geçerse).

---

# EK-7 — Kombo, öncesi/sonrası anatomi, portföy (2026-11-07; kullanıcı: "farklı taktiklerle birleştir, kombo yap, öncesine ve sonrasına bak")
Taban kural FR-10 (1h çekiç: alt fitil ≥ %70, ≥ 0,2 ATR, alt ≥ üst; 240 dk içinde tepe kırılımı AL; stop dip; TP 5R; 24 sa).
İkinci geometri: TP 3R / 16 sa. Setler: NDX Dukascopy KEŞİF/TEST, NDX 2016-23, DAX 2019-26, broker NAS100 2026.
**Kombo (gün düzeyi, bilinen bilgi, önceki gün kapanışıyla):** RSI2(D1) < 10 · RSI2 < 30 · VIX ≥ 18,4 · VIX ≥ 18,4 ∧ RSI2 < 30 ·
son 3 gün düşüş · gün açılışı önceki kapanışın ≥ 0,5 D1-ATR altında (boşluk) · önceki gün D1 kapanışı < SMA200 (ayı rejimi) ·
> SMA200 (boğa rejimi).
**Öncesi (1h):** çekiçten önceki ≥ 3 kırmızı mum · son 3 mumda art arda daha düşük dip · çekiçten önceki 6 mumun en büyük gövdesi
≥ 1 ATR (sert düşüş) · çekiç günün en düşük noktası (gün içi dip).
**Sonrası (giriş varyantı, 1h):** çekiçten sonraki ilk 1h mum çekicin tepesinin ÜSTÜNDE kapanırsa onun kapanışında AL (kapanış teyidi) ·
ilk sonraki mum içeride (inside) kalırsa, ondan sonraki tepe kırılımında AL · sonraki mum da alt fitilli (çift çekiç) ise AL.
Stop/TP/tutma taban kuralla aynı.
**Ölçüt (önceden):** katkı = komboluk ort. R − taban FR-10 ort. R (aynı set). Boş = aynı büyüklükte rastgele FR-10 alt kümesi (200).
"Kombo kazancı" = 5 setin ≥ 4'ünde katkı > 0 ve ≥ 3'ünde boşun %90'ı üstünde, n ≥ 20 her sette. Geçen varsa → kutuda MT5
NAS100/US500/US30/US2000/GER40 H1 2018-26 kör sınama; havuzda katkı > 0 olmalı.
**Portföy:** FR-10 + TR-C3 (RSI2 < 10 → 15:30 ET AL, ertesi 15:30 çık; Dukascopy NDX 2024-26'da yeniden kurulur) günlük P&L birleşimi:
korelasyon, birleşik Sharpe, maxDD; tek başlarına ile kıyas.

---

# EK-8 — Teyit ilkesinin genellenmesi (2026-11-07; FR-15 görüldükten sonra, EK-8 hücreleri görülmeden)
Teyit kuralı sabit: sinyal mumundan sonraki mum, sinyal mumunun ret yönündeki ucunun ötesinde kapanır (çekiçte tepe üstü, yıldızda dip altı)
ve karşı ucu kırmaz → sonraki mumun açılışında gir; stop sinyal mumunun ucu; TP 5R; 24 saat (TF'den bağımsız). Hücreler:
(a) teyitli kayan yıldız SAT (üst fitil ≥ %70, ≥ 0,2 ATR) 1h; (b) teyitli çekiç AL 30m / 2h / 4h; (c) teyitli çekiç AL 1h fitil ≥ %50 / %60.
Setler: yerel 5 (NDX Duka K/T, NDX 2016-23, DAX 2019-26, broker 2026) + kutu MT5 H1 5 endeks (30m hücresi kutuda M30 ile).
Ölçüt: 10 setin ≥ 8'inde ort. R > 0 ve MT5 havuz P ≥ 0,90. Sınıf en fazla B.
