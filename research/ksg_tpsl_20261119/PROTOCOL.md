# KSG — daha az zarar, daha çok kâr: gece içi TP/SL, sabah kurtarma, düşüşte ekleme, kapanış emri payı — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı isteği
"Bu strateji ile ilgili daha derin ve keskin araştırma yap — daha az SL yapıp daha fazla TP yaptırmak için."
KSG'nin TP/SL'si yok: 16:00 AL → ertesi 09:30 SAT. "SL" = eksi kapanan gece, "TP" = artı kapanan gece. İki ölçü AYRI raporlanır:
**isabet** (net > 0 gece payı) ve **beklenti** (gece başına net bp + kitap Sharpe). Hüküm yalnız beklenti/Sharpe ile verilir: isabeti
artırıp beklentiyi düşüren kural reddedilir (§2 vurkaç: "kısa TP isabet ↑ beklenti ↓").

## Defter kontrolü (tekrar edilmeyenler)
Giriş anı 543 özellik X (KA-01); kontrol saatinde zararda kes / kârda al X (KD-03, yalnız 20/00/03/06 kontrolleri); limit giriş, erken/geç giriş X
(KT-01); acil SL %6/%7 (NK-07); çıkış 09:30/09:32/09:45 (NK-07); 09:30→16:00 koşulsuz devam ≈ sinyalsiz (KT-01); son saat düşüş derinliği C (NX-07);
fitil B (FK); OPEX B (GX-05/06); olay gecesi C+ (OG-01).
**Sınanmamış (bu çalışma):** (T) gece boyunca bekleyen TP limiti + sürekli stop (kontrol saati değil, her mumda); (R) 09:30'da zararda olan geceyi
gün içinde tutmaya devam (kurtarma); (A) gece içi düşüşte ikinci birim ekleme; (M) 15→16 düşüşünün son 10 dakikadaki payı (kapanış emri satışı).

## Veri ve tanım
- KSG jenerik: d günü 15:00 ve 16:00 açılışları, 16:00 < 15:00 → 16:00 açılış + spread (ask) AL; çıkış sonraki işlem günü 09:30 açılışı (bid).
  Tatil/erken kapanış atlanır. Maliyet: spread + 1,756 bp/takvim günü finansman (her varyantta tam gece ücreti — TP'ye karşı muhafazakâr).
- Fiyat yolu: Duka NDX 1m (birincil, h/l bid), MT5 NAS100 M30 (ikinci besleme), kör MT5 US500 (2018-06+)/US30/US2000 M30.
  Bağımsız: U1 Duka M30 2016-04→2017-12 (dokunulmamış), EET30 30m 2016-11→2025-10 (bu soru için hiç bakılmadı), NQ vadeli 5m 2019-08→2024-08.
- Aynı mumda hem TP hem SL → SL (muhafazakâr). Stop dolumu min(stop, mum açılışı) (boşluk). TP dolumu limit fiyatı.
- KEŞİF ≤ 2021-10-31 (Duka), TEST sonrası. Bootstrap ay bloklu, NB 3000.

## Aileler
- **T (braket):** TP k ∈ {20, 30, 40, 60, 80, 120} bp × SL s ∈ {yok, 50, 100, 150, 250} bp, yoksa 09:30 → 30 hücre.
- **R (sabah kurtarma):** 09:30'da açık net ≤ −k (k ∈ {0, 30, 60, 100}) ise kapatma; tut → H ∈ {10:00, 10:30, 11:00, 12:00, 16:00} ya da
  **BE** (giriş fiyatına dönünce limitle çık, en geç 16:00). Kâr/eşikteki geceler 09:30'da kapanır → 24 hücre.
- **A (ekleme):** t ∈ {18:00, 20:00, 00:00, 03:00, 06:00} açılışında açık net ≤ −k (k ∈ {40, 80, 120}) → ikinci birim (ask), ikisi de 09:30 → 15 hücre.
  Ölçü: eklenen birimin getirisi ve iki birimli kitap Sharpe'ı. E116 karşı kolu: KSG-olmayan gecelerde aynı düşüş koşulu (betimleyici).
- **M (kapanış emri payı):** m = (o15:50 − o16:00)/(o15:00 − o16:00). Tek yönlü H: m ≥ 0,5 (düşüşün yarısından çoğu son 10 dk) > m < 0,5.
  Yalnız 1m/5m veride (Duka NDX, NQ).

## Seçim ve geçme (sabit)
- T, R, A: her ailede Duka KEŞİF'te tabana göre gece başına net farkı en yüksek **2 hücre** dondurulur (A'da iki birimli kitap Sharpe farkı).
  **B:** dondurulan hücre Duka TEST'te ve MT5 NAS100'de (tüm dönem) tabandan iyi, havuz (Duka TEST + MT5 + EET30 + NQ) eşli fark ay bloklu
  P ≥ 0,975 (Bonferroni 2 hücre); kör üç endeksin ≥ 2'sinde fark > 0; U1 Duka M30 ve EET30'da fark > 0; kitap Sharpe Duka ve MT5'te artar.
  **C:** TEST + MT5'te iyi ama havuz P < 0,975 ya da bağımsızlardan biri düşer. **X:** TEST'te ya da MT5'te tabandan kötü.
- M: **B** Duka KEŞİF ve TEST'te fark aynı işaret > 0, NQ'da > 0, havuz P ≥ 0,95. Aksi C/X.
- Isabet/beklenti tablosu tüm hücreler için betimleyici raporlanır (kullanıcı sorusunun doğrudan cevabı).
- Canlıya bağlama bu çalışmadan VERİLMEZ; B çıkarsa ayrı kart + kullanıcı kararı.

## EK-1 (ana sonuçlardan SONRA yazıldı; hükmü değiştirmez, yalnız sağlamlık/mekanizma)
Ana koşuda A(18:00, −40) C (U1 Duka M30'da 0 ekleme → bağımsız ölçüt sağlanamadı), R(−60, 16:00) C. Ölçülür:
(1) A: icra gecikmesi 18:05 / 18:15 / 18:30 (Duka 1m, NQ 5m; MT5/EET30 18:30), eşik komşuları −30/−50/−60, eklenen birim dağılımı (medyan,
isabet, en iyi 5 hariç), yıl yıl, bilanço gecesi örtüşmesi, U1'de 18:00 mumunun varlığı; 18:00 mumu spread'i vs 16:00 spread'i.
(2) R: E116 karşı kolu — KSG-olmayan gecelerde 09:30 net ≤ −60 → 16:00'a tutmanın 09:30→16:00 getirisi.
