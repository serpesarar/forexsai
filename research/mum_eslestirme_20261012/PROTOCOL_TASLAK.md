# Mum Eşleştirme — Ön-Kayıt Protokolü (TASLAK, dondurulmadı)

> **Durum:** TASLAK v0.2 · 2026-10-12 · Tasarım: `docs/MUM_ESLESTIRME_ALGORITMASI.md` (v0.2) · İnceleme:
> `docs/MUM_ESLESTIRME_TASARIM_INCELEMESI_CODEX.md`.
> **Dondurma koşulları:** (1) kullanıcı kararları (tasarım §19) verildi, (2) Faz 0 veri kabul testleri geçti (§2),
> (3) bu dosyanın son hâlinin sha1'i deftere (ME satırı) ve Evrim Paneli'ne yazıldı. **Dondurmadan önce hiçbir sonuç
> (gelecek getiri) hesaplanmaz.** Dondurmadan sonraki her değişiklik §14'e tarih + gerekçe + "sonuç görüldü mü" ile yazılır.

---

## 1. Hipotezler

| ID | Tür | Hipotez | Beklenti (yazılı) |
|---|---|---|---|
| H1 | **birincil, seçimsiz** | Sabit yapılandırmanın (§5.1) komşu dağılımından üretilen büyüklük kantilleri (|r_H|, MFE_H, MAE_H) "ATR + seans" tabanından iyi (pinball becerisi > 0) | küçük pozitif olası |
| H2 | **birincil, seçimsiz** | Aynı yapılandırmanın ham yön olasılığı seans-kovası tabanından iyi (Brier becerisi > 0) | ≈ 0 (PM, OLD-13, IO-18) |
| H3 | **birincil, seçimsiz** | Aynı yapılandırmanın "+T, −T'den önce, H içinde" olasılığı eşli tabandan iyi (log-loss becerisi > 0) | ≈ 0 – küçük |
| H4 | ikincil | Temsil sıralaması: ham 7 mum (R7) / piramit (P33) / piramit + yol özeti (P33Y) / İkiz / Hibrit | bilinmiyor |
| H5 | ikincil, seçim düzeltmeli | Sembol × TF × ufuk × hedef için "en iyi mum sayısı / temsil" | seçim gürültüsü riski yüksek (E23/E24) |

Birincil hipotezler **72 hücrede** (4 sembol × 6 TF × 3 ufuk) sınanır; hücre sayısı için Holm düzeltmesi + "geçen hücre
sayısı vs null altında beklenen" birlikte raporlanır. H1–H3 tek sabit yapılandırmayla yapıldığı için yapılandırma seçimi
yükü taşımaz; hücre ailesi yükü taşır.

## 2. Veri ve kabul testleri (Faz 0'da geçmeli)

- Semboller: NDX (`NAS100`), DAX (`GER40`), XAUUSD, USOIL (`SpotCrude`) — **yalnız broker (Pepperstone MT5) kaynağı**.
  Kaynağı belirsiz satır (`src` yok/karışık) doğrulanmış profile girmez; NDX 2025 Dukascopy kısmı ayrı `src` etiketiyle
  tutulur ve yalnız "kaynak duyarlılığı" ek analizinde kullanılır.
- TF: 5m, 15m, 30m, 1h (doğrudan), 4h ve 1d (1h'ten, broker D1/H4 sınırıyla — sınır broker verisinden doğrulanır).
- Her satırda: ham zaman, uygulanan dönüşüm (kaynak/dönem başına bir kez), `src`, `seg`, `flags`
  (`planned_break` | `missing` | `roll` | `partial_htf`).
- Kabul testleri: (a) zaman ekseni — bağımsız bir UTC beslemesiyle getiri gecikme korelasyonu tepe gecikmesi = 0
  (birincil); seans oynaklık tepesi yardımcı kontrol; (b) üst-TF mumlar yalnız beklenen alt-bar kapsamı tamsa;
  (c) eksik veri: herhangi bir beklenmeyen boşluk (planlı ara/hafta sonu/tatil dışı) pencereyi ve ufku geçersiz kılar
  (4 günden kısa olanlar dahil); (d) OIL devri: devir takvimi/kontrat metadata'sıyla işaretlenir; takvim yoksa devir
  adayı (> 3 ATR açılış boşluğu) yalnız inceleme listesine girer, otomatik devir sayılmaz; (e) yinelenen zaman damgası 0.
- DAX 1h 2020 öncesi dışarıda (ME-00: seyrek).

## 3. Kütüphane politikası — `eligible(t)` (canlı ve araştırma AYNI fonksiyon)

Karar anı t (sorgunun son kapanmış barının bitişi) için aday pencere sonu j uygundur ⇔
1. ts(j) ≥ t − L (L = 5 yıl; 10 yıl ayrı profil, seçim ailesinde sayılır),
2. j + H ≤ t (sonuç penceresi t'de kapanmış),
3. j'nin özellik penceresi ve sonuç penceresi `missing`/`roll` bayrağı geçmiyor, aynı `src` grubu,
4. j'nin özellik penceresi sorgunun özellik penceresiyle çakışmıyor.
Ek embargo yok (2. madde geleceği zaten dışlar). Taban oranları, ölçekleyiciler, bağlam standart sapmaları, nadirlik
dağılımı, kabul eşiği d_acc ve kalibrasyon katsayıları da yalnız `eligible(t)` kümesinden (veya t'den önce dondurulmuş
geliştirme bölümünden) üretilir.

## 4. Özellik sözleşmesi

- **ATR:** A(e) = TR'nin e−14 … e−1 barları üzerinden **basit** ortalaması (Wilder değil). TR = max(H−L, |H−C₋₁|, |L−C₋₁|).
- **Mum vektörü (ortak ölçek):** pencere sonu e için her mum i: (H_i−O_i, L_i−O_i, C_i−O_i) / A(e).
- **Kullanıcı % modu:** mumun kendi açılışına göre %; ölçek yok (yalnız İkiz-% görünümünde, doğrulanmış profilde değil).
- **R7:** son 7 mum, 21 boyut.
- **P33:** piramit [1,1,1,2,4,8,16]; seviye özelliği (u,d,b)/√s; 21 boyut.
- **P33Y:** P33 + yol özeti: (C_{e−k} − C_e)/A(e), k ∈ {1,2,4,8,16,32} (6) + birleşik seviyelerde (s ≥ 2) tepe-önce-dip
  işareti (4) + verimlilik |C_e − C_{e−33}| / Σ|ΔC| (1). Yol grubu, geliştirme bölümünde toplam varyansı şekil grubuna
  eşit olacak tek bir katsayıyla ölçeklenir.
- **İkiz T(X, τ):** X ∈ {1,2,3}, τ ∈ {0,15; 0,25} (ortak ölçek, L∞).
- **Hibrit:** T(2; 0,20) süzgeci → P33 sıralaması. Süzgeç sonrası uygun olay < 20 ise **çekimser** (P33'e sessiz geçiş yok;
  kullanıcı arayüzünde ayrı mod olarak gösterilir).
- Bağlam (`vol_z`, `loc`, `trend`, seans, `htf`, NDX/DAX `vix_reg`/`stres`) **yalnız H4/H5'te** ve "yalnız bağlam" tabanıyla
  birlikte.

## 5. Yapılandırmalar

### 5.1 Birincil sabit yapılandırma (H1–H3)
P33 · Öklid · kabul eşiği d_acc = geliştirme kütüphanesindeki rastgele pencere çifti mesafelerinin %5 yüzdeliği ·
K = min(150, kapasite) · L = 5 yıl · çekirdek ağırlık w = exp(−½(D/h)²), h = kabul edilen komşuların medyan mesafesi ·
büzülme m = 20 · olay tekilleştirme: seçilen komşuların özellik+sonuç aralıkları çakışmaz · kabul edilen bağımsız olay
< 20 → **çekimser** (tahmin yok; yalnız taban gösterilir).
**Kapasite:** kapasite(H) = ⌊ uygun bar sayısı / (kapsam + H) ⌋; K hiçbir zaman kapasiteyi aşamaz (1d, 5 y, H = 20 → ≤ 24).

### 5.2 İkincil ızgara (H4/H5) — tam seçim ailesi
Temsil {R7, P33, P33Y, T(1..3 × 2 τ), Hibrit} (10) × d_acc {%2, %5} × K {50, 150 — kapasiteyle sınırlı} × L {5 y, 10 y (yalnız 1h+)}
× bağlam {kapalı, açık} × hedef (§6: Y1, Y2, Y3×3, Y4) × ufuk (3) × TF (6) × sembol (4). Ailenin gerçek boyutu koşu
başında sayılıp rapora yazılır (≈ 50 bin test mertebesi).

## 6. Hedefler (ATR birimi, ref fiyat = son kapanmış barın kapanışı C_t)

| ID | Tanım |
|---|---|
| Y1 | ham yön: 1[C_{t+H} > C_t] |
| Y2 | anlamlı hareket (3 sınıf): r_H ≥ +b yukarı · ≤ −b aşağı · arası yatay; b = max(0,25 · A_t, 2 × ölçülen medyan spread) |
| Y3(T) | dört durum: +T önce · −T önce · H içinde hiçbiri · aynı barda ikisi (belirsiz; 1m varsa çözülür); T ∈ {0,5; 1,0; 1,5} |
| Y4 | |r_H|, MFE_H, MAE_H, rng_H kantilleri (0,1 / 0,25 / 0,5 / 0,75 / 0,9) |
| Y5 | hedef–süre tablosu: T ∈ {0,5; 1; 1,5; 2} × TF'nin üç ufku → P(+T'ye H içinde dokunma), P(+T, −T'den önce); aşağı ayrı |

- Belirsiz durum (Y3) **0,5 sayılmaz**: olasılık alt/üst sınırı (belirsizler hep aleyhte / hep lehte) raporlanır.
- "Hiçbiri" paydadan çıkarılmaz.
- Ufuklar (bar): 5m {6, 12, 48} · 15m {4, 16, 32} · 30m {2, 8, 16} · 1h {4, 8, 24} · 4h {3, 6, 30} · 1d {1, 5, 20}.
- Spread: NDX 1,5 puan (kutuda ölçülmüş), OIL 0,028 (USOIL breakout denetimi); DAX ve XAU Faz 0'da broker'dan ölçülür.

## 7. Bölümleme (F = dondurma tarihi)

| Bölüm | ≥ 3,5 yıllık TF'ler | Kısa TF'ler (5m: 15–21 ay) |
|---|---|---|
| Geliştirme (iç kronolojik 3 genişleyen kat; d_acc, ölçek katsayıları burada) | başlangıç + 1 y → F − 18 ay | ilk %50 |
| Kalibrasyon (aralık genişlik çarpanı; sonuçları tamamlanmış barlarla) | F − 18 ay → F − 12 ay | sonraki 3 ay |
| İç test (bir kez) | F − 12 ay → F | son 4 ay |
| **İleri gölge (bağlayıcı)** | F → F + ≥ 3 ay, otomatik sorgu takvimi | aynı |

- **İç test "hiç bakılmamış kasa" değildir** (§13): ilk bakış kaydı nedeniyle bağlayıcı kanıt ileri gölge dönemidir.
- Otomatik sorgu takvimi (ileri gölge): 1h/4h/1d her bar kapanışı, 30m her 2. bar, 15m her 4. bar, 5m her 12. bar.
  Kullanıcı tıklamaları ayrıca kaydedilir ama karneye girmez.
- Kısa TF'lerde iddia seviyesi bir alt sınıf (B → C) etiketlenir.

## 8. Tabanlar (hepsi aynı `eligible(t)` kümesinden)

1. Seans-kovası taban oranı / kantilleri (Y1–Y5).
2. "ATR + seans" büyüklük modeli (Y4: koşulsuz ATR-birimli kantiller, seans kovası başına).
3. Küçük geçmiş-oynaklık/trend regresyonu (ATR oranı, son H getiri, EMA50 uzaklığı → doğrusal/lojistik; geliştirmede kurulur).
4. R7 (ham son 7 mum) — piramit ve yol özetinin karşılaştırma tabanı.
5. "Yalnız bağlam" kNN (bağlam açık yapılandırmalar için).
6. Seans + oynaklık eşli rastgele komşular (aynı seans kovası ± 1 saat, ATR yüzdeliği ± 10 puan, aynı K).

## 9. Ölçütler

- Y1: Brier becerisi, kalibrasyon eğimi/kesişimi, güvenilirlik diyagramı.
- Y2/Y3/Y5: çok sınıflı log-loss becerisi; sınıf başına güvenilirlik; belirsiz sınırlarıyla.
- Y4: pinball becerisi (kantil başına + ortalama); nokta-bazlı %80 kapsama ve aralık genişliği.
- Pratik: kapsam (çekimser olmayan sorgu oranı), yıl/seans dağılımı, en iyi 5 gün hariç beceri, iki kronolojik yarı.
- Raporlama yönü ayrık (yukarı / aşağı tahminleri ayrı) — "korku döner coşku dönmez" asimetrisi.

## 10. Null ve plasebo

1. **Takvim-hafta kaydırması (yön/hedef):** her sorgu ve komşunun sonucu, k hafta sonraki aynı haftagünü + saatteki
   barın sonucuyla değiştirilir (k ~ U{4 … N_hafta − 4}, dairesel; eşleşen bar yoksa atlanır). Seans/haftagünü hizası ve
   sonuç otokorelasyonu korunur; şekil→sonuç bağı kırılır. ≥ 200 tekrar; **tüm seçim ailesi** her tekrarda yeniden
   değerlendirilir (maks-istatistik).
2. **Seans + oynaklık eşli rastgele komşu (büyüklük):** ATR–büyüklük bağı korunur, şekil bağı kırılır.
3. **Sentetik piyasa:** aynı oynaklık profilli, seans-blok bootstrap getiri serisi → boru hattının becerisi ≈ 0 olmalı.
Null tasarımının neyi koruduğu ve neyi kırdığı rapora yazılır.

## 11. Bağımsızlık ve belirsizlik

- Sorgular: değerlendirmede ≥ H aralıklı alt örnek anlamlılık için; tüm sorgular yalnız tanımlayıcı istatistikte.
- Raporlanan sayılar ayrı ayrı: ham K, Kish ağırlık etkinliği, bağımsız olay sayısı, farklı gün, farklı hafta.
- Blok bootstrap: blok uzunluğu ≥ max(H bar, 1 işlem günü); 1d/H = 20 için ≥ 4 hafta.

## 12. Geçme ölçütleri (sonuçlardan önce sabit)

- **Doğrulanmış (iç test):** beceri > 0 · blok-bootstrap P(beceri > 0) ≥ %95 · iki yarı > 0 · §8 tabanlarının tümünü geçer ·
  (ikincilse) aile maks-istatistiği p < 0,05 · Holm sonrası anlamlı (birincilde).
- **Kesinleşmiş (ileri gölge):** ≥ 100 bağımsız gölge tahmin · aynı işaretli beceri · %90 aralık sıfırı dışlar.
- Yalnız "kesinleşmiş" profil arayüzde renkli rozet alır; "doğrulanmış ama kesinleşmemiş" ayrı etiket (ör. "iç testte
  geçti, ileri doğrulama sürüyor").
- İşlem/kapı iddiası yalnız 2. KURAL kartıyla.

## 13. Önceki bakışların kaydı (E23)

| Çalışma | Veri / dönem | Örtüşme |
|---|---|---|
| PM, PM-2 | NAS100 1m/5m 2025-01→2026-10, 15m/30m 2023-10→2026-10 | NDX iç test ve geliştirme dönemlerinin tamamı |
| MK-01..05, pinbar | NDX/DAX/XAU/OIL 15m–1h, 2016→2026-10 | dört sembolün iç testi |
| NDX Kapı Dökümhanesi (GF) | NDX 1h 2016→2026, 30m 5 y, 15m 3,4 y | NDX tüm dönem |
| CORTEX | NQ günlük 2019–24 | NDX 1d kısmen |
| İşlem otopsisi (IO) | bot işlemleri 2026-06→10 | iç test son 4 ay |
Bu yüzden iç test "görülmemiş" sayılmaz; bağlayıcı kanıt ileri gölge dönemidir.

## 14. Değişiklik kaydı

| Tarih | Değişiklik | Gerekçe | Sonuç görüldü mü? |
|---|---|---|---|
| 2026-10-12 | Taslak oluşturuldu (Codex incelemesi §5 maddeleri işlendi) | — | hayır |
| 2026-10-12 | ChatGPT protokol incelemesi (`PROTOCOL_INCELEME_CODEX.md`, P1–P9) alındı; v0.3'e işlenmesi beklemede | — | hayır |
| 2026-10-12 | **Kullanıcı isteğiyle keşif testi** (`kaldirma_testi.py`): eşleşme kaldırma kurallarının (öz-çakışma, tekilleştirme, katı bağımsızlık, kabul sınırı) ileri sonuca etkisi, 4 temsil × 23 sembol×TF hücresi. **Her hücrenin son 7 ayı (iç test + kalibrasyon) dokunulmadı**; geliştirme dönemi artık 'görüldü' sayılır | kural eklemeden önce kanıt (kullanıcı: 'varsayımlara göre kural ekleme') | **evet — geliştirme dönemi** |
