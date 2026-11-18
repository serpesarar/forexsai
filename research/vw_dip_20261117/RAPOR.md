# NASDAQ V / W dip sistemi — farklı giriş ve TP'lerle kâr kapısı araması (2026-11-17)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md) (+ EK-1 çok turlu arama kuralı, EK-2 sabit veri kaynağı, EK-3 tur 3). Kod: `src/`, yeniden
üretim `zsh calistir.sh`. Kart: `backend/data/evolution/go_live_cards/ndx_vw_w1b_vix.json`.

## Sonuç

Sisteminizi V ve W dip mantığıyla yeniden kurdum (büyük düşüş → dip → (ikinci dip) → yükseliş). Ön kayıtlı 4 turda toplam **1.128 farklı
giriş/TP/zaman/bağlam bileşimi** denendi. Seçim yalnız 2018–2021'de yapıldı; dondurulan 9 aday 2021–2026'da kör sınandı, sonra
MT5'te, plaseboda ve başka endekslerde.

**Önceden yazdığım tüm ölçütleri geçen kâr kapısı bulunmadı.** Ön kayda göre arama 4 turda durdu.

**En güçlü aday — önce SHADOW kartı yazıldı; DAX 2018–26 bağımsız doğrulamasında −0,015R çıkınca RED (§5):**

> **W dip + korku:** 3,5 saatlik alt fitil mumundan sonra **ikinci dip teyidinde AL**. Bağlam: son 2 günün tepesinden ≥ %1,5 düşüş ve dünkü
> VIX ≥ 18,4. Stop: iki dibin altı −%0,10. TP 2R. Çıkış ertesi gün NY 16:00.

| | n | ort. R | not |
|---|---|---|---|
| KEŞİF 2018–21 (seçim) | 90 | +0,312 | şans düzeyindeki ızgaradan seçildi |
| **TEST 2021–26 (kör)** | 145 | **+0,192** | küme P %94,9; iki yarı +0,21 / +0,17; en iyi 5 hariç +0,13 |
| **MT5 bağımsız 2022–26** | 100 | **+0,121** | |
| eşli plasebo (aynı saat, rastgele gün) | — | −0,07 | gerçek − plasebo P %99 |
| tek pozisyon | — | +0,20 | |
| aynı tanım, 3. gün 16:00 çıkışı (tur 3) | 145 | +0,117 | MT5 +0,07 |
| tam örneklem kartı (2. KURAL) | 235 | +0,238 | 6/6, ama seçim yanlılığı taşır |

**Neden canlıya uygun değil:**
1. Kör TEST P'si %94,9. Dört turda 9 aday sınandığı için birikimli Bonferroni %98,9 gerektiriyordu.
2. Seçildiği ızgara bütünüyle şans düzeyinde: gerçek veride 39 aday hücre, rastgele kaydırılmış girişlerde 0–51 (yüzdelik %80).
3. **2025 ve 2026'da iki beslemede de eksi** (TEST 2025 −0,05, 2026 −0,25; MT5 2025 −0,14, 2026 −0,37). 2022–24'te ise iki
   beslemede de güçlü artı (+0,28…+0,78).
4. Başka endekslere taşınmıyor: GER40 −0,01, US500 −0,56, US30 +0,18, US2000 −0,18.
5. Mekanizması CAPREV'e (korku günü dip alımı, canlı) çok yakın. Ondan bağımsız bir kenar olduğu kanıtlanmadı.

## 1. Ne denendi

**Çapalar (birinci dip L1):**
- Sizin 3,5 sa alt fitil mumu (alt ≥ %0,50, üst ≤ alt/2).
- Genel düşüş dibi: 2 günün en düşüğü, tepeden ≥ %1,5 aşağı, fraktal teyitli.

**Girişler:**

| kod | giriş |
|---|---|
| V1 | 3,5 sa kapanışında |
| V2 | 3,5 sa tepesinin kırılımı |
| V3 | ana kırmızı gövdenin üstünün geri alınması |
| VG | genel dipte fraktal teyidi |
| W·b | ikinci dip teyidi |
| W·a | boyun kırılımı |
| W·r | boyun geri-testi (tur 3) |

**Turlar:**

| tur | ne | hücre | KEŞİF aday | plasebo %95 | kör sınav |
|---|---|---|---|---|---|
| 1 | 8 giriş × düşüş {hepsi, ≥1,5, ≥3} × VIX {hepsi, ≥18,4} × TP {1,2,3,5R, yok} × zaman {4 sa, 24 sa, ertesi gün 16:00} | 720 | 39 | 48 | 5 aday → en iyisi 6/7 (yukarıdaki), diğerleri 2–6/7, hiçbiri geçmedi |
| 2 | zaman çıkışı 2/3/5 gün, yapı / felaket stopu, düşüş ≥3/5, VIX ≥18,4/22 | 192 | 1 | 1 | V3 5 gün: TEST −0,288, MT5 −0,280 → X |
| 3 | W'nin kendi hedefi: ölçülen hareket TP'si + boyun geri-testi | 216 | 8 | 13 | 3 aday: W1b 3 gün +0,117 (MT5 +0,07) 6/7; diğerleri X |
| 4 | bağımsız piyasa: tur 3'ün en iyi KEŞİF hücresi | — | — | — | GER40/US500/US30/US2000 4/4 artı, havuz +0,09R (n 167) ama her biri P %61–67; aynı hücre NDX TEST'te −0,02 |

Ek: 2017 (görülmemiş MT5 dönemi) yetersiz. VIX hiç ≥ 18,4 olmadı; ön kayıtlı hücrede yalnız 7 olay (+0,47R).

## 2. Ne öğrenildi

- **V (tek dip) kenarsız:**
  - Fitil kapanışında AL (V1), tepe kırılımı (V2) ve genel dipte AL (VG) hiçbir TP/zamanda kör TEST'i geçmedi.
  - Ana gövde geri alımı (V3) VIX ≥ 18,4'te TEST'te ≈ +0,02…+0,03 (P %66–70).
- **W (çift dip) en iyi aile, ama yalnız korku rejiminde (VIX ≥ 18,4):**
  - VIX'siz aynı W1b TEST'te +0,005 / −0,020.
  - Bu, defterin "korku döner" ilkesinin (CAPREV) bir başka hâli.
  - W'nin "ikinci dip" yapısı plasebodan iyi, ama mutlak kâr 2025–26'da söndü.
- **TP:** sabit 1R/2R, 3R/5R'den iyi. 5R hiçbir yerde tutmadı. Ölçülen hareket TP'si 2R'den iyi değil.
- **Zaman:** 5 güne uzatmak (tur 2) işe yaramadı. Kenar varsa ertesi gün 16:00'da.
- **Boyun kırılımı / geri-testi** ikinci dip teyidinden iyi değil (limit/kovalama maliyeti; defter §3-19).

## 3. Yöntem

- Veri: Dukascopy NDX 1m (lib.load_m1 sabit kaynak), ask = bid + spread. TP/stop 1m'de; aynı barda ikisi → stop. Uzunda gecelik
  finansman.
- Giriş, karar mumunun kapanışından sonraki ilk 1m açılışında. W yapısı yalnız kapanmış mumlarla (fraktal +2 mum teyit).
- Seçim yalnız KEŞİF'te. Izgara plasebosu: aynı girişler ±1–7 gün kaydırılır (aynı saat, aynı % stop, aynı çıkışlar), 20 kopya.
- Birikimli Bonferroni: k. turda TEST eşiği 1 − 0,10/K.
- Bağımsız: kutu MT5 NAS100 M15 (2022-08 → 2026-11-17, taze çekim), GER40 M15 2022→, US500/US30/US2000 M5 2025-06→.
- Birim testleri: `src/vw_oz_test.py` (TP, stop, aynı bar, zaman çıkışı, iyimser icra, giriş zamanı).

## 4. Sonraki adım (öneri)

Geçmişte daha fazla arama yeni bilgi üretmez. İleri gölge kaydı önerisi DAX doğrulamasından sonra geri çekildi (§5): kural bağımsız
8 yıllık piyasada sıfırın altında. Evrim Paneli backlog'undaki gölge kaydı maddesi (bl_fd4574a728) geçersizdir.

## 5. Son doğrulama — DAX 2018–2026 (EK-4, kural değiştirilmeden)

| kural | n | ort. R | P | iki yarı | plasebodan |
|---|---|---|---|---|---|
| W1b + VIX ≥ 18,4, 2R, ertesi gün 16:00 | 190 | **−0,015** | 0,44 | −0,04 / +0,01 | P 0,78 |
| W1b, 2R, 3. gün 16:00 (tur 3) | 225 | −0,086 | 0,18 | −0,19 / +0,02 | P 0,72 |

En iyi aday 8 yıllık bağımsız bir piyasada sıfırın altında. **Aile kapandı; kart RED** (SHADOW geri çekildi). İleri gölge önerisi de
geri çekildi: NDX'teki +0,19R tek piyasaya ve 2022–24'e özgü görünüyor.
