# Korku gecesi çıkış türevleri + ikinci korku günü eklemesi (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/kc.py` (`kesif`, `dogrula`, `ekle`, `tasima`). Kart eki:
`backend/data/evolution/go_live_cards/ndx_korku_twap.json` → `cikis_alternatifi_XP` (SHADOW).

## Soru
Korku gecesi (K1 ve çift teyitli U2) yalnız "16:00 al → ertesi gün 16:00 sat" ile sınanmıştı. Çıkışı değiştirmek kuralı geliştirir mi?
2 tetik × 7 çıkış = 14 hücre. Seçim yalnız 2018–21'de yapıldı.

## Sonuç: "ilk yükselen kapanışta çık" (XP) — B, ama ılımlı
XP: sonraki 5 gün içinde 16:00 fiyatının bir önceki günün 16:00'ından yüksek olduğu ilk gün çık. Böyle bir gün yoksa 5. gün çık.
Ortalama tutuş 1,6 gün.

| | YENİ X1 (mevcut) | YENİ XP | TÜM X1 | TÜM XP |
|---|---|---|---|---|
| K1 ort. (bp) | +44,1 | **+68,9** | +53,2 | **+77,6** |
| K1 fark (tabana göre) | +47,2 | +62,4 (P 0,998) | +54,9 | +68,9 |
| K1 isabet | %57 | %74 | %60 | %77 |
| K1 günlük Sharpe | 1,23 | **1,35** | 1,41 | **1,52** |
| K1 maxDD / en kötü | −841 / −612 | −1.132 / −783 | −841 / −612 | −1.132 / −783 |
| U2 günlük Sharpe | 1,40 | **1,60** | 1,48 | **1,63** |

Beslemelerdeki Sharpe (XP / X1):
- K1: MT5 1,38 / 1,22 · EET30 1,37 / 1,30 · **NQ 0,94 / 1,48**
- U2: MT5 1,53 / 1,27 · EET30 1,49 / 1,32 · **NQ 1,12 / 1,75**

Ön kayıt ölçütlerinin dördü de geçti (YENİ, 3 beslemenin 2'si, sürtünme, kuyruk 1,5× sınırı) → **B**.

**Zayıflatan bulgular:**
- **EK-1 (seçimsiz taşıma):** K1 + XP, MT5 US30, US2000 ve US500'de işlem başına kazancı üçünde de artırıyor (+10…+24 bp). Sharpe ise
  yalnız US500'de artıyor (0,63 → 0,92). US30'da 0,73 → 0,70, US2000'de 0,82 → 0,80; maxDD de büyüyor.
- NQ vadelisinde Sharpe düşüyor.
- Kazancın bir kısmı uzun tutuşun sürüklenmesi: XP tabanı +7…+9 bp, X1 tabanı ≈ 0.

**Ne anlama geliyor:** Kaybeden geceyi ertesi gün kapatmak yerine ilk yükselen güne kadar beklemek, isabeti %60'tan %77'ye çıkarıyor
ve işlem başına kazancı artırıyor. Riske göre düzeltilmiş getirideki artış ise küçük (+0,1 Sharpe) ve her piyasada görülmüyor.
Kuyruk biraz büyüyor: en kötü işlem −612 → −783 bp.

Canlı kural X1 olarak kalır, XP gölge alternatiftir. Kullanıcı isabeti ve işlem başına kazancı önemserse XP seçilebilir; karar kullanıcıda.

## Diğer çıkışlar (bilgi, YENİ)
| çıkış | K1 Sharpe | K1 maxDD | açıklama |
|---|---|---|---|
| X2, 2 gün | 1,33 | −1.026 | XP'ye yakın |
| X3 / X5, 3 / 5 gün | 1,15 / 0,54 | −1.804 / −2.249 | Korku etkisi 1–2 günde tükeniyor; uzun tutuş yalnız sürüklenme + risk |
| XU (giriş fiyatını aşınca) | 0,93 | −1.406 | Kaybedeni çok uzun tutuyor (en kötü −1.644, ESKİ) |
| XT (TWAP'a dönüş) | 1,02 | −1.885 | Kaybedeni çok uzun tutuyor (en kötü −1.644, ESKİ) |

## Bölüm 2 — ikinci korku günü eklemesi: X
Pozisyon açıkken yeni tetik gelirse ikinci birim açıldı. Eklenen birimlerin ortalaması 16 durumun 16'sında artı ve ilk birimlerden
yüksek; örneğin DUKA K1 YENİ'de +118 bp, ilk birimlerde +69. Portföy Sharpe'ı ise ESKİ'de düşüyor: DUKA K1 1,73 → 1,71, U2
1,67 → 1,61. Sekiz besleme × tetik durumundan yalnız biri ön kayıt ölçütünü geçti → **X**.

Bilgi olarak: ikinci korku günü daha kötü değil. Pozisyon açıkken gelen tetiği atlamak bir şey kaybettirmiyor, eklemek de Sharpe
kazandırmıyor; yoğunlaşma riski kazancı yiyor.
