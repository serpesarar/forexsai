# QS-05 — Ters mantık + genişleme: ay ortası trend, diğer endeksler, korku katmanı — ön kayıt (2026-11-11)

Kullanıcı: "tam tersi mantıkla düşün / ters işlem aç / daha da genişlet, son bir kapı". Temel: ay sonu döngüsü (R1 D−3→D ters yön +
E2 uzun D→D+3), kart 6/6. Sonuçlar görülmeden yazıldı; 3 karar hipotezi (T1, T2, T3), deneme sayacı QS-03/04 + 3.

**Dürüstlük notu:** T1'in fikri QS-03 teşhisindeki ay içi profilden geldi (ay ortası sinyallerde ters yön kuralı eksiydi; yalnız-hisse
profilinde D−7…D−12 −15…−37 bp). O profil 2002-26 ABD verisiydi → T1 kararı **yalnız o veride olmayan** yerde verilir: ABD 1990-2002,
16 yabancı endeks (kendi ay içi getirileriyle), broker NAS100 2018-26 yalnız icra.

## T1 — Ay ortası trend (R1'in tam tersi: akışa karşı değil, trendle)
Mekanizma: ay ortasında zorunlu dengeleme yok; ay içi hareket trend takipçileri/"coşku dönmez" ile sürer (§3-2). Dengeleme ancak son haftada
gelir ve o zaman tersine çevirir.
- Sinyal D−10 kapanışında endeksin KENDİ ay içi getirisi m (önceki ay sonu → D−10). m ≥ +%2 → UZUN, m ≤ −%2 → KISA; tutuş D−10 → D−7
  (3 gün). Maliyet ETF/endeks 2 / 3 bp.
- Ölçüt (hepsi): (1) 16 yabancı endekste 1990-2026 tüm dönem: ≥ %60'ı artı ∧ işaret p ≤ 0,10 ∧ havuz > 0; (2) ABD ^GSPC 1990-2002 > 0;
  (3) broker NAS100 2018-26 net > 0. Üçü → **B−**; (1) → **C+**; diğer **X**. Bacaklar ayrı raporlanır.

## T2 — Döngünün diğer ABD endekslerine genişlemesi (broker)
- Aynı döngü (R1 iki bacak + E2 uzun, sinyal SPY−TLT) broker US500, US30, US2000 M30 (US500 2020→, diğerleri 2018-06→), icra 16:30 ET,
  maliyet `ortak.py` + swap. Uzun geçmiş: SPY, DIA, IWM 2002-26 (QS-03/04'te R1 dört fonda artıydı; E2 yalnız QQQ/SPY'da ölçüldü).
- Ölçüt: (1) IWM ve DIA 2002-26 döngü ort > 0, P ≥ %90; (2) broker US500/US30/US2000 üçünün de döngü ort > 0; (3) eşit riskli
  NAS100 + üç endeks portföyünün broker 2018-26 aylık Sharpe'ı NAS100 tek başına Sharpe'ından yüksek. Üçü → **genişleme kabul** (yeni semboller
  gölgeye); (1)+(2) → **C+**; diğer **X**.

## T3 — Korku katmanı (uzun bacaklar × VIX)
Mekanizma: zorunlu alış (R1 uzun: tahvil hisseyi geçti → fon hisse alacak) korkulu piyasada (VIX ≥ 18,4) gelirse "korku döner" ile üst üste
biner; E2 uzun da aynı.
- Önceki gün VIX kapanışı (sinyal günü, ^VIX 1990→). Katman: VIX ≥ 18,4 / < 18,4. R1 uzun ve E2 uzun ayrı ayrı.
- Ölçüt: yüksek − düşük farkı KEŞİF 2002-13, TEST 2014-26 ve 1990-2002'nin üçünde de > 0 (R1 uzun ve E2 uzun havuzu, QQQ/SPY; 1990-2002
  ^GSPC) ∧ düşük VIX katmanı da > 0 (filtre değil, boyut kuralı). Hepsi → **boyut eğimi kabul (1,5× yüksek VIX)**, portföy Sharpe'ı ölçülür
  (E110: Sharpe artmıyorsa kabul edilmez); diğer **X**.

## Betimsel
- D (son gün) gün içi: broker NAS100'de R1 işaretli D 09:30→15:30 ve 15:30→16:00 (kapanış emri akışı son yarım saatte mi?).

---
## EK-1 — Son günün kapanış yarım saati (F1), sonuç görülmeden (2026-11-11)
Betimsel bulgu (broker NAS100 2018-26, SONRADAN): ayın son günü D, R1 işaretli 15:30→16:00 +14,1 bp (n 64, P 0,993); 09:30→15:30 +25,4.
Mekanizma: dengeleme emirleri kapanış (MOC) emriyle verilir → baskı son yarım saatte yoğunlaşır.
- **F1:** D günü 15:30 ET'de R1 Δ (D−3'te hesaplanmış, |Δ| ≥ %2) yönünde gir, 16:00'da çık. Maliyet `ortak.py` (RTH max(spread, medyan)×1,5).
- Kör sınama (NAS100 dışı, aynı çağ): broker US500 (2020→), US30, US2000 (2018-06→); ek: Dukascopy NDX 1m 2021-11→ (farklı besleme).
- Ölçüt: üç kör sembolün üçü de > 0 ∧ havuz P ≥ %90 → **B−** (aynı çağ, bağımsız dönem yok); 2/3 → **C+**; diğer **X**.
- Kontrol: aynı yarım saat, sinyal olmayan ay sonları (|Δ| < %2) ve tüm günler (işaretsiz uzun) raporlanır.
