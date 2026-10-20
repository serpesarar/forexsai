# ME-09 — Kullanıcı tanımlı "dalgalı tepe aralığı" şablon benzerliği — sonuç (2026-10-19)

Ön-kayıt: `PROTOCOL.md` (ileri getiriler hesaplanmadan yazıldı). Betikler: `ortak.py`, `sablon_dogrulama.py` (adım 1, şekil),
`etiketleme_gorseli.py` (adım 2, görsel), `sonuc_testi.py` (adım 3, **bir kez** koşuldu; koşumdan sonra yalnız `run_cells`'e
varsayılanı değişmeyen `pct_sim/pct_non` parametresi eklendi), `ek_tanilama.py` (sonradan tanılama, başarı ailesini değiştirmez).
Çıktılar `results/`. Veri: NDX CFD 1h 2016-05-29 → 2026-10-02 04:00 UTC; DAX CFD 1h 2020-01 →.

## 1. Ölçü üç şablonu birbirine benzer görüyor mu? — Çoğunlukla HAYIR
Şablonlar (kullanıcının günleri, UTC gün sınırı): T1 07-06→07-21 (276 bar, 14 gün), T2 07-17→07-29 (207 bar, 11 gün),
T3 08-13→08-20 (138 bar, 7 gün). L = {166, 207, 248}. Eşik %2 → D 3,63 (şekil korelasyonu r ≥ 0,897); %5 → D 4,14 (r ≥ 0,866).

| Çift | r (tam aralık) | şablon başına D dağılımında dilim | not |
|---|---|---|---|
| T2–T3 | 0,87 | %2,8 / %2,8 | sınırda benzer |
| T1–T2 | 0,68 | %7 / %18 | benzer değil |
| T1–T3 | 0,44 | %24 / %32 | benzer değil |

- Dedektör tarzı (her şablonun son barında diğer ikisiyle): T1 %17, T2 %2,9, T3 %11. **Kendini tanıma** (kendi sonunda, f=1):
  T2 D 1,90 (dilim %0) ✓; **T1 %16 ✗** (en yakın T3), **T3 %17 ✗** (en yakın T2) — T1 (276 bar) ve T3 (138 bar) pencere
  ızgarasının (166–248) dışında kalıyor; pencere 1–2 gün kayınca dalgalı yolun z-şekli değişiyor.
- Görsel sınırlarla (elips kenarları) tablo yer değiştiriyor: T1–T3 r 0,78 (%1,9–3,3), T2–T3 0,59, T1–T2 0,67 → benzerlik sınıra duyarlı.
- Farklar: süre 14/11/7 gün; aralık %5,8/%7,9/%3,9; net −%1,9/−%5,2/−%1,8; %1 zigzag bacağı 10/17/2 (%0,5'te 24/32/8);
  1h oynaklık 25/38/20 bp (207-bar oynaklık ondalığı 5/8/3); dip konumu 0,80/0,99/0,97 (T1 toparlanarak bitiyor); tepe önceki
  20 günün zirvesine göre −%2,7/−%4,9/+%1,0 (yalnız T3 yeni tepe). Ortak olan nitel (tepe yakınında oynaklık + düşüş), yol şekli değil.

## 2. Etiketleme görseli — `tur1_etiketleme.png`
En benzer 12 çakışmasız bölge (her 2 saatte biten pencere, sonrası gösterilmiyor; liste `results/tur1_secilenler.csv`):
#1 2021-09-22→10-01 (T3, r 0,97) · #2 2024-08-28→09-09 (T3) · #3 2021-09-02→09-15 (T2) · #4 2020-08-28→09-09 (T3) ·
#5 2022-10-03→10-12 (T3) · #6 2018-12-07→12-24 (T2) · #7 2022-04-29→05-12 (T3) · #8 2022-04-18→04-27 (T3) ·
#9 2020-02-14→02-28 (T2) · #10 2020-02-28→03-12 (T3) · #11 2023-12-26→2024-01-05 (T2) · #12 2018-06-19→06-28 (T3); r 0,93–0,97.
**Hiçbiri T1'e en yakın değil**; çoğu "yükseliş/düzlük → dipte biten düşüş" (birkaçı sakin başlangıçlı: #9, #11) — kullanıcının
etiketi ölçünün onun gözünü yakalayıp yakalamadığını gösterecek.

## 3. Ön-kayıtlı test — NDX geliştirme (2016-06 → 2025-11), %2 eşik, kıyas = getiri+oynaklık eşli benzer-olmayan günler
Her hücrede 48 benzer gün; 28–41 olay. Fark = benzer − eşli taban (bp); P↓ = ay-blok P(fark < 0).

| Aşama (olay) | +1 saat | +1 gün | +5 gün | kalan |
|---|---|---|---|---|
| 1/3 (35) | +6,5 (P↓ 0,004) | **+33,6 (0,002)** | −21,4 (0,72) | +4,7 (0,44) |
| 1/2 (41) | +4,2 (0,06) | −18,7 (0,87) | **−63,2 (0,974)** | −54,0 (0,96) |
| 2/3 (40) | −5,5 (0,85) | +17,0 (0,15) | −19,5 (0,58) | −22,9 (0,63) |
| tam (28) | **+14,3 (0,018)** | −21,4 (0,68) | +2,8 (0,47) | — |

- **Ön-kayıtlı yön (aşağı): 0/15 hücre geçti.** En yakını 1/2 +5 gün: −63 bp, P↓ 0,974 (eşik 0,975; MC hatası ~0,002), yarılar
  −117/−18, 41 olay, medyan −51, %56 negatif, en negatif olay hariç −52, plasebo dilimi %8 → (a)'yı kıl payı kaçırdı; güçlü değil.
  Sağlam da değil: %5 eşikte −25 (P 0,86), görsel sınırlarla −12 (0,65), DAX'ta −10 (0,61).
- **Karşı yön (yukarı, ön-kayıt dışı):** 3 hücre tek-hücre ölçütlerinin hepsini sağlıyor — 1/3 +1s (+6,5, P↑ 0,996, olay %60 +),
  1/3 +1g (+33,6, P↑ 0,998, yarılar +23/+40, 35 olay medyan +32, %71 +, en iyi olay hariç +23), tam +1s (+14,3, P↑ 0,982, yarılar
  +16/+13, 28 olay medyan +9, %75 +, en iyi hariç +8; plasebo dilimi %99). İki yönlü Bonferroni (P ≥ 0,99917) hiçbirinde yok →
  protokole göre "aday (C)". Sonradan tanılamada **dağılıyor:** DAX'ta üçü de ters işaretli (−3,7 / −18,5 / −18,7 bp); %5 eşikte
  +3,4/+15,6/+4,0 (P↑ 0,83/0,95/0,84); görsel sınırlarla −0,8/+26,4/−0,6; aile düzeyi plasebo: gerçekteki "plasebonun %95'i
  üstünde 2 hücre" rastgele şablon üçlülerinin %20'sinde, en uç dilim (%98,8) %16'sında görülüyor; olay medyanlarında 2 üst + 2 alt
  uç hücre (simetrik, E26). Etkinin tamamı T3 benzerlerinden (şablon-başına: T3 tam +1s +19,5 P↑ 0,999; T1/T2 dedektörlerinde yok).
  Doğrulamada 1/3 hücreleri ters (4 gün: −14 / −42 bp). +1 saat ufku 20:00 barının kapanışından sonraki bar = 22:00 (günlük ara)
  ya da Cuma'da Pazar açılışı — "saatlik" değil, ara/hafta sonu boşluğu.
- "Oluşurken fiyat ne yaptı" (tam eşleşmelerin penceresi, tanımlayıcı): medyan net −%5,0 (çeyrekler −%8,0 / −%2,9), medyan aralık
  %8,6; 48 günün 34'ü (%71) üst 4 oynaklık ondalığında; en yakın şablon T2 23, T3 25, **T1 0**. Yani dedektörün bulduğu "tamamlanmış
  yapı" pratikte 1–2 haftalık sert düşüş (T2 tipi), T1'in dalgalı-yatay hâli değil.
- Kalan süre (kısmi): 1/3 kalan +4,7, 1/2 kalan −54 (P↓ 0,96), 2/3 kalan −23 (0,63) → yapı oluşurken geri kalanın yönü tabandan ayrışmıyor.

## 4. Bağımsız piyasa (DAX 2020-01 → 2025-11) ve doğrulama
- DAX: 31 benzer gün/hücre, 14–29 olay. NDX'te geçen hücre yok → teyit edilecek bir şey yok. DAX'ta aşağı yönde tek P ≥ 0,975
  hücresi 2/3 +1s (−13 bp, P↓ 0,975, 23 olay, medyan −3, %61 negatif) — NDX'te aynı hücre −5,5 (0,85); 15 hücrede 1 isabet
  tesadüf beklentisi (0,4) düzeyinde. DAX benzer günlerinin %26 (1/3) / %48'i (tam) NDX benzer günlerine ±3 gün yakın → kısmen aynı olaylar.
- Doğrulama (NDX 2025-12 → 2026-10, şablonla çakışan sorgular hariç): 168–182 uygun gün, hücre başına **0–4 benzer gün**
  (tam: 2026-06-10/11 tek olay, +35 / +199 / +324 bp; 1/3: 4 gün, −14 / −42 / −100 / −45 bp; 2/3: 0) → güç yok.

## 5. Bugün (son bar 2026-10-02 04:00 UTC)
D yüzdeliği: 1/3 %53 (en yakın T3), 1/2 %44 (T2), 2/3 %64 (T1), tam %47 (T3) → **yapı oluşmuyor** (eşik %2/%5). Son 60 sorgu
gününde %2 benzerlik yalnız şablonların kendi dönemi içinde (Temmuz–Ağustos, kendine eşleşme); Eylül'de yalnız %5 düzeyinde
dağınık günler (1/3: 09-03, 09-21, 09-23; 1/2: 09-23; 2/3: 09-02). Veri 2026-10-02'de bitiyor; 19 Ekim için söz söylenemez.

## 6. Okuma
- Kullanıcının üç örneği bu ölçüde **tek bir şekil değil**: yalnız T2–T3 sınırda benziyor; T1 ne diğerlerine ne de dedektörün
  kendi pencere ızgarasına uyuyor. Birleşik min-D dedektörü pratikte "1–2 haftalık oynak düşüş" (T2/T3) dedektörü.
- Ön-kayıtlı "tepe → düşüş devam eder" iddiası **desteklenmedi** (0/15). Ters yöndeki üç hücre (kısa vadeli yukarı) seçim
  düzeltmesi, DAX, eşik ve sınır değişikliği karşısında dağılıyor → kenar yok (X). Tek tutarlı tanımlayıcı gözlem: eşleşen
  pencereler yüksek oynaklıkta ve sert düşüşle bitiyor — bu tanım gereği.
- Sonraki tur için (yeni tanım gerekir, aynı veriyle tekrar değil): şablon başına kendi uzunluğunun 0,8–1,2 katı pencereler +
  şekil yerine nitel özellikler (bacak sayısı, tepe/zirve uzaklığı, oynaklık) — kullanıcının "aynı yapı" dediği şey bunlar;
  önce kullanıcının `tur1_etiketleme.png` etiketleri.
