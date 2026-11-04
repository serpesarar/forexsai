# Ön-kayıt — Alternatif benzerlik algoritmaları ile NDX yön tahmini (2026-10-13)

Sonuçlara bakılmadan yazıldı. Değişiklik olursa bu dosyanın sonuna tarihli not düşülür.

## Soru
Defterde elenmiş yöntemlerden (ME-02/ME-03: L∞ ikiz, ATR-ham 7 mum kNN, piramit-33; PM; OLD-13) FARKLI benzerlik aileleri,
NAS100 (NDX CFD) için +15 dk / +1 saat / +1 gün yönünü hep-çoğunluk, aynı-saat ve rastgele-komşu tabanlarından iyi tahmin ediyor mu?

## Veri ve kutsal dönem
- 1m/5m: `research/ndx_pattern_motifs/data/bars_{1m,5m}.parquet` (2025 Dukascopy), 15m: `bars_15m.parquet` (Pepperstone, 2023-10+),
  1h: `research/ndx_gate_forge/data/long_1h_utc.parquet` (Pepperstone, 2016-05+). Damgalar UTC bar başlangıcı.
- **HOLDOUT:** yükleme anında bar_bitişi < 2025-12-01 00:00 UTC olmayan her bar ATILIR (assert). Sonuç penceresi bu sınırdan önce biter.

## Hedef
- Karar anı t = sorgu barının kapanışı (bitiş damgası). Sonuç barı: bitişi ≤ t + h olan son bar; bitiş t + h ile birebir eşit olmalı
  (1m'de ≤ 4 dk tolerans), aynı segmentte (>4 gün boşluk yok). y = close(sonuç) − close(t) NDX puanı. Yön = sign(y); y = 0 sorgular atılır.
- Ufuklar h ∈ {15 dk, 1 saat, 1 gün (24 saat)}; TF ≥ h olan hücrede uygulanır (1h TF'de 15 dk yok) → 11 TF×ufuk hücresi.

## Sızıntı kuralları
- Komşu j yalnız te_j + h ≤ t ise (sonucu kapanmış); kütüphane = t'den önceki kayan 5 yıl (veri ne kadarsa).
- Komşu penceresi sorgu penceresiyle çakışmaz (j ≤ q − kapsam − 1).
- Seçilen komşular arası ≥ H_bar = h/TF bar (sonuç pencereleri çakışmaz), mesafe sırasıyla açgözlü.
- Normalizasyonlar yalnız pencere içi veya pencere-sonu öncesi (ATR = önceki 14 barın TR ortalaması; n-gram σ = önceki 100 getirinin std'si).
- Sorgular arası ≥ h (bağımsız olay): kısa set 1m/5m 60 dk, 15m 120 dk, 1h 480 dk; 1g seti 25 saat (saat döner). Isınma 1m/5m 60 g, 15m 90 g, 1h 365 g.

## Aileler (W ∈ {10,20,30,50}, K ∈ {20,50,100})
- **a** `zED`: z-normalize kapanış yolu, Öklid (MASS'e eşdeğer: kayan nokta çarpımı matris çarpımıyla birebir). **a2** `zED_amp`: + pencere menzili (maks yüksek − min düşük) sorgununkinin 0,5–2 katı.
- **b** `DTW`: z-yol, Sakoe–Chiba bandı r = max(1, round(0,1·W)); tüm havuzda LB_Keogh → en küçük 1000 LB (yetmezse ×4) → tam DTW → tekilleştir. Seçimin tam olduğu (100. komşunun DTW'si ≤ dışarıda kalanların LB'si) oranı kaydedilir.
- **c** `retcorr`: W log-getirinin Pearson korelasyonu, en yüksek K.
- **d1** `SAXyol`: z-yol → PAA w parça → alfabe a (Gauss kırılımları) kelime; tam kelime eşleşmesi, en yeniden geriye tekilleştir, en çok 200. (a,w) ∈ {(3,4),(3,8),(5,4),(5,8)}.
  **d2** `ngram`: bar getirisi / σ(önceki 100) → a sembol; son w sembol kelime (Markov n-gram), a ∈ {3,4,5}, w ∈ {4,6,8}. W kullanılmaz.
- **e** `NW`: ATR-normalize W bar getiri vektörü (Δclose/ATR), Öklid; tekilleştirilmiş en yakın 300 aday; Gauss çekirdeği, bant h_K = K'ncı komşunun mesafesi (sabit kural, sonuca bakmaz). Tahmin = Σw·(y/ATR)/Σw.
- **f** `cokolcek`: son 1,2,4,8,16,32 barın kümülatif getirisi ve menzili, ATR ve √s ile ölçekli (12 boyut), Öklid. W kullanılmaz.
- **ref** `refR7`: ME-02'nin ATR-ham 7 mum kNN'i (aynı sorgularda kıyas için). Aileye dahil (seçim düzeltmesinde sayılır).

## Karar kuralı
- R1 `tum`: komşuların yukarı payı > 0,5 → YUKARI, < 0,5 → AŞAĞI, = 0,5 çağrı yok. NW'de sign(tahmin).
- R2 `guclu`: |pay − 0,5| ≥ 0,20 (NW'de ağırlıklı yukarı payı). Geçerli oy en az 15.

## Tabanlar ve ölçütler
- Hep-çoğunluk: kütüphanenin (havuz [lo, hi0]) yukarı oranı → çoğunluk yönü. Aynı-saat: aynı UTC saatindeki (te saati) havuz oranı.
- Plasebo: aynı uygun havuzdan aynı sayıda rastgele komşu, 20 tekrar; "plaseboyu geçer" = model isabeti 20 tekrarın HEPSİNDEN yüksek.
- Fark = isabet − max(çoğunluk, saat) (çağrı yapılan sorgularda). Gün-blok bootstrap (h ≤ 1s → 1 gün, 1g → 7 gün blok), B = 2000.
- **ADAY ölçütü (hepsi):** ≥ 200 bağımsız çağrı · fark ≥ +2,0 puan · plaseboyu geçer · P ≥ 0,975 · iki kronolojik yarıda fark > 0 ·
  tahmin yönünde ortalama hareket > 1,5 puan · seçim düzeltmesi: maxT ayarlı p ≤ 0,05.
- **Seçim düzeltmesi:** sonuç (etiket) dizisi tam hafta kadar dairesel kaydırılır (saat/gün korunur; 1m+5m ortak kaydırma, 15m ve 1h ayrı),
  TÜM aile (her TF×ufuk×aile×W×K×kural) yeniden değerlendirilir, 200 tekrar. İstatistik: blok-t (fark / blok-SE), n ≥ 200 olan
  yapılandırmalar arasında maksimum. Gerçek en iyi, boş dağılımın %95'ini geçmeli. Ek: Bonferroni.
- Her yapılandırma `results/tum_yapilandirmalar.csv`'ye yazılır.

## Hesap sınırı
En çok 2 süreç, `nice`, toplam ≲ 90 dk.
