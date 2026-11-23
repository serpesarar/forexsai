# KS — Korku sepeti risk defteri: canlı NAS100 kitabında çakışma ve ortak lot tavanı — RAPOR (2026-11-23)

- **Ön kayıt:** `PROTOCOL.md` (+ EK-1, sonradan, betimleyici).
- **Kod:** `src/veri.py` (bacak listeleri), `src/kitap.py` (tavan adayları, işaretleme, ölçüler, betimleme, KR-03), `src/ek1.py`.
- **Sonuç:** `results/ozet.json`, `results/ek1.json`, `results/atlanan_A0.csv`.
- **Koşma:** `../../.venv/bin/python src/kitap.py` (≈ 1 sn).

## Kitap
- **Kurallar:** NAS100'deki 8 canlı kural, canlı lot ve sürümleriyle: C3B, CAPREV-NDX (KQ-06 bölünmüş giriş, 0,4), ORB×VIX (TP 3R), ÇEKİÇ, KSG (OPEX vetosu + VIX ≥ 25'te çift lot), AY SONU, AY BAŞI, KORKU (T30).
- **Veri:** Dukascopy NDX 1m, 2018-01 → 2026-11, maliyet ve finansman dahil.
- **Ölçü:** her gün sonu 1m kapanışıyla işaretlenir.
- **Kaynakla birebir:** C3B 132 / +68,1 bp; ORB 741 / +0,199R; KSG vetodan sonra 879 / +8,0; KORKU 324 / +74,3; CAPREV 101 / +76,2. MT5: KORKU 309 / +73,9; KSG 888; CAPREV 101 / +78,7.
- **İkinci kitap (yarı bağımsız):** KORKU, KSG ve CAPREV MT5 NAS100'den, diğerleri Duka'dan. Gün sonu işaretlemesi yok; işlem sonucu çıkış gününe yazılır.

**Bugünkü kitap (A0):** toplam +81.473 $, aylık Sharpe 2,39.
- Maks. düşüş −5.108 $ (2025-03-24 → 04-06).
- En kötü gün −3.201 $ (2025-04-06, gümrük tarifesi şoku).
- En kötü 10 günün toplamı −17.857 $.
- 4,5 lot tavanı yalnız 35 işlemi atlatıyor (ORB 12, KORKU 7, KSG 6, ÇEKİÇ 5, CAPREV 5). Atlananlar ortalama +59,5 bp; kayıp 1.256 $.

## 1. Çakışma (betimleyici)

| gün sonunda açık korku kuralı | gün | gün başına ort $ | toplam $ | zararın payı | en kötü gün |
|---|---|---|---|---|---|
| 0 | 549 | +1 | +750 | %3,9 | −449 |
| 1 | 897 | +12 | +10.541 | %18,4 | −969 |
| 2 | 576 | +39 | +22.257 | %20,4 | −1.106 |
| 3 | 305 | +34 | +10.307 | %36,2 | −3.201 |
| 4 | 130 | +157 | +20.377 | %14,8 | −1.519 |
| 5 | 36 | +479 | +17.240 | %6,4 | −2.271 |

- **En kötü 10 günün hepsinde ≥ 2 korku kuralı açık** (ortalama 3,7). Zararın %57'si 3+ kuralın açık olduğu günlerden geliyor.
- **Ama aynı günler en kârlı günler de:** 4–5 kural açıkken gün başına +157…+479 $. Toplam kârın %46'sı bu 166 günden geliyor.
- Çakışma, kuyruğun da kenarın da kaynağı.

**Kim taşıyor:**

| kural | kâr payı | en kötü 10 gün zararındaki payı |
|---|---|---|
| C3B (2,0 lot) | %36 | **%57** |
| KORKU | %28 | %25 |
| KSG | %9 | %12 |
| CAPREV | %4 | %4 |
| ÇEKİÇ / ORB / AY SONU / AY BAŞI | %22 | %2 |

- Günlük $ korelasyonu: C3B–KORKU 0,61, KORKU–KSG 0,43, C3B–KSG 0,29.
- **Maks. düşüş penceresi** (2025-03-24 → 04-06): KORKU −2.122, C3B −1.849, KSG −1.186, ÇEKİÇ −323; CAPREV +81, ORB +290.
- **İşaretli ile gerçekleşen arasındaki fark:** Duka gerçekleşen kitapta maks. düşüş −2.783 $, işaretlide −5.108 $. Düşüşün yarısı açık pozisyonun ara zararı; pozisyonlar kapanmadan geri geliyor.

## 2. Tavan adayları (ön kayıtlı; Duka işaretli kitap)

| aday | toplam $ | maks. düşüş | en kötü gün | en kötü 10 | Calmar | Sharpe | ESKİ C/S | YENİ C/S | MT5 Calmar/S | K'ya göre fark $ | hüküm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A0 bugünkü** | 81.473 | −5.108 | −3.201 | −17.857 | 15,95 | 2,39 | 9,67/1,98 | 11,97/2,77 | 29,82/2,44 | — | — |
| A1 aile ≤ 2,5 | 65.167 | −3.986 | −1.863 | −13.831 | 16,35 | 2,52 | 11,09/2,16 | 11,91/2,87 | 24,06/2,55 | +1.584 | X |
| A1 aile ≤ 3,0 | 71.360 | −4.262 | −2.219 | −15.028 | 16,74 | 2,54 | 10,17/2,10 | 12,34/2,94 | 26,34/2,57 | +3.374 | X |
| A1 aile ≤ 3,5 | 76.363 | −4.622 | −2.575 | −16.171 | 16,52 | 2,52 | 9,75/2,02 | 12,28/2,96 | 27,44/2,55 | +2.635 | X |
| A2 çakışmada yarım lot | 55.635 | −3.342 | −1.824 | −11.532 | 16,64 | 2,51 | 10,22/2,01 | 12,42/2,95 | 24,44/2,55 | +2.321 | X |
| A3 = A1-3,0 ∧ A2 | 55.571 | −3.382 | −1.824 | −11.532 | 16,43 | 2,51 | 10,02/2,01 | 12,26/2,95 | 24,43/2,55 | +1.633 | X |

- **K (kontrol):** A0'ın bütün lotları tekdüze f ile küçültülür, f adayın maks. düşüşünü verecek kadar. "K'ya göre fark", aynı maks. düşüşte adayın K'dan fazla kazandığı $.
- Sharpe farkı için P(aday > A0): 0,73–0,93.
- **Ölçüt 1 (kuyruk ≤ %70):** yalnız A2 ve A3 geçti. A1'ler en kötü 10 günü %9–23 azalttı, ama maks. düşüş en iyi hâlde %78.
- **Ölçüt 2 (Calmar ≥ ×1,10):** hiçbiri geçmedi. Artış yalnız %2,5–5. Bu, aynı düşüşteki tekdüze lot küçültmesine göre 1,6–3,4 bin $ demek.
- **Ölçüt 3 (iki yarı + MT5):** hiçbiri geçmedi. ESKİ yarıda hepsi iyileşiyor; YENİ yarıda A1-2,5 kötüleşiyor. MT5 gerçekleşen kitapta hepsi A0'dan kötü (Calmar 29,8 → 24–27); Duka gerçekleşende de aynı (29,3 → 24–28).
  - Neden: gerçekleşen düşüş açık pozisyonun ara zararını görmüyor. Tavanın kestiği şey tam o ara zarar.

**Hüküm: 5 adayın 5'i X.**
- Tavanlar en kötü günü küçültüyor: A2'de −3.201 → −1.824 $, en kötü 10 gün −%35.
- Ama aşağı yukarı aynı oranda kârı da götürüyor (A2 −%32).
- Risk başına kârdaki küçük artış iki yarıda ve gerçekleşen kitaplarda tutarlı değil. Aynı kuyruk küçülmesi bütün lotları ×0,65'e indirerek de elde ediliyor.

## EK-1 — tek kuralın lotu ×0,75 (sonradan, betimleyici)

| kural | Δ toplam | Δ maks. düşüş | Δ en kötü 10 | Calmar | Sharpe | ESKİ C | YENİ C | MT5 C |
|---|---|---|---|---|---|---|---|---|
| (taban) | — | — | — | 15,95 | 2,39 | 9,67 | 11,97 | 29,82 |
| C3B | −%8,3 | −%7,4 | −%12,4 | 15,79 | 2,44 | 10,83 | 11,68 | 30,41 |
| KORKU | −%6,4 | −%10,4 | −%5,8 | 16,66 | 2,36 | 9,40 | 12,53 | 29,63 |
| KSG | −%2,5 | −%5,8 | −%3,0 | 16,52 | 2,34 | 9,50 | 12,43 | 29,46 |
| CAPREV | −%1,0 | +%0,4 | −%0,9 | 15,72 | 2,40 | 9,89 | 11,79 | 29,60 |
| ORB / ÇEKİÇ / AY SONU / AY BAŞI | −%0,9…−%1,9 | 0…+%1,4 | ≈ 0 | 15,4–16,1 | 2,37–2,39 | ≈ | ≈ | ≈ |

- Hiçbir tek kural Calmar ile Sharpe'ı iki yarıda birlikte iyileştirmiyor.
- **C3B'yi kısmak** en kötü 10 günü en çok azaltıyor (−%12) ama kâr da −%8. ESKİ'de iyileşiyor, YENİ'de kötüleşiyor.
- **KORKU'yu kısmak** düşüşü en çok azaltıyor (−%10) ama ESKİ'de kötüleşiyor.
- Kitap her yönde tekdüze lot küçültmesi gibi davranıyor. "Bedava" risk azaltan bir ağırlık yok.

## KR-03 senaryosu (betimleyici; gölgedeki koşullu ekleme kitaba eklenirse)
- 82 ekleme sinyali; 4,5 tavanı altında 59'u açılabiliyor. Ortalama +80,8 bp.
- Kitap toplamı +3.241 $ (84.714); maks. düşüş değişmiyor (−5.108); en kötü 10 gün −17.918 (≈ aynı); Calmar 15,95 → 16,59; Sharpe 2,39 → 2,46. İki yarıda da artı (ESKİ 9,67 → 9,80, YENİ 11,97 → 12,40).
- §2.110'daki "maks. düşüş ×1,6" uyarısı KORKU tek başınaydı. Kitapta kuyruğu C3B taşıdığı ve tavan en dolu günlerde eklemeyi engellediği için büyümüyor.
- Bu bir aday değil, karar da değil. Kitap düzeyinde zarar yazmadığını gösteriyor.

## Ne demek
1. **Korku ailesinde kuyruk, kenarın bedeli.** Kuralların çakıştığı günler hem en kötü hem en kârlı günler. Tavan ikisini birlikte kesiyor.
2. **Bugünkü 4,5 tavanı ucuz:** yalnız 35 işlem atlıyor, 1,3 bin $ kayıp. Daha sıkı tavanın getirdiği, aynı kuyruğu veren tekdüze lot küçültmesinden ancak %2–5 fazla; o da tutarlı değil.
3. **En kötü günü küçültmek istenirse** dürüst araç toplam lot kararıdır. Kitapta bütün lotlar ×0,65 → maks. düşüş ve en kötü 10 gün yaklaşık −%35, kâr −%35. KQ-08 ile aynı sonuç (§2.109).
4. Bu iş bitti; canlıya dokunulmadı. Kanıt sayısı: 5 aday + 1 kontrol + 8 EK-1 hücresi × 4 kitap (Duka işaretli, iki yarı, Duka gerçekleşen, MT5 gerçekleşen).

## Sınırlar
- **SOMA E2X3 NAS100 klonu** bu kitapta yok. Kural 2026-11-23'te, bu çalışma sürerken canlıya alındı (`98b85280`). Altın/endeks itki tarzı bir kural, korku ailesinden değil. Ama 4,5 sembol tavanını paylaşıyor; atlanan işlem sayısını artırabilir.
- **İkinci kitap yarı bağımsız:** beş kural iki kitapta da Duka'dan.
- **CAPREV günlük yolu yaklaşık:** gün sonu işaretlenir, stop ve kısmi kapanış çıkış gününe yazılır (toplam birebir).
- **Pazar günü sorunu:** en kötü gün olarak görünen 2025-04-06 Pazar. Bu, NY Pazar akşamı açılan vadeli seansının gün sonu işaretidir.
