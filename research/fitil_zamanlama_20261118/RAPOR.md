# Büyük alt fitilden sonra giriş zamanlaması — ilk / ikinci giriş, ikinci mum, 5 dk mumlar (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/fz.py` (tetik, girişler, değerlendirici), `src/fz_run.py` (tarama, doğrulama),
`src/fz_oz_test.py`.

## Sonuç

**Kâr kapısı bulunmadı.** Ön kayıtlı 3 turda toplam 2.448 hücre denendi:
- AL 504 hücre,
- SAT 504 hücre,
- oynaklığa göre tetik 1.440 hücre.

Seçim yalnız 2018–21'de yapıldı. Dondurulan 11 aday 2021–26 kör TEST'te, DAX 2018–26'da ve NQ vadeli 2019–24'te sınandı.
Hiçbiri 8 ölçütün hepsini geçmedi. Ön kayda göre aile kapandı.

**En yakın aday (C) — 1 saatlik büyük alt fitil, ardından ilk iki 5 dk mum yeşil → AL:**
- Stop fitil dibi − %0,10, TP 2R, çıkış ertesi gün NY 16:00.

| | n | ort. R | not |
|---|---|---|---|
| KEŞİF 2018–21 | 80 | +0,300 | seçim |
| TEST 2021–26 (kör) | 73 | **+0,203** | küme P %92 (eşik %98); iki yarı +0,17 / +0,24; en iyi 5 hariç +0,07; plasebodan P %100 |
| DAX 2018–26 | 78 | +0,054 | P %68 (eşik %90) |
| NQ 2019–24 | 76 | +0,070 | |

Yılda ~9 işlem. TEST'te 2021 −0,67, 2026 −0,05. 8 ölçütün 6'sı tuttu; TEST ve DAX güven eşikleri tutmadı.

## Tur tur

| tur | ne | KEŞİF aday / plasebo %95 | kör sonuç |
|---|---|---|---|
| Z1 (AL) | tetik 1h / 3,5 sa (alt ≥ %0,50, üst ≤ alt/2) × 7 zamanlama × 2 stop × TP 1/2/3R × 1 sa / 4 sa / ertesi gün × VIX | 16 / 41 (şans) | ilk iki 5 dk yeşil: TEST +0,20, DAX +0,05, NQ +0,07 (6/8) · ilk 5 dk yeşil, VIX, 3R: TEST +0,18, DAX −0,01 · **ikinci giriş (ilk kırmızıdan sonra)**: TEST −0,17, DAX −0,10 |
| Z2 (SAT, ayna) | aynı tetik, ayna zamanlamalar | 1 / 133 (**şansın çok altında**) | TEST −0,14, DAX −0,23 |
| Z3 (AL, oynaklık tetiği) | alt fitil ≥ 1 / 1,5 / 2 × ATR14 | 146 / 144 (**ilk şans-üstü ızgara**) | 5 aday kör TEST'te −0,13…+0,01; DAX çoğu eksi → aşırı uyum |

## Ne öğrenildi

1. **Büyük alt fitilin bilgisi gerçek ve yönü yukarı.**
   - Fitilden sonra SAT, rastgele zamanda SAT'tan çok daha kötü: ızgarada 1 aday, plasebolarda 48–139.
   - AL tarafında en iyi zamanlamalar plasebodan iyi (P %100).
   - Ama bu bilgi mutlak kâra ancak sınırda dönüşüyor (≈ +0,05…+0,20R) ve piyasadan piyasaya tutarsız.
2. **"İlk girişte" bekleme kazandırıyor, "ikinci giriş" kaybettiriyor.**
   - Fitilden sonra ilk 5 dk mumların yeşil olmasını beklemek tutarlı en iyi zamanlama.
   - İlk geri çekilmeden sonra girmek (Z4) her yerde eksi: düşen bıçağı ikinci kez yakalamak.
3. **1 saatlik tetik 3,5 saatlikten iyi.** Daha sık, daha taze. 3,5 sa tetikte hiçbir zamanlama dondurulacak kadar iyi değildi.
4. **"İkinci mum" (aynı zaman diliminde teyit, Z5/Z6)** 5 dk teyitten iyi değil; FR-15'in 9 yıllık zayıflamasıyla (NX-01) tutarlı.
5. **Oynaklığa göre eşik KEŞİF'te güzel görünüp kör dönemde sıfırlandı.** Daha çok olay = daha çok ince ayar şansı = daha büyük
   aşırı uyum.

## Sınırlar

- MT5 broker beslemesi bu sınamada yok: 5 dk giriş için 2018–21 M1/M5 broker verisi yok. Bağımsız besleme olarak NQ vadeli 5 dk
  kullanıldı (5 dk çözünürlük, aynı mumda TP+SL → SL).
- DAX'ta kural aynen taşındı: NY saatleri, VIX. DAX'a özel uyarlama yapılmadı.
