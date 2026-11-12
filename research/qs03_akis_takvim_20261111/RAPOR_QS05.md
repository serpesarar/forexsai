# QS-05 — Ters mantık + genişleme: rapor (2026-11-11)

Ön kayıt `PROTOCOL_QS05.md` (+ EK-1 F1). Kod `qs05.py`, `qs05_f1.py`; sonuçlar `results/qs05*.json`. Deneme sayacı QS-03/04 + 4 (T1, T2, T3, F1).

## Özet
| ID | Fikir | Sonuç | Sınıf |
|---|---|---|---|
| **F1** | **Ayın son günü 15:30→16:00, R1 yönünde** (kapanış emri akışı) | kör US500 +13,5 / US30 +11,0 / US2000 +21,9 bp (P 0,99 / 0,99 / 1,00), Dukascopy NDX +19,2 (P 0,997); NAS100 +14,1; tüm günler aynı yarım saat ≈ 0 | **B−** |
| **T2** | Döngünün diğer ABD endekslerine genişlemesi | ETF 2002-26 Sharpe SPY 1,00 · DIA 0,95 · IWM 0,98 · QQQ 0,82; broker US500 +54 bp/ay Sharpe 1,03, US30 0,55, US2000 0,58; eşit ağırlık 0,72 > NAS100 0,69 | **genişleme kabul** |
| T1 | Ay ortası trend (R1'in tersi: D−10 ay içi ≥ ±%2 yönünde 3 gün) | yabancı 12/16 artı (p 0,038), 1990-2002 +9,7, broker +26,4 → ölçüt B− ama havuz yalnız +6 bp, bacaklar dağınık (uzun 8/16, kısa 10/16) | B− kâğıtta, **işlem değeri yok** |
| T3 | Uzun bacaklara VIX ≥ 18,4 boyut eğimi | fark üç dönemde artı (+25 / +62 / +39) ama 1,5× boyut Sharpe'ı 0,82 → 0,78 düşürüyor (E110); bacaklar arası ters (R1 uzun KEŞİF yüksek < düşük) | X |

## F1 — ayın son yarım saati (en net yeni bulgu)
Mekanizma: dengeleme emirleri kapanış (MOC) emriyle verilir; baskı son yarım saatte yoğunlaşır. Bulgu NAS100'de betimsel olarak
görüldü (+14,1 bp, P 0,993), sonra kör sembollerde ön-kayıtla sınandı.
| Sembol | F1 (n) | uzun bacak | kısa bacak | tüm günler 15:30→16:00 |
|---|---|---|---|---|
| NAS100 (keşif) | +14,1 (64) | +32,6 (21) | +3,2 (43) | +0,1 |
| US500 (kör, 2020→) | +13,5 (44) | +24,9 (12) | +9,2 (32) | −0,6 |
| US30 (kör) | +11,0 (64) | +24,9 (21) | +4,4 (43) | −0,2 |
| US2000 (kör) | +21,9 (64) | +38,6 (21) | +14,0 (43) | −0,6 |
| Dukascopy NDX 1m (farklı besleme) | +19,2 (32) | | | |
Not: F1, R1 tutuşunun (D−3 → D 16:30) içindedir — ek kazanç değil, **yoğunlaşmış hâli**: R1'in ~31 bp'sinin ~14'ü son 30 dakikada.
Kullanım: (a) yalnız 30 dk risk almak isteyen için tek başına kural; (b) R1 açıkken son yarım saatte ek lot. Sınırlar: aynı çağ
(2018-26), bağımsız dönem yok; sembol başına ~8 işlem/yıl → kart hacim ölçütü tek sembolde geçmez (dört sembol havuzu 236).

## T2 — genişleme
Döngü (R1 iki bacak + E2 uzun, sinyal SPY − TLT) ETF 2002-26'da dört fonun dördünde P 1,00; IWM işlem başına +98,7 bp en yüksek.
Broker 2018-26 ay başına: NAS100 +49,3 (Sharpe 0,69), **US500 +54,4 (1,03)**, US30 +30,2 (0,55), US2000 +43,5 (0,58). NAS100 ile
korelasyon US500 0,94, US30 0,75, US2000 0,72 → çeşitlendirme küçük (eşit ağırlık Sharpe 0,72). Akış S&P 500'e (dengeli fonların
asıl tuttuğu endeks) en temiz yansıyor; bot US500'ü işleyebiliyorsa NAS100 yanına ya da yerine aday.

## T1 — tersi mantık
Ay ortasında ay içi trend yönünde işlem: işaret istatistiği geçti ama +6 bp maliyet mertebesinde, QQQ 2002-26 (görülmüş) +9,9 P 0,73,
broker ikinci yarı −13. "Coşku dönmez"in ay ölçeğinde zayıf izi; ayrı kural olarak işlenmez.

## T3 — korku katmanı
Yüksek VIX'te döngü uzun bacakları ortalamada daha iyi, ama boyut büyütmek dalgalanmayı daha çok artırıyor → Sharpe düşüyor. Kabul edilmedi.

## Öneri
1. GÖLGE'ye (backlog'daki döngüye ek): F1 son yarım saat işareti + US500 döngüsü. 2. Canlı kararlar kullanıcıda.
3. Ay sonu ailesinde artık: R1 (B, kart 6/6) · E2 uzun (B) · döngü (kart 6/6) · F1 (B−) · küresel taşma (B−) · US500 genişleme.
