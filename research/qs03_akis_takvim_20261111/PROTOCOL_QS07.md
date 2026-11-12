# QS-07 — Algoritma değişikliği: akışı strateji olarak değil KAPI olarak kullan — ön kayıt (2026-11-12)

Kullanıcı: "mantık algoritmanı bir tık değiştir, yeni trader hamlesi / kazanç kapısı". QS-03…06 ay sonu zorunlu akışını **tek başına
işlem** olarak sınadı (R1, E2, F1, son seans — kartlar 6/6). Değişiklik: aynı akış takvimini, botun ZATEN canlı olan uzun yönlü
kurallarına **kapı** (engelle / büyüt) olarak uygulamak. Usta trader kuralı: "zorunlu akışın tersine pozisyon taşıma, yönünde büyüt".
Canlı kuralların hepsi UZUN (C3b 2.0 lot, ORB×VIX 0.75, KSG 0.5, CAPREV, çekiç) → akış takvimi onların rüzgârını belirler.
Sonuçlar görülmeden yazıldı. Deneme sayacı: QS-03…06 17 + QS-07 3 (H1, H2, H3).

## Akış pencereleri (her ay; Δ = SPY − TLT ay içi, D−3 kapanışında; s: Δ ≥ +%2 → −1, ≤ −%2 → +1, arada pencere yok)
- **W1 son seans:** D 09:30 → 16:00, yön s (QS-06 GÜN+0, kart 6/6).
- **W2 son gece:** D 16:00 → D+1 09:30, yön −s (QS-06 GECE+1).
- **W3 ay başı:** D+1 09:30 → D+3 16:00, yön +1 yalnız Δ_D ≥ +%2 ise (QS-04 E2 uzun); değilse pencere yok.
Uzun işlemin akış puanı F = Σ yön_w · 1[işlem tutuşu w ile pozitif uzunlukta kesişir]. **RÜZGAR** F > 0 · **KARŞI** F < 0 · **NÖTR** F = 0.

## H1 — Akış kapısı (canlı uzun kurallar)
Veri ve işlem listeleri (kurallar birebir KT-01 motorlarından):
- **C3b günlük** (RSI2(kapanış) < 10 → kapanışta AL, ilk yükselen kapanışta SAT, ≤ 5 gün; maliyet 2 bp): QQQ+SPY 2002-08→2026-10 (ana),
  SPY 1993-03→2002-07 (bağımsız, sentetik tahvil Δ).
- **C3b broker** NAS100 M30 2018-06→2026-11 (15:30 serisi, `ortak.Mkt`), **KSG broker** NAS100 (15:00→16:00 < 0 → 16:00 AL → ertesi
  09:30), **ORB×VIX** Dukascopy 2021-11→2026-11 (`c_orb_islemler.csv`, kural "taban", VIX ≥ 18,4; gün içi).
Ölçütler:
1. C3b günlük 2002-26: ort(KARŞI) < ort(NÖTR) < ort(RÜZGAR); RÜZGAR − KARŞI > 0, işlem-bootstrap P ≥ %90.
2. C3b günlük 1993-2002: RÜZGAR − KARŞI > 0.
3. Broker üç kural (C3b, KSG, ORB×VIX): her birinde RÜZGAR − KARŞI > 0 (n küçük; işaret).
4. Portföy (E19/E110): kapı (KARŞI engelle) + büyütme (RÜZGAR 2×) her kuralın aylık Sharpe'ını düşürmez, C3b günlük 2002-26'da artırır.
Sınıf: 1–4 → **B** (canlı kurallara kapı, gölge) · 1 ∧ 2 → **C+** · 1 → **C** · diğer **X**.

## H2 — İtme → sönüm (iki aşamalı: akışı gör, sönümüne gir)
Mekanizma: zorunlu akışın fiyat etkisi geçicidir; sönüm, gerçekleşen itme kadar büyük olmalı. Sıradan günlerin aynı büyüklükteki
hareketlerinden DAHA FAZLA dönmeli (fiyat baskısı imzası).
- D'de gerçekleşen itme P = s · (C_D/O_D − 1) (bp, 16:00'da bilinir). Sönüm Y = −s · (O_{D+1}/C_D − 1).
- Sıradan gün kontrolü: ay sonu ±3 gün dışındaki her gün t, s_t = işaret(C_t/O_t − 1), P_t = |C_t/O_t − 1|, Y_t = −s_t · gece getirisi.
- Ölçüt (QQQ+SPY 2002-26 ve SPY 1993-2002 ayrı): (a) ay sonu eğimi β(Y~P) > 0; (b) ay sonu eğimi − sıradan gün eğimi > 0 (fark
  bootstrap P ≥ %90, 2002-26); (c) broker NAS100+US500 2018-26 ay sonu eğimi > 0. (a)–(c) 2002-26'da ve (a) 1993-2002'de → **B−**
  (KSG'ye ay sonu büyütme kapısı) · (a)+(b) → **C+** · diğer **X**.

## H3 — Çeyrek penceresi olgusu, bağımsız dönem (backlog bl: "Çeyrek dönümü penceresi")
QS-06 C'de sonradan görüldü: [Q−10, Q+15] (ay dönümü ve D−3…D+3 hariç) 2004-26'da ABD + 16 yabancıda ~+4,6 bp/gün yüksek; SPY 1993-2003'te
yok (görüldü). **Karar yalnız görülmemiş veride:** yabancı 12 endeks + GDAXI/N225/FTSE 1990-01→2003-12 (kendi takvimleriyle) ve
^GSPC/IXIC 1985-01→1993-01.
- Ölçüt: yabancı ≥ %60 piyasada fark (pencere − dışı) > 0, işaret p ≤ 0,10, havuz > 0; ^GSPC/IXIC 1985-93 ikisi > 0. → **B−** (gün takvimi
  kapısı adayı) · yalnız yabancı → **C** · diğer **X** (2004 sonrası çağa özgü).

---
## EK-1 (2026-11-12) — algoritmanın iki ek değişikliği, H1–H3 sonuçlarından sonra, H4/H5 sonuçları görülmeden
H1–H3 X. Ek bulgu (betimsel): ay sonu gecesi koşulsuz +12,3 bp (geceler +3,9); s = −1 +25,9 · s = 0 +10,7 · s = +1 −8,6; 2014-26 s = 0 +1,1 →
gece dönüşü akışın VARLIĞINA bağlı, gerçekleşen itmenin büyüklüğüne değil (H2'nin X'i bununla tutarlı: itme = akış + haber gürültüsü).

### H4 — Frekans: haftalık dengeleme
Mekanizma aynı, takvim haftalık: drift-tabanlı/haftalık dengeleyen fonlar (robo, bazı hedef-tarih fonları) varsa her haftanın son seansında
küçük bir R1/GÜN+0 kopyası görülmeli. 52 olay/yıl → yüksek güç.
- Hafta = takvim haftası; F = haftanın son işlem günü; sinyal F−1 kapanışında Δw = SPY (önceki hafta son kapanışı → F−1) − TLT (aynı).
  |Δw| ≥ %1 → sw = −işaret(Δw). Ay sonu D'nin D−3…D+3 aralığına değen haftalar ÇIKARILIR (R1 ile çakışmasın).
- İşlem H4a: F seansı 09:30→16:00, sw yönünde. H4b: F 16:00 → sonraki işlem günü 09:30, −sw yönünde (hafta sonu gecesi dönüşü).
- Veri: QQQ+SPY 2002-08→2026-10 (KEŞİF 2002-13, TEST 2014-26), SPY 1993-2002 (sentetik tahvil), broker NAS100+US500 2018-26.
- Ölçüt (H4a ve H4b ayrı): KEŞİF ve TEST net (−2 bp) > 0, TEST P ≥ %90; 1993-2002 > 0; broker iki sembol ortalaması > 0 → **B−**;
  KEŞİF ∧ TEST > 0 → **C**; diğer **X**.

### H5 — Yerel akış: Avrupa hisse/tahvil farkı → DAX
- Tahvil: ECB AAA euro bölgesi 10Y spot faiz (günlük, 2004-09→), sentetik getiri y_{t−1}/252 − 8·Δy. Hisse: ^GDAXI (yerel).
- DAX takvimiyle D, D−3; Δ_EU = DAX ay içi − Euro tahvil ay içi (D−3 kapanışı). Kural: Δ_EU ≥ +%2 → KISA, ≤ −%2 → UZUN, DAX kapanışı
  D−3 → D kapanışı (3 bp). Ek: son seans D açılış → kapanış.
- Ölçüt: (1) KEŞİF 2004-14 ve TEST 2015-26 ikisi > 0, havuz P ≥ %90; (2) pencere getirisi ~ Δ_EU + Δ_US regresyonunda Δ_EU katsayısı
  iki dönemde < 0, t ≤ −1,5 (ABD sinyalinin ötesinde yerel bilgi); (3) broker GER40 2018-26 (D−3 11:30 ET → D 11:30 ET, Xetra kapanışı) > 0.
  1–3 → **B−** (GER40 kapısı) · (1) → **C** · diğer **X**.

---
## EK-2 (2026-11-12) — Avrupa son seansı, H4/H5 sonuçlarından sonra, bu sınama görülmeden
H4 X (Cuma seansı haftalık farkın YÖNÜNDE gidiyor → dengeleme aylık takvime kilitli; R1 için negatif kontrol). H5 C: Δ_EU, DAX'ta Δ_US'nin
ötesinde bilgi taşımıyor; ama ön-kayıtlı EK ölçümünde DAX son seansı (D açılış → kapanış, s yönünde) KEŞİF +20,1 (P 0,957), TEST +17,0 (P 0,982).
DAX bu yüzden artık GÖRÜLMÜŞ; karar görülmemiş Euro bölgesi endekslerinde.
- **H6 Avrupa son seansı:** her endeks kendi takviminde D; Δ_loc = endeks ay içi − Euro AAA 10Y sentetik tahvil ay içi (D−3 kapanışı);
  s = −işaret(Δ_loc) (|Δ_loc| ≥ %2). İşlem: D günü açılış → kapanış, s yönünde, 3 bp. Yahoo açılışı geçersizse (önceki kapanışa eşit) gün atlanır.
- Kör endeksler: ^FCHI, ^AEX, ^IBEX, ^STOXX50E; dönem 2004-10 → 2026-10.
- Uygulanabilirlik: broker GER40 M30 2018-06→ son seans 03:00 → 11:30 ET (Xetra 09:00 → 17:30 CET; DST uyumsuz haftalarda 1 saat kayar), maliyet
  `ortak.py`, s DAX'ın Δ_EU'sundan.
- Ölçüt: (1) dört kör endeksin ≥ 3'ü artı ∧ havuz (piyasa eşit ağırlık) P ≥ %90; (2) broker GER40 > 0. 1 ∧ 2 → **B−** (GER40 son seans
  kapısı, gölge) · yalnız 1 → **C+** · diğer **X**.
