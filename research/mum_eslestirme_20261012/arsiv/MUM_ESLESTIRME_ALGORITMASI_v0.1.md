# Mum Eşleştirme Motoru ("Geçmiş Eşleşme Radarı") — Algoritma Tasarımı

> **Sürüm:** v0.1 · 2026-10-12 · **Durum:** TASARIM — kod yok, araştırma ön-kaydı öncesi.
> **Amaç:** Bu belge başka bir yapay zekâyla birlikte geliştirilecek; son hâli uygulamanın sözleşmesi olacak.
> **Kanıt klasörü:** `research/mum_eslestirme_20261012/` — bugünkü fizibilite ölçümleri (yalnız eşleşme SAYIMI; hiçbir
> betik gelecekteki fiyata bakmadı → ön-kayıt temiz).
> **Bağlı kurallar:** CLAUDE.md 1. (Evrim Paneli), 2. (canlıya alma kartı), 3. (kapı kayıt defteri) KURAL;
> `docs/KAPI_KAYIT_DEFTERI.md` satırları PM, PM-2, OLD-13, OLD-15, IO-18, MK-01..05, GF-01 ve tuzaklar E1–E25.

---

## 0. Tek sayfada özet

**İstek.** Bir tuşa basılınca sembolün son X kapanmış mumu, farklı zaman dilimlerinde, geçmiş 5 yıllık veride (yoksa
eldeki en eski veriye kadar) her mum küçük bir sapma payıyla (örn. %0,01–0,02) taransın; benzer geçmiş durumlardan sonra
fiyatın hangi yöne ve kaç pips gittiği ekrana basılsın. X her sembol için araştırmayla, "yönün en tahmin edilebilir
olduğu" değere ayarlansın. Veriler yerel bilgisayarda hazır olsun.

**Tasarımı belirleyen dört olgu (üçü bugün ölçüldü):**

1. **Matematiksel tavan.** Mum-mum birebir eşleşmede beklenen eşleşme sayısı ≈ N·p₁^X (p₁ = tek bir mumun rastgele bir
   mumla pay içinde eşleşme olasılığı). Buradan **X_max ≈ ln(N / n_min) / ln(1 / p₁)**. 5 yıllık veride ≥30 bağımsız
   eşleşme için: kullanıcının %0,01–0,02 payıyla **X = 0–2 mum** (çoğu hücrede 1), anlamlı en gevşek payla bile
   **≤ 3 mum**. Veriyi 10 katına çıkarmak X'i yalnız ~0,8 mum artırır. Örnek: NDX 15m, %0,02 → 1 mumluk ikiz 1.052,
   2 mumluk 18, **3 mumluk 0** (3 yıllık kütüphane, sorgu medyanı). "10–20 mumu mum mum eşleştir" bu yüzden fiziksel olarak mümkün değil; uzun yapı için başka temsil şart.
2. **Sabit % pay semboller ve zaman dilimleri arasında adil değil.** %0,02 = NDX 5m medyan mumun %29'u, OIL 1h'in %3,8'i;
   tek mum eşleşme olasılığı OIL 1h'te %0,01, NDX 5m'de %6,2 (600 kat fark). ATR-birimli pay (örn. 0,2 ATR) bu
   olasılığı her yerde %3–6'ya eşitliyor → **içeride ATR birimi, ekranda % ve pips karşılığı.**
3. **Logaritmik zaman piramidi çalışıyor.** Son 33 mumu 7 "süper mumla" (son 3 tam, öncekiler 2-4-8-16'lık birleşik)
   kodlamak, en yakın komşu kalitesini ham 7 mumluk pencere düzeyinde tutuyor (göreli kontrast 2,3–2,6); ham 33 mum
   1,5'e, yani rastgeleye yakın düzeye düşüyor → **ana motor: piramit-kNN.**
4. **Önceki kanıt yön için olumsuz.** NAS100 mum dizisi atlasında (PM) tekrarlar plasebo düzeyinde, tekrar sonrası yön
   tabandan ayrışmıyor; analog-kNN (OLD-13) ve benzer-işlem kNN'i (IO-18) yön vermedi; klasik formasyonlar (MK-01..05)
   elendi → **yön çıktısı ancak araştırmada doğrulanırsa "kenar" diye sunulur, varsayılan "bilgi amaçlı".**
   Büyüklük/oynaklık ("kaç pips oynar", MFE/MAE) bu projede hiç ölçülmedi ve oynaklık kümelenmesi nedeniyle gerçek bilgi
   taşıması muhtemel → ayrı hedef olarak ölçülür.

**Önerilen yapı.** Tek beslemeli, UTC, temiz parquet kütüphanesi → eşleştirme motorları (**A "İkiz"**: kullanıcı tanımı,
X ≤ 3, birebir pay · **B "Piramit-kNN"**: 9/17/33/65 mumluk bağlam · **AB "Hibrit"**: son 1–2 mum birebir + öncesi
piramitle sıralama · opsiyonel **C "Çizgi"**) → ATR birimli sonuç etiketleri (net getiri, MFE/MAE, ±k·ATR yarışı, yol
konisi) → taban oranına çekilmiş olasılık + kantil dağılımı + sorgu-başına plasebo → **dürüstlük katmanı** (etkin n,
taban, fark, plasebo p, doğrulanmış/doğrulanmamış rozeti) → API + panel (koni grafiği, eşleşme listesi) → gölge kaydı.

**"Her sembole özel mum sayısı"** = ön-kayıtlı, yürüyen-ileri araştırmanın çıktısı: sembol × TF × mum sayısı (derinlik)
× ufuk için **tahmin edilebilirlik haritası**; seçim yükü maks-istatistik plasebosuyla düzeltilir; sonuç
`backend/data/candle_match/profiles.json`.

---

## 1. Problem tanımı

| Öğe | Tanım |
|---|---|
| Sembol | NDX (MT5 `NAS100`), DAX (`GER40`), XAUUSD, USOIL (`SpotCrude`) |
| Zaman dilimi (TF) | 5m · 15m · 30m · 1h · 4h · 1d (1m opsiyonel, §5.1) |
| Karar anı t | Tuşa basıldığı an |
| Sorgu | t'den önceki **son kapanmış** mum e_q ve öncesi. Koşan (oluşmakta olan) mum ASLA kullanılmaz |
| Kütüphane 𝓛 | Aynı besleme, aynı TF, [t − 5 yıl, t) aralığındaki tüm kapanmış mumlar (5 yıl yoksa mevcut en eski) |
| Eşleşme | Kütüphanede biten bir pencere j; motor-bağımlı benzerlik D(q, j) eşiği/sıralamayı geçer; j'nin sonuç penceresi (j+1 … j+H) t'den önce tamamen bitmiş olmalı |
| Ufuk H | Sonucun ölçüldüğü bar sayısı (TF başına ön-kayıtlı 3 değer, §8) |
| Pips | Proje sabitleri (`meta_analysis_engine`): NDX 1,0 · DAX 1,0 · XAU 0,1 · OIL 0,01 |

**Çıktı (her TF için):**
- **Yön:** P(H bar sonra fiyat > şimdiki) — mutlaka **taban oranı p₀** ve **fark (lift)** ile.
- **Büyüklük:** H sonunda net hareketin dağılımı (pips; P10/P25/P50/P75/P90), en olumlu gidiş (MFE), en olumsuz gidiş
  (MAE), yönsüz oynaklık beklentisi.
- **Yol:** adım adım kantil konisi (grafiğe çizilir).
- **Güven:** etkin bağımsız eşleşme sayısı, farklı gün sayısı, benzerlik, nadirlik, plasebo p-değeri, araştırma rozeti.

---

## 2. Önceki kanıt (3. KURAL — defter taraması)

| ID | Ne denendi | Sonuç | Bu tasarıma etkisi |
|---|---|---|---|
| **PM** | NAS100 mum dizisi atlası: 3–100 mum, mum-mum %0,005–0,20, 4 TF, birebir + %90/80/70 kısmi | gerçek/plasebo medyan 1,0; en uzun birebir tekrar 9 mum; sonraki 10 mum yönü taban ±2 puan; çoklu test sonrası 0 | Uzun birebir dizi = tesadüf geometrisi; **her sayı plaseboyla verilmeli** |
| **PM-2** | Aynı modeller ATR TP/SL işlemi olarak | sınama −0,062R (143k işlem); "en iyi 20" plasebo sınırında, "en iyi 50" geçmiyor | "En iyi X'i seç" aynı seçim tuzağına düşer (E23/E24) |
| **OLD-13** | CORTEX analog-kNN (günlük durum vektörü) | yön yok (Q4−Q1 ≤ 0; holdout −11 puan) | kNN tek başına yön vermez |
| **OLD-14** | Aynı hedefte denetimli ML + çoklu-TF teknik çakışma | gerçek ama rejime bağlı (AUC 0,60; 2022'de çöktü) | Bilgi, rejimle kesişince çıkıyor → bağlam vektörü |
| **IO-18** | Benzer-işlem kNN (bot işlemleri) | sonuç tekrarlamıyor (AUC 0,46–0,50) | aynı |
| **MK-01..05** | Klasik mum formasyonları, 4 sembol | elendi; tek ayakta XAU "yeni tepe BUY" (gölge, B−) | Şekil değil mekanizma (momentum/dönüş) taşıyor |
| **OLD-15** | NDX 5/60 dk yön tahmini | taban düzeyi (ilk %70 sızıntıydı) | Kısa ufukta yön ≈ yazı-tura |
| **GF-01** | 780 tek-özellik hücresi + plasebo | plasebo düzeyi | Meta-ders 1: rastgele girişte durum kapısı yok |

**Neden yeniden açılabilir** (defter §0.1: *yeni tanım, yeni veri veya yeni gerekçe* şartı):
1. *Yeni tanım* — "en sık tekrar eden motif" değil, **o anki yapıya koşullu** tahmin (sorgu-merkezli komşu arama).
2. *Yeni hedef* — **büyüklük/oynaklık** (kaç pips oynar, MFE/MAE, menzil). Hiç ölçülmedi.
3. *Yeni veri* — DAX/XAU/OIL (PM yalnız NDX'ti); 30m/1h/4h/1d'de 5–10 yıl.
4. *Yeni temsil* — ATR-normalize mum + log-zaman piramidi (PM'de % pay ve ham dizi vardı).
5. *Yeni gerekçe* — kanıtlı mekanizmalarla bağlam koşulu (VIX rejimi, stres, "korku döner coşku dönmez").

**Yazılı ön-beklenti** (sonuçlar gelince "sürpriz mi?" diye kıyaslanacak): yönde Brier becerisi ≈ 0 ve fark ±2 puan
içinde; büyüklükte "yalnız ATR + saat" tabanını küçük ama pozitif farkla geçmesi olası.

---

## 3. Fizibilite ölçümü (2026-10-12; sonuçlara bakılmadan)

**Yöntem.** Her sembol × TF için son 1 yıldan rastgele 120–150 sorgu anı; kütüphane = mevcut 5 yıl. Mum özellikleri
kullanıcı tanımıyla aynı: tepe, dip, kapanış — mumun kendi açılışına göre (% veya ATR14 birimi). Öz-eşleşme ve kendi
kaydırmaları hariç, çakışmasız sayım. Betikler ve ham sonuçlar: `research/mum_eslestirme_20261012/`.

### 3.1 Kullanıcı payının gerçek karşılığı

| Sembol | TF | kütüphane (bar) | medyan mum | %0,01 = | %0,02 = | %0,02 ÷ medyan mum | p₁ @%0,02 | p₁ @0,2 ATR |
|---|---|---|---|---|---|---|---|---|
| NDX | 5m | 106.809 (21 ay) | %0,069 · 17 p | 3,1 p | 6,1 p | %29 | %6,24 | %5,41 |
| NDX | 15m | 70.863 (3 y) | %0,108 · 24 p | 3,1 p | 6,1 p | %18 | %1,49 | %4,58 |
| NDX | 30m | 59.019 (5 y) | %0,170 · 30 p | 3,0 p | 5,9 p | %12 | %1,14 | %5,03 |
| NDX | 1h | 29.579 (5 y) | %0,250 · 44 p | 3,0 p | 5,9 p | %8 | %0,20 | %3,83 |
| DAX | 15m | 83.915 (3,9 y) | %0,100 · 19 p | 2,5 p | 5,0 p | %20 | %1,61 | %4,74 |
| DAX | 30m | 55.353 (5 y) | %0,156 · 29 p | 2,5 p | 5,0 p | %13 | %0,62 | %5,59 |
| DAX | 1h | 27.728 (5 y) | %0,225 · 41 p | 2,5 p | 5,0 p | %9 | %0,24 | %4,55 |
| XAU | 5m | 87.320 (15 ay) | %0,093 · 40 p | 4,4 p | 8,8 p | %22 | %2,76 | %6,09 |
| XAU | 15m | 82.464 (3,5 y) | %0,118 · 33 p | 4,4 p | 8,8 p | %17 | %0,47 | %4,61 |
| XAU | 30m | 59.152 (5 y) | %0,159 · 37 p | 4,4 p | 8,8 p | %13 | %0,12 | %4,42 |
| XAU | 1h | 29.599 (5 y) | %0,229 · 54 p | 4,4 p | 8,8 p | %9 | %0,05 | %4,58 |
| OIL | 5m | 87.322 (15 ay) | %0,154 · 11 p | 0,9 p | 1,8 p | %13 | %1,03 | %5,32 |
| OIL | 15m | 82.464 (3,5 y) | %0,224 · 16 p | 0,9 p | 1,8 p | %9 | %0,14 | %4,06 |
| OIL | 30m | 59.127 (5 y) | %0,356 · 27 p | 0,9 p | 1,8 p | %6 | %0,05 | %4,94 |
| OIL | 1h | 29.592 (5 y) | %0,520 · 40 p | 0,9 p | 1,8 p | %4 | %0,01 | %3,06 |

p = pips. Pips karşılıkları her dosyanın son fiyatından (NDX ≈ 30.670; NDX 30m/1h dosyaları 07-14'te bittiği için
≈ 29.680 · DAX ≈ 25.070 · XAU ≈ 4.385 · OIL ≈ 91). XAU/OIL 5m'nin medyan
pips'i 15m'den büyük görünüyor çünkü 5m yalnız son 15 ayı (yüksek fiyat dönemi) kapsıyor.

### 3.2 ≥30 bağımsız eşleşme veren en uzun mum dizisi (X_max, sorgu medyanı)

| Sembol | TF | %0,01 | %0,02 | %0,05 | 0,1 ATR | 0,2 ATR | 0,3 ATR | huni¹ | kısmi %80² |
|---|---|---|---|---|---|---|---|---|---|
| NDX | 5m | 1 | 2 | 8³ | 1 | 2 | 3 | 2 | 2 |
| NDX | 15m | 1 | 1 | 4³ | 1 | 2 | 3 | 2 | 2 |
| NDX | 30m | 1 | 1 | 3 | 1 | 2 | 3 | 2 | 2 |
| NDX | 1h | 0 | 1 | 1 | 1 | 2 | 3 | 0 | 2 |
| DAX | 15m | 1 | 1 | 3³ | 1 | 2 | 3 | 2 | 2 |
| DAX | 30m | 1 | 1 | 2 | 1 | 2 | 3 | 2 | 2 |
| DAX | 1h | 0 | 1 | 1 | 1 | 2 | 2 | 0 | 2 |
| XAU | 5m | 1 | 2 | 4³ | 1 | 2 | 3 | 2 | 2 |
| XAU | 15m | 1 | 1 | 2³ | 1 | 2 | 3 | 2 | 2 |
| XAU | 30m | 0 | 1 | 1 | 1 | 2 | 3 | 2 | 2 |
| XAU | 1h | 0 | 0 | 1 | 1 | 2 | 2 | 0 | 2 |
| OIL | 5m | 1 | 1 | 3 | 1 | 2 | 3 | 2 | 2 |
| OIL | 15m | 0 | 1 | 1 | 1 | 2 | 3 | 2 | 2 |
| OIL | 30m | 0 | 1 | 1 | 1 | 2 | 3 | 2 | 2 |
| OIL | 1h | 0 | 0 | 1 | 1 | 1 | 2 | 0 | 0 |

¹ huni: son mum ≤ 0,15 ATR, her geri adımda +0,05 ATR · ² son 2 mum ≤ 0,2 ATR şart + mumların ≥ %80'i ≤ 0,2 ATR ·
³ bu hücrelerde pay medyan mumun %43–73'ü → "her mum her mumla eşleşir"; PM'nin uygunluk kuralını
(pay ≤ medyan mum / 3) çiğniyor, sayı anlamsız.

**Formül sınaması:** 0,2 ATR'de formülün öngördüğü X_max 15 hücrenin hepsinde 2,0–2,9; gözlenen 2 (OIL 1h'te 1).
Uzantılar (p₁ ≈ %5, yani 0,2 ATR varsayımıyla): 4h (5 yıl ≈ 7.500 bar) → X_max ≈ 1,8; 1d (5 yıl ≈ 1.300 bar) → ≈ 1,3;
5 yıllık 1m (≈ 1,75 milyon bar) → ≈ 3,7. Veri 10 katına çıkınca X_max yalnız ln 10 / ln(1/p₁) ≈ 0,8 artar.

### 3.3 Uzun bağlam: kNN ve piramit

**Göreli kontrast (RC)** = sorgunun tüm kütüphaneye medyan mesafesi ÷ 30. en yakın komşunun mesafesi. RC → 1 ise "en
yakın" komşular rastgele seçilmiş pencerelerden ayırt edilemez (boyut laneti).

| Ham pencere (mum sayısı) | 3 | 5 | 8 | 12 | 20 | 30 |
|---|---|---|---|---|---|---|
| RC, 15 hücre aralığı | 3,5–4,6 | 2,4–3,2 | 2,1–2,4 | 1,9–2,2 | 1,6–1,8 | 1,5–1,6 |

| Hücre | **Piramit, 33 mum (21 boyut)** | Ham 33 mum (99 boyut) | Ham 7 mum (21 boyut) |
|---|---|---|---|
| NDX 15m | **2,57** | 1,50 | 2,50 |
| NDX 1h | **2,31** | 1,50 | 2,28 |
| DAX 30m | **2,45** | 1,50 | 2,41 |
| XAU 30m | **2,49** | 1,47 | 2,51 |
| OIL 15m | **2,60** | 1,51 | 2,51 |

Piramit uzayında birebir kutu payı da çalışmıyor (0,5 ATR'de bile medyan 1,5–15 eşleşme) → piramit **sıralama (kNN)**
ile kullanılır, kutu payıyla değil.

### 3.4 Tasarım kararlarına çevirisi

1. Kullanıcı tanımı (mum-mum pay) korunur ama yalnız **X ≤ 3** ile ("İkiz" motoru); ekran kaç ikiz bulunduğunu dürüstçe
   yazar ("5 yılda 0 ikiz" dahil).
2. Pay içeride **ATR biriminde**; ekranda % ve pips karşılığı.
3. Uzun bağlam = **piramit-kNN**; kullanıcıya söylenen "mum sayısı" = piramit derinliği (9/17/33/65).
4. Son 1–2 mumun birebirliği isteniyorsa **Hibrit**: önce İkiz süzgeci, sonra piramitle sıralama.
5. n her zaman **etkin bağımsız** sayı olarak raporlanır.

---

## 4. Mimari genel bakış

```
┌──────────────────────────── ÇEVRİMDIŞI ────────────────────────────┐
│ MT5 (kutu) ─► data_recorder ─► indicator_snapshots (broker gerçeği)  │
│ Derin geçmiş: mevcut research parquet'leri + MT5 export (+Dukascopy) │
│        │                                                             │
│        ▼                                                             │
│ [§5] Kütüphane kurucu ─► data/candle_match/<SYM>/<tf>.parquet        │
│                          + manifest.json (kaynak, aralık, sha1)       │
│        ▼                                                             │
│ [§6, §8] Özellik + sonuç ön-hesabı (ATR birimli, nedensel)           │
│        ▼                                                             │
│ [§11] Sembol araştırması: ön-kayıt → yürüyen-ileri → plasebo → TEST  │
│        └─► backend/data/candle_match/profiles.json + rapor + defter  │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────────── ÇEVRİMİÇİ (tuş) ───────────────────────┐
│ "Mum Eşleştir" ─► GET /api/candle-match/{symbol}                     │
│   → kütüphaneye son kapanmış broker mumlarını ekle (aynı besleme)    │
│   → her TF için sorgu vektörü (İkiz / piramit / bağlam)              │
│   → RAM'deki kütüphanede arama (numpy, < 50 ms/TF)                   │
│   → komşu sonuçları → birleştirme (büzülme, kantiller, plasebo)      │
│   → dürüstlük katmanı (profil rozeti) → JSON → panel (koni + liste)  │
│   → gölge kaydı → H bar sonra notlanır (canlı karne)                 │
└──────────────────────────────────────────────────────────────────────┘
```

**Sadakat ilkesi:** araştırma betiği ve canlı servis **aynı çekirdek modülü** çağırır (fakeout dedektöründeki "deploy
edilen artefakt test edilenin ta kendisi" ilkesi). Ayrı yeniden yazım yok.

---

## 5. Veri katmanı

### 5.1 Yerel veri envanteri (2026-10-12, yıllık bar sayısıyla doğrulandı)

| Sembol | 1m | 5m | 15m | 30m | 1h | Not |
|---|---|---|---|---|---|---|
| NDX | 2025-01→2026-10 (21 ay; Dukascopy 2025 + Pepperstone 2026) | 1m'den, 21 ay | 2023-10→2026-10 | 2021-06→2026-07 | **2016-05→2026-07 (10 y)** | 30m/1h dosyaları 07-14'te bitiyor → bugüne uzatılmalı; 1m'de 2025-08-22→27 ve 2026-01-01→02-10 boşluk |
| DAX | yok (14 günlük paketler) | yok | 2022-11→2026-10 | 2021-03→2026-10 | 2020-01→2026-10 (~6,8 y) | `dax_1h` 1999'dan başlıyor görünür ama 2019'a kadar seyrek (2012: 254 bar/yıl) → **2020 öncesi kullanılmaz** |
| XAU | yok | 2025-06→2026-09 | 2023-03→2026-09 | 2021-07→2026-09 | **2016-05→2026-09 (10 y)** | 2026-09-03 sonrası Yahoo GC=F (E21) → broker'dan doldurulmalı |
| OIL | yok | 2025-06→2026-09 | 2023-03→2026-09 | 2021-07→2026-09 | **2016-05→2026-09 (10 y)** | Aynı + vade devri riski (§5.4) |

Kaynak klasörleri: `research/ndx_pattern_motifs/data`, `research/ndx_gate_forge/data`, `research/pinbar_20261010/data`.
4h ve 1d, 1h'ten türetilir (§5.3). Saat ekseni testi (yaz dönemi en oynak saat): NDX 14/13 UTC, XAU 13/14 UTC, OIL
13/14/15 UTC → yerel dosyalar UTC ile tutarlı (`pinbar_20261010/pull_other.py` docstring'indeki "07-15 öncesi broker
saati" notu bu dosyalarda doğrulanmadı; Faz 0'da her TF × dönem için otomatik testle kesinleştirilir).

**Derinlik sınırları:** MT5/candle_cache TF başına ~60–100 bin bar sınırında: 1h ≈ 10 y, 30m ≈ 5 y, 15m ≈ 3,5 y,
5m ≈ 15–21 ay, 1m ≈ 68–100 gün. 5 yıllık 5m/1m için dış kaynak gerekir: Dukascopy (2026-10-02'de bu ağdan erişilemedi
— yeniden denenmeli) veya kutuda MT5 "Grafikteki en fazla bar = Sınırsız" + parçalı `copy_rates_range` denemesi. Bu
sağlanana kadar 5m profilleri "kütüphane 15–21 ay" rozetiyle çalışır; 1m ilk sürümde kapalı.

### 5.2 Tek besleme kuralı (en kritik veri ilkesi)

Sorgu mumları ile kütüphane mumları **aynı fiyat kaynağından, aynı saat ekseniyle, aynı mum sınırlarıyla** gelmeli.
Pay 0,15–0,3 ATR mertebesinde; besleme farkı (USOIL broker ↔ Yahoo CL=F 0,1–4,7 $, XAU −32…−46 $ — E21) bu payı tek
başına aşar ve eşleşmeyi gürültüye çevirir.
- Kütüphane = broker (Pepperstone MT5) mumları.
- Canlı sorgu = aynı kütüphane dosyasına artımlı eklenen son kapanmış broker mumları (`indicator_snapshots` ← kutudaki
  `data_recorder`). **DataHub'ın Yahoo-hibrit beslemesi KULLANILMAZ.**
- Her satır `src` etiketi taşır; sorgu penceresinde farklı `src` varsa → uyarı + sonuç "veri tutarsız" bayraklı.

### 5.3 Saat ekseni ve mum sınırları

- Tümü UTC, bar BAŞLANGICI damgalı. MT5 `time` = sunucu saati (UTC+2/+3) → ölçülen offset çıkarılır (E2/E3/E5).
- Otomatik test (her kurulum ve her güncellemede): 1m/5m'de günün en büyük ortalama aralık saati NDX/DAX için ABD nakit
  açılışı (13:30 yaz / 14:30 kış UTC), DAX'ta ek olarak 07:00 UTC (Xetra açılışı). Tutmazsa kurulum DURUR.
- **4h ve 1d mumları broker sunucu saatine hizalı türetilir** (kullanıcının MT5'te gördüğü mumlarla aynı olsun diye):
  D1 sınırı = sunucu gece yarısı = NY 17:00; H4 sınırları sunucu 00/04/08/12/16/20. UTC'ye hizalı 4h, ekrandaki 4h ile
  aynı mum değildir.
- Seans kovaları DST-doğru `services/session_context_service.py`'den alınır (borsa yerel saatiyle tanımlı).
- Ekranda UTC + MT5 sunucu saati birlikte gösterilir (kullanıcı şablon tarihlerini MT5 saatinde verir).

### 5.4 Temizlik

- Saniye ≠ 0 tick kirliliği, kovaya hizasız dakikalar, NY 17:00–18:00 kopya barları (candle_cache 15m), hafta sonu
  barları, çift barlar (son yazan kazanır), H < L veya ≤ 0 fiyatlar atılır (`ndx_pattern_motifs/build_bars.py` mantığı).
- **Segment:** > 4 gün boşluk = yeni segment; hiçbir pencere veya sonuç ufku segment sınırını aşmaz.
- Günlük 1 saatlik ara pencere içinde olabilir (yapının parçası) ama `gap` özelliğiyle işaretlenir.
- **OIL vade devri:** devir günlerinde açılış boşluğu > 3 × ATR olan bar `roll` bayrağı alır; pencere/ufuk bu bayrağı
  geçemez. CFD sağlayıcısının devirde fiyat ayarlaması yapıp yapmadığı bilinmiyor → Faz 0'da veriyle tespit edilir.
- **Hacim** hiçbir özelliğe girmez (DAX tick hacmi sentetik; IO-03'te hacim SL/TP ayırmadı).
- NDX 1m 2026-02-10→03-08 arası +60 dk düzeltilir (E4).

### 5.5 Depolama ve güncelleme

- `data/candle_match/<SYM>/<tf>.parquet` (git dışı; `*.parquet` zaten ignore'da). Kolonlar:
  `ts, open, high, low, close, spread?, src, seg, flags(gap|roll)`.
- `data/candle_match/manifest.json`: kaynak, aralık, uygulanan offset, satır sayısı, sha1, kurulum zamanı.
- Kurucu: `scripts/candle_match/build_library.py --symbol ALL` — mevcut research parquet'leri + Supabase broker verisi
  birleştirilir, temizlenir, saat testi koşar.
- Artımlı güncelleyici: backend açılışında + 5 dk'da bir `indicator_snapshots`'tan yeni kapanmış barlar; üst TF'ler
  kova-hizalı yeniden örnekleme (DataHub'daki bucket-aligned mantıkla aynı).
- Bellek: 5 yıllık 5m ≈ 350 bin bar ≈ 8 MB; 1m dahil sembol başına ≈ 50 MB → tamamı RAM'de.
- Railway'e taşınırsa kütüphane bir volume'a konmalı; ilk sürüm yerel (kullanıcı isteği).

---

## 6. Mum temsili (özellik uzayı)

### 6.1 Temel mum vektörü

Pencere sonu e için ölçek A_e = **ATR14, pencerenin son mumundan önceki 14 mum** (nedensel; son mum kendini
normalize etmesin). Penceredeki her mum i için:

```
u_i = (H_i − O_i) / A_e      üst uç
d_i = (L_i − O_i) / A_e      alt uç (≤ 0)
b_i = (C_i − O_i) / A_e      gövde (işaretli)
g_i = (O_i − C_{i−1}) / A_e  boşluk (opsiyonel; seans aralarında anlamlı)
```

- Penceredeki tüm mumlar **aynı** A_e ile ölçeklenir → mumların birbirine oranı korunur ("büyük mum + üç küçük mum"
  şekli bozulmaz).
- Kullanıcı tanımıyla ilişki: (u, d, b) = PM'deki "tepe/dip/kapanış, açılışa göre" üçlüsünün ATR'ye bölünmüş hâli.
  % moda dönüş: pay_% = τ · A_e / fiyat · 100.
- Neden ATR: (i) semboller/TF'ler arası eşit katılık (§3.1), (ii) rejimler arası şekil karşılaştırması (2022 yüksek
  oynaklık ↔ 2025 sakin), (iii) fiyat seviyesinden bağımsızlık (NDX 15.000 ↔ 30.000). Kaybedilen mutlak oynaklık
  bilgisi bağlam vektörüne geri eklenir (§6.3).

### 6.2 Logaritmik zaman piramidi (Motor B'nin temsili)

Seviye boyutları, en yeniden eskiye:

| Derinlik | Seviyeler | Kapsadığı mum | Boyut |
|---|---|---|---|
| D9 | 1, 1, 1, 2, 4 | 9 | 15 |
| D17 | 1, 1, 1, 2, 4, 8 | 17 | 18 |
| D33 | 1, 1, 1, 2, 4, 8, 16 | 33 | 21 |
| D65 | 1, 1, 1, 2, 4, 8, 16, 32 | 65 | 24 |

Seviye ℓ (boyut s, sondan gecikme a) birleşik mumu: O = açılış[e−a−s+1], H = max(tepe), L = min(dip),
C = kapanış[e−a]. Özellik: (u, d, b)_ℓ / √s. √s, birleşik mum aralığının ~√zaman büyümesini dengeler → her seviye
mesafeye yaklaşık eşit katkı yapar; bar başına ağırlık son mumda 1, 16'lık seviyede ~1/16 → **doğal yakınlık ağırlığı**
("en son mumlar en önemli" sezgisi). Kullanıcıya söylenen "mum sayısı" = kapsadığı mum (9/17/33/65).

### 6.3 Bağlam vektörü (ön-kayıtlı ayrı varyant)

Yalnız mekanizması kanıtlı/yarı-kanıtlı küçük set:

| Özellik | Tanım | Gerekçe |
|---|---|---|
| `vol_z` | log(A_e / medyan A, son 1 yıl, aynı TF) | Oynaklık rejimi — ATR normalizasyonunun kaybettiği bilgi |
| `loc` | (C_e − min L₁₀₀) / (max H₁₀₀ − min L₁₀₀) | Aralıktaki konum; OIL dönüş / XAU momentum (MK-03/04) |
| `trend` | (C_e − EMA50_e) / A_e, ±5'te kırpılmış | Kovalama / aşırılık (GF-15, IO-18) |
| `seans` | seans kovası (sert süzgeç) veya saatin sin/cos kodu | Mum boyu ve davranış seansa bağlı (PM: uzun tekrarlar Asya'da) |
| `htf` | son **kapanmış** üst-TF mumunun (u, d, b)'si (örn. 15m sorguda son 4h) | E16: yalnız kapanmış üst-TF barı |
| `vix_reg` (NDX/DAX) | önceki günün **tamamlanmış** VIX kapanışı ≥ 18,4 (E20) | OLD-10 / K1 (A sınıfı) |
| `stres` (NDX/DAX) | dün ≤ −%1,5 veya 5 günde ≤ −%4 | GF-10/16 CAPREV (B+) |

Mesafe: `D² = Σ_ℓ Σ_f (P_qℓf − P_jℓf)² + λ · Σ_m ((c_qm − c_jm) / σ_m)²`, λ ∈ {0, 1} ön-kayıtlı (0 = yalnız şekil).
**Uyarı:** bağlam açıkken kenar çıkarsa kıyas **"yalnız bağlam" modeli** olmalı — şekil bir şey katıyor mu?

### 6.4 Sembolik kodlama (Motor 0 — taban)

Her mum → 9 sembol (yön 3 × gövde/ATR tertili 3); son 2–3 sembolün n-gram'ından koşullu yukarı oranı. Basit Markov
tabanı: piramit-kNN bunu geçemiyorsa karmaşıklığa gerek yoktur.

---

## 7. Eşleştirme motorları

### 7.1 Motor A — "İkiz" (kullanıcı tanımı, birebir pay)

- Koşul: ∀k ∈ [0, X−1], ∀f ∈ {u, d, b}: |f(q, e_q−k) − f(j, e_j−k)| ≤ τ.
- X ∈ {1, 2, 3} (fizibilite tavanı); τ ∈ {0,10 · 0,15 · 0,20 · 0,25} ATR (TF'ye göre kullanıcının ≈ %0,01–0,05'i).
- **Kullanıcı modu:** "benim payım %0,02" → % uzayında birebir arama; "5 yılda 0 ikiz" çıkabilir, dürüstçe gösterilir.
  Manuel ayar her zaman ⚪ "bilgi amaçlı" rozeti alır (araştırmada doğrulanan ayar değil).
- **Uygunluk kuralı** (PM): τ ≤ sorgu mumlarının medyan aralığı / 3; aksi hâlde küçük mumlar her şeyle eşleşir →
  τ otomatik daraltılır ve not düşülür.
- Hesap: kaydırılmış boolean VE, O(N·X) ≈ 1 ms.
- En anlamlı olduğu yer: karakteristik son mumlar (örn. ABD açılışında 2 ATR'lik mum) — "parmak izi" güçlüyken.

### 7.2 Motor B — "Piramit-kNN" (ana motor)

1. Sorgu piramidi P_q (derinlik profilden).
2. Tüm kütüphane pencereleri için D(q, j): kaba kuvvet, float32, ‖a−b‖² = ‖a‖² + ‖b‖² − 2a·b (BLAS);
   N = 350 bin × 21 boyut → < 10 ms. İndeks yapısı gereksiz.
3. Dışlamalar: (a) j + H ≥ t (sonucu bilinmeyen), (b) |j − e_q| < kapsam (öz-çakışma), (c) segment/devir geçen
   pencereler, (d) araştırmada ek olarak j + H > t − embargo.
4. **Tekilleştirme:** mesafe sırasıyla açgözlü; seçilen komşular arası en az max(H, kapsam/2) bar → aynı tarihsel olay
   beş kez sayılmaz (E6/E9).
5. K ∈ {50, 150} (ön-kayıtlı); çekirdek ağırlık w_j = exp(−½ (D_j / h)²), h = K komşunun medyan mesafesi.
6. Kalite ölçüleri: RC_q (§3.3); **benzerlik %** = 100 · (1 − D_j / D_rastgele-çift-medyanı), [0, 100]'e kırpılmış;
   **nadirlik** = sorgunun 1. komşu mesafesinin, rastgele geçmiş sorguların 1. komşu mesafeleri içindeki yüzdeliği
   (yüksek → "bu yapı tarihte nadir, sonuç zayıf"; çoğu zaman haber/olay anlarına denk gelir — kendi başına bilgi).

### 7.3 Motor AB — "Hibrit" (kullanıcı tanımı + uzun bağlam)

İkiz süzgeci (X_f ∈ {1, 2}, τ = 0,2 ATR) → kalan adaylar piramit mesafesiyle sıralanır → en yakın K = min(50, aday).
Fizibilite (0,2 ATR): X_f = 2 aday havuzu medyan 80–215 (5m–30m), 25–37 (1h); X_f = 1 havuzu 900–5.800.
Kural: aday < 30 ise saf B'ye düşülür ve bayrak konur. Böylece "son iki mum senin payınla birebir, önceki 31 mum benzer"
denebilir.

### 7.4 Motor C — "Çizgi" (opsiyonel, tamamlayıcı)

Kapanış yolunun z-normalize şekli (MASS / matrix profile, `stumpy`), genlik oranı 0,5–2× kısıtıyla. PM'de çizgi
benzerliği de plasebo düzeyindeydi → ayrı sekmede gösterilir, birleştirmeye girmez.

### 7.5 Bilerek dışarıda bırakılanlar (ilk sürüm)

- **DTW:** zaman esnetme = daha fazla serbestlik = daha fazla sahte benzerlik; Faz 3 deneyi.
- **Öğrenilmiş gömme** (autoencoder / contrastive): güçlü olabilir ama aşırı uyum ve açıklanabilirlik riski; A/B
  tabanları kurulmadan denenmez.
- **Hacim:** §5.4.

### 7.6 Çoklu zaman dilimi

- Her TF bağımsız koşar ve yan yana gösterilir.
- TF'ler bağımsız değildir (1h yapısı 15m'yi içerir) → **tek bir "konsensüs olasılığı" üretilmez**; yalnız "kaç TF
  tabandan aynı yöne anlamlı ayrışıyor" sayısı gösterilir.
- Hiyerarşik MTF (alt TF eşleşmesi + üst TF bağlam benzerliği) ayrı motor değil, bağlam vektöründeki `htf` ile yapılır.

---

## 8. Sonuç etiketleri — "hangi yön, nereye kadar"

Her kütüphane penceresi sonu j için önceden hesaplanır (`outcomes.npz`), hepsi A_j (o anki ATR) biriminde:

| Etiket | Tanım | Ekrandaki karşılığı |
|---|---|---|
| r_h (h = 1…H_max) | (C_{j+h} − C_j) / A_j | yol konisi; H sonunda net hareket |
| MFE_H | max_{1…H} (H_{j+h} − C_j) / A_j | "en fazla nereye kadar çıktı" |
| MAE_H | min_{1…H} (L_{j+h} − C_j) / A_j | "en fazla ne kadar ters gitti" |
| race_k | ±k·A_j'den hangisine önce dokunuldu (k ∈ {0,5 · 1,0 · 1,5}); aynı barda ikisi → 1m ile çöz, yoksa "belirsiz" | TP/SL dilinde yön |
| rng_H | (max H − min L) / A_j | yönsüz "kaç pips oynar" |
| t_mfe | MFE'ye ulaşma süresi (bar) | zamanlama |

- **Pips'e dönüş:** pips = r · A_now / pip. A_now ile ölçeklemek, 2021'deki bir eşleşmeyi bugünün oynaklığına taşır.
  % ölçekleme araştırmada ikincil varyant.
- **Ufuk seti** (ön-kayıtlı, TF başına 3, bar): 5m {6, 12, 48} · 15m {4, 16, 32} · 30m {2, 8, 16} · 1h {4, 8, 24} ·
  4h {3, 6, 30} · 1d {1, 5, 20}.
- **Giriş referansı:** ekranda C_j (kapanış). EV/işlem iddialarında **sonraki M1 açılışı + gerçek spread** (E7; 2. KURAL
  ölçüt 5).
- Aynı barda TP+SL belirsizliği yön istatistiğinde 0,5, EV hesabında aleyhe sayılır (ön-kayıtlı).

---

## 9. Tahmin birleştirme

Komşu kümesi 𝒩 ve ağırlıklar w_j ile:

- **Etkin örneklem:** n_eff = (Σw)² / Σw² (Kish); ayrıca farklı gün sayısı gösterilir.
- **Taban p₀:** aynı sembol × TF × H × **seans kovası**, kütüphanenin aynı dönemi. Sürüklenme (E13) ve gün-içi tabana
  gelecek sızdırma (E15) yüzünden taban "aynı günün ortalaması" değil, dönem × saat kovasıdır.
- **Yön:** P_ham = Σ w_j · 1[r_H,j > 0] / Σw; büzülme P̂ = (n_eff · P_ham + m · p₀) / (n_eff + m), **m = 20**
  (ön-kayıtlı) → az eşleşmede tahmin tabana yapışır. Gösterilen asıl bilgi **fark = P̂ − p₀**.
- **Büyüklük:** ağırlıklı kantiller (P10, P25, P50, P75, P90) — r_H, MFE, MAE, rng; beklenen değer aynı şekilde μ₀'a
  büzülür: Ê = (n_eff · r̄ + m · μ₀) / (n_eff + m).
- **Belirsizlik:** gün-blok bootstrap (komşular günlerine göre kümelenir) → P̂ ve P50 için %80 aralık.
- **Konformal kalibrasyon** (araştırmada): VAL'de P10–P90 bandının gerçek kapsama oranı ölçülür, bant genişliği
  nominal %80'e ayarlanır, TEST'te doğrulanır → "kaç pips" aralığı istatistiksel olarak dürüst olur.
- **Sorgu-başına plasebo:** aynı seans kovası ± 1 saat ve ATR yüzdeliği ± 10 puan havuzundan rastgele K pencere × 1.000
  → P_ham ve medyan |r_H| için p-değeri. p > 0,10 ise etiket: *"Bu eşleşmeler, rastgele seçilmiş benzer oynaklıktaki
  anlardan farklı değil."*

---

## 10. Dürüstlük katmanı (pazarlıksız)

Her yanıtta: n_eff, farklı gün, p₀, fark, %80 aralık, plasebo p, nadirlik, profil rozeti.

| Rozet | Koşul | Ekranda |
|---|---|---|
| 🟢 Doğrulanmış (yön) | Profil TEST'te yön ölçütlerini geçti (§11.6) | Yön çubuğu renkli + "geçmişte bu ayarla isabet %X (n)" |
| 🔵 Doğrulanmış (büyüklük) | Büyüklük ölçütlerini geçti | Koni/kantiller renkli |
| ⚪ Bilgi amaçlı | Doğrulanmamış veya manuel ayar | Yön gri; AL/SAT kelimesi YOK; başlık "tarihsel dağılım" |
| ⚠ Yetersiz | n_eff < 15 veya plasebo p > 0,10 veya nadirlik > %95 | Uyarı metni öne çıkar |

- Tahmin `signal_gates`'e, bota veya decider'a **bağlanmaz**. Yalnız 2. KURAL kartıyla (bar verisinden yeniden
  üretilebilir → `go_live_gate` tarzı kart mümkün) ve önce gölgede.
- Benzerlik % ≠ olasılık: ikisi ayrı yerde gösterilir.

---

## 11. Sembole özel araştırma protokolü ("en tahmin edilebilir mum sayısı")

### 11.1 Neyi seçiyoruz

Her sembol × TF için: motor (A / B / AB), X (A) veya derinlik D (B/AB), τ veya K, bağlam λ, ufuk H, hedef (net işaret /
race_1,0).

### 11.2 Ön-kayıtlı ızgara (bilerek küçük)

| Motor | Izgara | Yapılandırma |
|---|---|---|
| A | X ∈ {1, 2, 3} × τ ∈ {0,15, 0,25} | 6 |
| B | D ∈ {9, 17, 33, 65} × K ∈ {50, 150} × λ ∈ {0, 1} | 16 |
| AB | X_f ∈ {1, 2} × D ∈ {17, 33}, K = 50 | 4 |

× 3 ufuk × 2 hedef → TF başına 156, 6 TF'de sembol başına ~940 yapılandırma.
**Birincil hipotez seçimsizdir:** eşit ağırlıklı topluluk (B: D ∈ {9, 17, 33}, K = 150, λ = 0) — tek test, seçim yükü
yok. "En iyi mum sayısı" analizi ikincildir ve seçim düzeltmesine tabidir (§11.5).

### 11.3 Bölme ve yürüyen-ileri değerlendirme

- Kronolojik: başlangıç … T₁ (yalnız kütüphane) | T₁ … T₂ = **VAL** (seçim) | T₂ … son = **TEST** (bir kez açılır).
  Öneri: TEST = son 12 ay, VAL = önceki 12 ay. 5m'de (15–21 ay) VAL/TEST 4'er ay.
- Her değerlendirme anı t için kütüphane = {j : j + H_max < t − embargo}, embargo = 1 işlem günü (genişleyen pencere —
  canlıyla aynı mantık).
- Bağımsızlık: anlamlılık için sorgular ≥ H aralıklı; ayrıca gün-blok bootstrap (E6/E9).
- Her koşudan önce: saat ekseni testi, "bar bitişi ≤ karar anı" testi, prefix testi (geleceği değiştir → geçmiş
  özellikler değişmemeli; meta-ders 9).
- Maliyet: 2 yıllık 15m VAL+TEST ≈ 47 bin sorgu × 70 bin kütüphane × 21 boyut ≈ 7·10¹⁰ işlem → BLAS ile saniyeler;
  bir sembolün tüm ızgarası Mac'te dakikalar mertebesinde.

### 11.4 Ölçütler ve tabanlar (hiyerarşik)

**Yön**
- Brier becerisi: BSS = 1 − Brier / Brier_ref; ref = seans-kovası taban oranı p₀(saat) (sabit p₀ değil).
- Ek tabanlar: (i) momentum (son H getirisinin işareti), (ii) Motor 0 Markov, (iii) λ = 1 ise "yalnız bağlam" modeli.
  kNN hepsini geçmeli.
- Kapsam–isabet: |P̂ − p₀| ≥ 0,05 kümesinde isabet ve kapsam, plasebo karşılığıyla.
- **Yön-ayrık rapor zorunlu** ("korku döner coşku dönmez" asimetrisi; ayı-sonrası ve boğa-sonrası tahminler ayrı).

**Büyüklük**
- Kantil (pinball) kaybı becerisi = 1 − L / L_ref; ref = aynı TF × H × seans kovası, koşulsuz ATR-birimli kantiller —
  yani **"yalnız ATR + saat" modeli**. Oynaklık kümelenmesinin ATR'den gelen kısmı tabana bağışlanır; kNN'nin EK katkısı
  ölçülür.
- Kapsama: P10–P90'ın gerçek kapsaması ≈ %80.

**Ekonomik** (yalnız yön geçerse): 2. KURAL kartı — ≥ 150 olay, ort. R > 0 ve P(EV > 0) ≥ %90, iki yarı ≥ 0,
spread × 1,5, sonraki M1 açılışı girişi, tek pozisyon.

### 11.5 Seçim yükü ve plasebolar

1. **Dairesel kaydırma maks-istatistiği (E24):** sonuç dizisi rastgele ≥ 1 ay kaydırılır (özellik ve komşu listeleri
   sabit; otokorelasyon ve taban korunur), tüm ızgara yeniden değerlendirilir, en iyi VAL skoru kaydedilir × 200.
   Gerçek en iyi, boş dağılımın %95'ini geçmeli. Komşu listeleri değişmediği için ucuz (yalnız yeniden toplama).
2. **Oynaklık-eşli rastgele komşu plasebosu (PM-2):** komşular aynı ATR yüzdeliği + seans kovasından rastgele
   pencerelerle değiştirilir → şekil benzerliği bilgi katıyor mu?
3. **Sentetik piyasa testi:** aynı oynaklık profilli blok-bootstrap getiri serisinde tüm boru hattı → beceri ≈ 0
   çıkmalı (boru hattının kendisinde sızıntı olmadığının kanıtı).
4. **Plato:** seçilen yapılandırmanın komşuları (D ± 1 seviye, diğer K) da pozitif olmalı.
5. **Yarılar ve yıllar:** TEST'in iki kronolojik yarısı da ≥ 0; yıl yıl tablo.
6. **Uç gün bağımlılığı:** en iyi 5 gün çıkarılınca hâlâ pozitif mi (GF-21/22 uyarısı).

### 11.6 "Doğrulanmış" tanımı (sonuçlardan önce sabit)

- **Yön:** TEST BSS > 0 · gün-blok P(BSS > 0) ≥ %95 · iki yarı > 0 · momentum, Markov ve oynaklık-eşli plaseboyu geçer ·
  (ikincil seçimse) maks-istatistik p < 0,05.
- **Büyüklük:** TEST pinball becerisi > 0 · P ≥ %95 · iki yarı > 0 · kapsama |%80 − gerçek| ≤ 5 puan.

### 11.7 Çıktılar

- **Tahmin edilebilirlik haritası** (sembol başına ısı haritası): satır TF, sütun mum sayısı (X veya D), hücre TEST yön
  becerisi + büyüklük becerisi + anlamlılık işareti. Kullanıcının istediği "her sembol için en tahmin edilebilir mum
  sayısı" sorusunun dürüst cevabı budur — cevap "hiçbiri" de olabilir.
- `backend/data/candle_match/profiles.json` (commit'lenir), örnek:

```json
{
  "version": "2026-10-xx",
  "protocol_sha": "…",
  "data_manifest_sha": "…",
  "NDX.INDX": {
    "15m": {"engine": "pyramid_knn", "depth": 33, "K": 150, "ctx": false,
            "horizons": [4, 16, 32], "target": "sign",
            "direction": {"verified": false, "test_bss": -0.002, "n_test": 1240},
            "magnitude": {"verified": true, "test_pinball_skill": 0.031, "coverage_p10_p90": 0.79},
            "rarity_quantiles": [0.41, 0.55, 0.73, 0.98], "pair_dist_median": 6.8}
  }
}
```

- Deftere ME-nn satırları (olumsuz sonuçlar dahil), Evrim Paneli oturum notu, `analyses.json` girdisi.
- Yeniden kalibrasyon: 3 ayda bir veya veri kaynağı değişince. Profil `data_manifest_sha` taşır; uyuşmazlıkta rozet
  ⚪'a düşer.

---

## 12. Sembole özel özelleştirmeler

### 12.1 Ayar tablosu

| Ayar | NDX | DAX | XAU | OIL |
|---|---|---|---|---|
| TF seti | 5m (21 ay), 15m, 30m, 1h, 4h, 1d | 15m, 30m, 1h, 4h, 1d | 5m (15 ay), 15m, 30m, 1h, 4h, 1d | 5m (15 ay), 15m, 30m, 1h, 4h, 1d |
| Kütüphane derinliği varyantı (1h+) | 5 y / 10 y | 5 y / tam (~6,8 y) | 5 y / 10 y | 5 y / 10 y |
| 1d kütüphanesi | 10 y (1h'ten) | ~6,8 y | 10 y | 10 y |
| Seans kovaları (borsa yerel saati) | Asya · Avrupa · ABD açılış (09:30–11:00 ET) · ABD öğle · ABD kapanış | Asya · Xetra açılış (09:00–10:00 CET) · Avrupa · ABD açılış · akşam | Asya · Londra · NY (veri saatleri 08:30 ET) · akşam | Asya · Avrupa · NY açılış + EIA · NY öğleden sonra · settle sonrası |
| Bağlam adayları | `vix_reg`, `stres`, `trend` | `stres`, `vix_reg` | `trend`, `loc`, `vol_z` | `loc`, `vol_z`, gün (Çar/Per) |
| race_k | 0,5 / 1 / 1,5 | 0,5 / 1 / 1,5 | 0,75 / 1 / 1,5 | 0,5 / 1 / 1,5 |
| Özel temizlik | 1m 02-10→03-08 +60 dk (E4); 30m/1h'i bugüne uzat | 2020 öncesi 1h'i at | Yahoo satırlarını at, broker'dan doldur | Yahoo + vade devri |
| Pip | 1,0 | 1,0 | 0,1 | 0,01 |

### 12.2 Gerekçeler

**NDX (`NAS100`)**
- 23 saatlik CFD; günlük ara NY 17:00–18:00. ABD nakit açılışı en büyük oynaklık sıçraması → seans kovası zorunlu
  bağlam adayı; ATR14 normalizasyonu açılış mumunu "dev" gösterir ve yalnız diğer açılış patlamalarıyla eşler.
- 2021–26 güçlü yukarı sürüklenme → p₀ ≈ %52–55; yön farkı mutlaka seans-kovası tabanına göre (E13).
- Mekanizmalar: VIX rejimi (A), stres + VIX → kapitülasyon dönüşü (CAPREV, B+), "korku döner coşku dönmez" (ayı
  şekillerinden sonra dönüş, boğa şekillerinden sonra devam beklentisi → yön-ayrık rapor), Cuma etkisi (B2).
- Spread ~1,5 puan.

**DAX (`GER40`)**
- Xetra açılışı (09:00 CET) ve ABD açılışı iki ayrı oynaklık tepesi. Hacim sentetik → kullanılmaz.
- CAPREV DAX'a taşındı (GF-18) → `stres` bağlamı; NDX'teki "korku döner" ilkesi burada da geçerli.
- 5m/1m kütüphanesi yok; en kısa TF 15m.

**XAUUSD**
- İki yönlü trend/momentum (MK-03/04: yeni tepe BUY gölgede, B−); makro DXY/US10Y yalnız ÖNCEKİ gün değerleriyle
  kullanılabilir (aynı gün değer sızıntıydı — CORTEX) → bağlamda `trend`, `loc`, `vol_z`.
- Fakeout lab'da XAU yarış geometrisi tp 0,75 → race_k setinde 0,75.
- Fiyat ≈ 4.385 → %0,01 = 4,4 pips; pip $0,10.

**USOIL (`SpotCrude`)**
- Vade devri (§5.4); EIA Çarşamba stok raporu sıçraması; Perşembe çukuru (TQ); NY settle.
- Dönüş/whipsaw karakteri (MK-03: yeni dip SELL bile pozitif) → `loc` önemli.
- % payın en çok yanılttığı sembol: %0,01 = 0,9 pips = 1h medyan mumun %1,9'u.

---

## 13. Çalışma zamanı akışı (tuşa basınca)

| Adım | İş | Bütçe |
|---|---|---|
| 1 | Kullanıcı sembol sayfasında **"Mum Eşleştir"**e basar (opsiyonel: TF, motor, pay, ufuk) | — |
| 2 | Kütüphaneye son kapanmış broker mumları eklenir (artımlı; aynı besleme) | < 200 ms |
| 3 | Profil yüklenir; her TF için motor/parametre | önbellek |
| 4 | Sorgu vektörleri (İkiz / piramit / bağlam) | < 5 ms |
| 5 | Arama + dışlamalar + tekilleştirme | < 50 ms/TF |
| 6 | Birleştirme, taban, plasebo (önceden hesaplı havuzlar), nadirlik | < 50 ms/TF |
| 7 | JSON yanıt; önbellek anahtarı (sembol, TF, son_bar_ts, parametreler) — yeni bar kapanana kadar aynı | — |
| 8 | Gölge kaydı: `backend/data/candle_match/predictions.jsonl` (önce yerel; sonra istenirse Supabase) → H bar sonra aynı kütüphaneden notlanır | arka plan |

Toplam hedef: 6 TF < 1,5 sn. Piyasa kapalıysa: "piyasa kapalı — son kapanmış mum: Cuma 20:55" yazılır, hesap yine
yapılır (yapı geçerli), sonuç ufkunun pazartesi açılışıyla başlayacağı not edilir.

---

## 14. API sözleşmesi (taslak)

| Uç nokta | Açıklama |
|---|---|
| `GET /api/candle-match/{symbol}?tfs=15m,1h,4h&engine=auto&tol=auto&horizon=auto` | Ana sonuç |
| `GET /api/candle-match/{symbol}/neighbors?tf=1h&limit=20` | En yakın eşleşmelerin ayrıntısı ("geçmişte göster") |
| `GET /api/candle-match/profiles` | Araştırma özeti + tahmin edilebilirlik haritası |
| `POST /api/candle-match/rebuild-library?symbol=` | Yönetici: kütüphaneyi yeniden kur |

Yanıt örneği (**değerler örnektir, gerçek değildir**):

```json
{
  "symbol": "NDX.INDX",
  "computed_at": "2026-10-12T14:03:11Z",
  "last_closed_bar": {"ts_utc": "2026-10-12T13:45:00Z", "ts_mt5": "2026-10-12 16:45", "close": 30655.2},
  "library": {"source": "broker", "from": "2021-10-12", "manifest_sha": "…", "stale": false},
  "timeframes": [{
    "tf": "15m",
    "profile": {"engine": "pyramid_knn", "depth": 33, "K": 150, "ctx": false,
                "badge_direction": "info", "badge_magnitude": "verified"},
    "query": {"atr_pips": 41.3, "candles_used": 33, "fine_candles": 3},
    "neighbors": {"k": 150, "n_eff": 96.4, "distinct_days": 131,
                  "similarity_median_pct": 63, "rc": 2.6, "rarity_pct": 41},
    "horizons": [{
      "h_bars": 16, "h_label": "4s",
      "p_up": 0.541, "p_up_ci80": [0.49, 0.59], "p0": 0.527, "lift_pp": 1.4,
      "net_pips": {"p10": -88, "p25": -39, "p50": 6, "p75": 47, "p90": 96},
      "mfe_pips": {"p50": 52, "p75": 91}, "mae_pips": {"p50": -47, "p25": -86},
      "range_pips_p50": 112,
      "race_1atr": {"up_first": 0.52, "down_first": 0.46, "ambiguous": 0.02},
      "placebo_p": {"direction": 0.38, "magnitude": 0.04},
      "test_skill": {"bss": -0.002, "pinball_skill": 0.031, "n_test": 1240}
    }],
    "cone": [{"step": 1, "p10": -18, "p25": -8, "p50": 0, "p75": 9, "p90": 19}],
    "top_matches": [{"end_ts_utc": "2024-03-18T13:45:00Z", "similarity_pct": 81,
                     "net_pips_h16": 34, "mfe_pips": 58, "mae_pips": -12}],
    "warnings": []
  }]
}
```

Kurallar: CORS mevcut ayarlar; hata → 500 + log (sessiz fail yok); kütüphane yoksa 503 + "kütüphane kurulmadı".

---

## 15. Panel (UI) tasarımı

```
┌ Geçmiş Eşleşme Radarı — NDX ─────────────────────────── [▶ Mum Eşleştir] [⚙] ┐
│ Son kapanmış mum 13:45 UTC (16:45 MT5) · kütüphane broker 2021-10 → bugün       │
├────────────┬────────────┬────────────┬────────────┬────────────┬───────────────┤
│    15m     │    30m     │     1h     │     4h     │     1d     │               │
│ ↑ %54  ⚪  │ ↑ %51  ⚪  │ ↓ %47  ⚪  │ …          │ …          │ TF uyumu:     │
│ taban %53  │ taban %52  │ taban %53  │            │            │ 1/5 TF        │
│ fark +1,4  │ fark −1    │ fark −6    │            │            │ anlamlı       │
│ 4s: +6 p   │            │            │            │            │               │
│ P25 −39 / P75 +47 🔵    │            │            │            │               │
│ MFE 52 · MAE −47        │            │            │            │               │
│ n_eff 96 · 131 gün · benzerlik %63 · plasebo p 0,38                            │
└────────────┴────────────┴────────────┴────────────┴────────────┴───────────────┘
[ Grafik: canlı mumlar + sağda gelecek konisi (P10–P90, P25–P75, medyan) + soluk 20 komşu yolu ]
[ Eşleşmeler: 2024-03-18 13:45 · %81 · 4s sonra +34 p (MFE 58 / MAE −12) ▸ tıkla → yan yana mini grafik ]
```

- **Konum:** Neural sembol sayfası (`frontend/app/neural/[symbol]/page.tsx`), Kırılım Radarı'nın yanında (Panel Tekrar
  Kuralı: tek yerde).
- **Bileşenler:** `frontend/lib/api/candleMatch.ts` (servis katmanı; bileşende fetch yok) +
  `frontend/components/neural/CandleMatchPanel.tsx` + koni katmanı için `SharedChart` (lightweight-charts 4.2.1)
  üzerinde gelecek zaman damgalı çizgi/alan serileri.
- **Ayarlar (⚙):** motor (Otomatik / İkiz / Piramit / Hibrit), pay (Otomatik / "benim payım" %0,01–0,05 kaydırıcı —
  canlı "≈ N eşleşme bulunur" göstergesiyle), ufuk, TF seti. Manuel ayar → ⚪ rozet.
- **Durumlar:** yükleniyor (TF başına iskelet), hata (TF başına; diğerleri çalışmaya devam), boş ("bu payla 5 yılda 0
  ikiz — piramit moduna geç ya da payı gevşet"), bayat veri ("son mum 25 dk önce — besleme gecikmesi").
- **"Neden bu kadar az eşleşme?"** bilgi balonu: §3.2 tablosu + X_max formülü sade dille.
- Renkler: proje renk sistemi (yön yeşil/kırmızı yalnız 🟢 rozetle; ⚪'da gri).

---

## 16. Kod yerleşimi (öneri)

```
backend/services/candle_match/
    library.py      # parquet yükle, manifest, artımlı güncelleme, saat testi
    features.py     # ATR, mum vektörü, piramit, bağlam (saf numpy, nedensel)
    outcomes.py     # r_h, MFE/MAE, race, rng ön-hesabı
    engines.py      # twin_search (A), pyramid_knn (B), hybrid (AB), shape (C)
    aggregate.py    # ağırlık, n_eff, büzülme, kantiller, bootstrap, plasebo, nadirlik
    profiles.py     # profiles.json yükle + varsayılanlar + rozet mantığı
    service.py      # orkestrasyon + önbellek + gölge kaydı
backend/routers/candle_match_router.py
backend/data/candle_match/profiles.json          # commit'lenir
data/candle_match/<SYM>/<tf>.parquet            # git dışı
scripts/candle_match/build_library.py
research/mum_eslestirme_20261012/               # fizibilite (bugün) + PROTOCOL.md + yürüyen-ileri değerlendirme
frontend/lib/api/candleMatch.ts
frontend/components/neural/CandleMatchPanel.tsx
backend/tests/test_candle_match_*.py
```

Araştırma betiği `backend/services/candle_match` modüllerini doğrudan import eder → sadakat yapısal olarak garanti.

---

## 17. Test ve doğrulama planı

**Birim testleri**
- Piramit: sentetik seride bilinen değerler; seviye sınırlarında off-by-one.
- Nedensellik: prefix testi — j'den sonraki barlar değiştirilince j'nin özellikleri değişmez.
- Dışlama: hiçbir komşunun sonuç penceresi sorgu anını geçmez; öz-çakışma ve tekilleştirme aralıkları.
- ATR: "son mumu içermez" kuralı; segment başında NaN davranışı.
- Pips dönüşümü dört sembolde; büzülme formülü sınır durumları (n_eff = 0 → P̂ = p₀).
- Saat ekseni: ABD açılış sıçraması testi; 4h/1d broker hizası.

**Sızıntı testleri** — "bar bitişi ≤ karar anı"; üst-TF bağlamı yalnız kapanmış bar (E16); VIX önceki gün tamamlanmış
kapanış (E20); taban dönem × seans kovası (E15).

**Altın test** — geçmiş bir an için canlı servis (kütüphane o ana kesilmiş) ile araştırma tahmini birebir aynı;
200 rastgele anda %100 uyum (CAPREV sadakat 54/54 örneği).

**Sentetik null** — blok-bootstrap rastgele yürüyüşte yön becerisi ≈ 0.

---

## 18. Yol haritası

| Faz | İçerik | Çıkış ölçütü |
|---|---|---|
| **0 — Veri** (1–2 gün) | Kütüphane kurucu, temizlik, manifest, saat testleri; NDX 30m/1h ve XAU/OIL broker uzatması; DAX 2020 kesimi; OIL devir tespiti; 5m/1m için Dukascopy/MT5 derin çekim denemesi | 4 sembol × TF seti tutarlı UTC parquet; testler yeşil |
| **1 — Çekirdek** (2–3 gün) | `features/engines/outcomes/aggregate`; birim testleri; CLI ile tek sorgu | Testler yeşil; bir tarihsel an için elle doğrulanmış çıktı |
| **2 — Araştırma** (3–5 gün) | `PROTOCOL.md` ön-kayıt (bu belgenin §11'i) → yürüyen-ileri → plasebolar → TEST bir kez → harita + `profiles.json` + rapor; defter ME satırları | Rapor + profil; olumsuz sonuç da kabul |
| **3 — Ürün** (2–3 gün) | API + panel (varsayılan ⚪ bilgi modu), gölge kaydı + notlayıcı, Evrim Paneli kataloğu | Uçtan uca çalışır; sadakat testi %100 |
| **4 — Canlı karne** (sürekli) | ≥ 100 bağımsız gölge tahmin sonrası canlı/araştırma tutarlılığı | Ancak sonra kart / kapı tartışması |

---

## 19. Açık sorular — kullanıcı ve diğer yapay zekâyla tartışılacaklar

**Kullanıcı kararı gerekenler**
1. Pay semantiği: içeride ATR, ekranda % — kabul mü, yoksa % modu varsayılan mı kalsın?
2. Varsayılan motor: Hibrit (son 2 mum birebir + 31 mum bağlam) mı, saf Piramit mi?
3. Ufuk: TF başına sabit 3 ufuk mu, kullanıcı seçimi mi?
4. 5 yıllık 5m/1m için dış veri (Dukascopy) edinmeye değer mi? (Fizibilite: 1m X tavanını yalnız ~3,7'ye çıkarır.)
5. Panel yeri: Neural sayfası mı, sembol sayfası mı?

**Diğer yapay zekâya teknik sorular**
1. Piramit yerine dalgacık (Haar) katsayıları veya PAA/SAX daha iyi bir düşük-boyutlu temsil olur mu? Seviye ağırlıkları
   (√s yerine başka üs) nasıl ön-kayıtlanmalı?
2. kNN çekirdek bant genişliği ve K için veri-güdümlü ama sızıntısız seçim (VAL içinde iç çapraz doğrulama)?
3. Büyüklük hedefi için kantil kNN'e alternatif: konformal kantil regresyonu? Hangisi az parametreyle daha dürüst?
4. Seçim düzeltmesi: dairesel kaydırma maks-istatistiği yerine Hansen SPA / Romano-Wolf daha mı uygun?
5. Bağlam ağırlığı λ'yı sabit {0, 1} yerine Mahalanobis ölçekli tek parametre yapmak?
6. Öğrenilmiş benzerlik (siamese/contrastive) — hangi koşulda denenmeye değer, aşırı uyum nasıl önlenir?
7. Rejim değişimi: eski komşulara zaman-çürüme ağırlığı (exp(−yaş/τ)) mı, yoksa sert 5 yıl penceresi mi?

---

## 20. Değiştirilemez kısıtlar (diğer yapay zekâ için)

Bu projede kanıtların çoğu aşağıdakilerde çöktü (defter §1). Tasarımda değişiklik önerilirken bunlar korunmalı:

1. **Koşan mum yok;** yalnız kapanmış mumlar. Üst TF bağlamı yalnız kapanmış üst-TF barı (E16).
2. **Tek besleme** (§5.2); Yahoo/broker karışımı yok (E21). Saat ekseni ölçülür, varsayılmaz (E2–E5).
3. **Kütüphane nedensel:** komşunun sonucu karar anından önce bitmiş olmalı; araştırmada genişleyen pencere + embargo.
   `mt5.copy_rates_from` ileriye bar döndürür → geçmiş an kurgusunda `backend/research/_bars_upto.py` (E1).
4. **Taban zorunlu:** dönem × seans kovası (E13, E15); çıplak isabet yasak — fark + beceri + beklenti (R).
5. **Bağımsız n:** komşular tekilleştirilir, sorgular ≥ H aralıklı, gün-blok bootstrap (E6, E9).
6. **Ön-kayıt:** ızgara, ufuklar, ölçütler sonuçlardan önce `PROTOCOL.md`'ye yazılır; TEST bir kez açılır.
7. **Seçim düzeltmesi:** "en iyi mum sayısı" maks-istatistik plasebosundan geçmeden doğrulanmış sayılmaz (E23, E24).
8. **Plasebo her sayıda:** oynaklık-eşli rastgele komşu + dairesel kaydırma + sentetik piyasa.
9. **Canlıya yok:** kapı/bot/decider bağlantısı yalnız 2. KURAL kartıyla, önce gölge; varsayılan ⚪ bilgi modu.
10. **Sadakat:** araştırma ve canlı aynı çekirdek kodu kullanır.

---

## Ek A — Sözde kod

```python
def pyramid_features(o, h, l, c, atr_prev, levels):           # nedensel: e ve öncesi
    feats, lag = [], 0
    for s in levels:
        H = rolling_max(h, s).shift(lag); L = rolling_min(l, s).shift(lag)
        O = o.shift(lag + s - 1);          C = c.shift(lag)
        for v in (H - O, L - O, C - O):
            feats.append(v / atr_prev / sqrt(s))
        lag += s
    return stack(feats)                                         # [n × 3·len(levels)]


def search(lib, q, t, cfg):
    d2 = lib.sqnorm + sqnorm(lib.P[q]) - 2 * lib.P @ lib.P[q]   # BLAS
    d2[~lib.valid] = inf
    d2[lib.end + cfg.H > t - cfg.embargo] = inf                 # sonucu bilinmeyen
    d2[abs(lib.end - q) < cfg.coverage] = inf                   # öz-çakışma
    if cfg.twin_filter:
        d2[~twin_mask(lib.F, q, cfg.X_f, cfg.tau)] = inf        # Hibrit
    cand = argpartition(d2, 5 * cfg.K)[: 5 * cfg.K]
    nbrs = greedy_dedup(sorted_by(d2, cand), min_gap=max(cfg.H, cfg.coverage // 2))[: cfg.K]
    return nbrs, sqrt(d2[nbrs])


def aggregate(nbrs, dist, out, H, p0, mu0, m=20):
    h = median(dist); w = exp(-0.5 * (dist / h) ** 2)
    n_eff = w.sum() ** 2 / (w ** 2).sum()
    up = (w * (out.r[nbrs, H] > 0)).sum() / w.sum()
    p_hat = (n_eff * up + m * p0) / (n_eff + m)
    e_hat = (n_eff * wmean(out.r[nbrs, H], w) + m * mu0) / (n_eff + m)
    q = wquantile(out.r[nbrs, H], w, [.10, .25, .50, .75, .90])
    return dict(p_up=p_hat, lift=p_hat - p0, exp=e_hat, q=q, n_eff=n_eff,
                mfe=wquantile(out.mfe[nbrs, H], w, [.5, .75]),
                mae=wquantile(out.mae[nbrs, H], w, [.5, .25]))


def walk_forward(lib, query_times, cfg):                         # VAL veya TEST
    preds, ys = [], []
    for t in query_times:                                       # ≥ H aralıklı
        nbrs, dist = search(lib, t, t, cfg)
        preds.append(aggregate(nbrs, dist, lib.out, cfg.H, p0_session(lib, t), mu0_session(lib, t)))
        ys.append(lib.out.r[t, cfg.H] > 0)
    return brier_skill(preds, ys, ref="p0_session"), pinball_skill(preds, lib.out, ref="atr_session")


def max_stat_null(grid, lib, n_shift=200):                      # E24
    best = []
    for s in random_shifts(n_shift, min_months=1):
        lib_s = lib.with_circular_shifted_outcomes(s)           # komşu listeleri sabit
        best.append(max(walk_forward(lib_s, VAL, cfg)[0] for cfg in grid))
    return best                                                 # gerçek en iyi > %95 kantili mi?
```

## Ek B — Fizibilite ölçümünü yeniden üretme

```bash
python3 research/mum_eslestirme_20261012/fizibilite_1_birebir.py      # ~3 dk → results/fizibilite_1_birebir.csv
python3 research/mum_eslestirme_20261012/fizibilite_2_huni_kismi_knn.py # ~4 dk → results/fizibilite_2_huni_kismi_knn.csv
python3 research/mum_eslestirme_20261012/fizibilite_3_piramit.py      # ~1 dk → ekrana
python3 research/mum_eslestirme_20261012/ozet.py                      # → results/ozet.csv (§3.1–3.2 tabloları)
```

Duman testi: `FEAS_ONLY="NDX:1h" FEAS_NQ=4 python3 …/fizibilite_1_birebir.py /tmp/x.csv`.

## Ek C — Sözlük

| Terim | Anlam |
|---|---|
| ATR14 | Son 14 mumun ortalama gerçek aralığı; "tipik mum boyu" |
| İkiz | Son X mumu birebir pay içinde eşleşen geçmiş pencere |
| Piramit | Son mumları tam, eskileri giderek büyüyen gruplar hâlinde birleştiren temsil |
| kNN | En yakın K komşu araması |
| RC (göreli kontrast) | Medyan mesafe ÷ K. komşu mesafesi; 1'e yakınsa komşular rastgeleden ayırt edilemez |
| n_eff | Ağırlıklı etkin örneklem: (Σw)² / Σw² |
| Taban p₀ | Koşulsuz yukarı oranı (aynı dönem × seans kovası) |
| Büzülme | Az veride tahmini tabana çekme: (n·P + m·p₀) / (n + m) |
| MFE / MAE | Ufuk içindeki en olumlu / en olumsuz gidiş |
| BSS | Brier beceri skoru; > 0 → tabandan iyi |
| Pinball kaybı | Kantil tahmininin kaybı; büyüklük becerisinin ölçüsü |
| Konformal kalibrasyon | Tahmin aralığını, doğrulama verisinde ölçülen kapsamaya göre genişletip daraltma |
| Embargo | Araştırmada sorgu ile kütüphane arasında bırakılan güvenlik boşluğu |
| Maks-istatistik plasebosu | Tüm aramayı rastgele kaydırılmış sonuçlarla tekrarlayıp "en iyinin" tesadüfen ne kadar iyi çıktığını ölçme |
