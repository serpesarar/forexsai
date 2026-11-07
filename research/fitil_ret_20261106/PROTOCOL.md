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
