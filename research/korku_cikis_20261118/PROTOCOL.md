# Ön kayıt — Korku gecesi çıkış türevleri + ikinci korku günü eklemesi (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "olan yapıyı geliştir, farklı yapılar bul".

## Gerekçe (defter 3. KURAL)
§2.71 K1 ve §2.75 S≥2 yalnız **16:00 → ertesi 16:00** ile sınandı; 09:30 çıkışı daha zayıftı ("toparlanmanın büyük kısmı ertesi
seansta"). Çok günlü tutuş ve koşullu çıkış hiç sınanmadı. C3b'de "ilk yükselen kapanışta çık" büyük iyileştirmeydi (§2.26).
KB-05 kısa TP X ("braket ≠ zaman") → burada yalnız zaman/koşul çıkışları. Yeni tanım = çıkış ailesi, tetikler aynen korunur.

## Tetikler (değişmez; `korku_birlesik_20261118/results/geceler_*.parquet` bayrakları)
- **K1** = T_k1 (16:00 TWAP'ın ≥ %0,5 altı ∧ 15:00→16:00 aşağı).
- **U2** = S ≥ 2 (dört korku tetiğinden en az ikisi).

## Çıkışlar (giriş d günü 16:00 ask; çıkış 16:00 bid; finansman takvim gecesi başına `lib.FIN_BP_PER_DAY`)
| kod | kural |
|---|---|
| X1 | d+1 16:00 (referans, mevcut kart) |
| X2 / X3 / X5 | d+2 / d+3 / d+5 16:00 |
| XU | d+1…d+5 arasında 16:00 fiyatı giriş fiyatının (ask) üstünde olan ilk gün; yoksa d+5 |
| XP | d+1…d+5 arasında 16:00 fiyatı bir önceki günün 16:00'ından yüksek olan ilk gün ("ilk yükselen kapanış"); yoksa d+5 |
| XT | d+1…d+5 arasında 16:00 fiyatı d gününün TWAP'ına (09:30–16:00) ulaşan ilk gün; yoksa d+5 |

2 tetik × 7 çıkış = 14 hücre. Tek pozisyon: açıkken gelen yeni tetik atlanır (Bölüm 2 hariç).

## Ölçüler
- İşlem başına net bp, **tetik − taban farkı** (taban = aynı çıkış kuralı tetiksiz her günden; uzun tutuşun NDX sürüklenmesini
  kazanç sanmamak için asıl ölçü budur), gün-küme bootstrap P (fark > 0).
- **Günlük portföy Sharpe**: tek pozisyon, 16:00→16:00 günlük piyasa değeri getirileri, boşta 0; yıllıklaştırılmış (√252);
  maxDD (bp), en kötü işlem.

## Seçim (yalnız ESKİ 2018-04 → 2021-10)
Her tetik için X1 dışındaki çıkışlardan, ESKİ'de (a) fark > X1'in farkı, (b) günlük Sharpe > X1'in Sharpe'ı, (c) fark P ≥ 0,90
olanlardan Sharpe'ı en yüksek **bir** çıkış dondurulur (tetik başına ≤ 1 → toplam ≤ 2 aday).

## Doğrulama (YENİ 2021-11 → 2026-11, kör + bağımsız beslemeler MT5 M30 / EET30 / NQ 5m, tüm dönem)
Dondurulan çıkış için:
1. YENİ: günlük Sharpe > X1'in YENİ Sharpe'ı **ve** fark > X1'in farkı **ve** fark P ≥ 0,975 (2 aday Bonferroni).
2. Beslemeler: 3 beslemenin en az 2'sinde Sharpe > X1 ve fark > X1 farkı.
3. Sürtünme: spread ×1,5 ile ortalama > 0.
4. Kuyruk: en kötü işlem X1'in en kötüsünün 1,5 katından kötü değil **ve** maxDD X1'in 1,5 katından kötü değil (TÜM).
Hepsi → **B (çıkış iyileştirmesi)**; 1+2 → C+; değilse X (X1 kalır).

## Bölüm 2 — İkinci korku günü eklemesi (seçimsiz, tek hücre / tetik)
Dondurulan çıkış (yoksa X2) ile pozisyon açıkken yeni tetik gelirse **ikinci birim** aynı 16:00'da açılır (en fazla 2 birim), kendi
çıkış kuralıyla kapanır. Ölçüt: eklenen birimlerin ortalaması ESKİ ve YENİ'de ikisinde de > 0 ve birinci birimlerin ortalamasından
düşük değil, portföy Sharpe iki dönemde de artıyor → **"ekle" taktiği C+** (n küçük beklendiği için en fazla C+). Değilse X.

## Sınırlar
Canlıya bağlama yok. Kart yalnız B çıkarsa güncellenir (SHADOW). Toplam hücre sayısı raporlanır.

## EK-1 (doğrulama sonrası, kesif/dogrula/ekle sonuçları görüldükten sonra yazıldı; seçimsiz)
Dondurulan XP çıkışı K1 tetiğiyle (GI-02'deki gibi değiştirilmeden) MT5 US30, US2000, US500 (2021→) M30'da: XP vs X1 ortalama,
fark ve günlük Sharpe. Ölçüt: 3 endeksin en az 2'sinde Sharpe(XP) > Sharpe(X1) → çıkış iyileştirmesi "piyasalar arası" notu.
Hükmü değiştirmez, yalnız güçlendirir/zayıflatır.
