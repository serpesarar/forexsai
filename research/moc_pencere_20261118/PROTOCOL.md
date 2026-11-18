# Ön kayıt — Kapanış müzayedesi (MOC) penceresi: 15:50 → 16:00 düşüşü ve korku gecesi (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
§2.71 korku gecesi ABD endekslerinde var (GI-02). Aynı kurallar DAX, CAC ve Stoxx'ta yok (korku_kuresel_20261118, bu gün).
ABD'ye özgü aday mekanizma: **kapanış müzayedesi dengesizliği**. MOC dengesizliği 15:50'de yayımlanır, 16:00 kapanışına kadar
fiyatı dengesizlik yönünde iter. Bu itme geçici fiyat baskısıysa ertesi gün dönmelidir. Defterde 15:50 → 16:00 penceresi hiç
sınanmadı. GM-01 15:30 → 16:00 momentumunu sınadı; bu ise ertesi güne dönüşü soruyor. KSG ve K3 bütün son saati ölçüyordu.

## Veri
Dukascopy NDX 1m (seçim). Bağımsız: **MT5 NAS100 2m** (broker 1m geçmişinden, 2017-06 → 2026-11; `ndx_tf_yapilandirma_20261117/out/MT5`;
spread 0 ise 1,3 puan), NQ vadelisi 5m (2019-08 → 2024-08).

## Tanımlar (16:00 AL ask, çıkış bid, finansman takvim gecesi başına)
- M10 = P(16:00) / P(15:50) − 1. **M10↓(e):** M10 ≤ −e, e ∈ {%0,10, %0,20, %0,30}.
- K1 (§2.71, değiştirilmeden): P(16:00) ≤ TWAP(09:30–16:00) × 0,995 ∧ P(16:00) < P(15:00).
- Çıkış ertesi işlem günü 09:30 veya 16:00.

## Hücreler (9)
- A (6): M10↓(e) × 2 çıkış; taban = M10↓ olmayan günler.
- B (3): K1 gecelerinde M10↓(e) vs M10↓ olmayan K1 geceleri, ertesi 16:00 (doz: MOC baskısı korku gecesini güçlendiriyor mu?).

## Seçim (ESKİ 2018-04 → 2021-10)
n ≥ 25, tetik ort > 0, fark > 0, P ≥ 0,90; t'ye göre en iyi ≤ 3 hücre dondurulur.

## Doğrulama
1. YENİ (kör): fark > 0 ∧ P ≥ 1 − 0,10/3 = 0,967 (A için ayrıca tetik ort > 0).
2. MT5 2m ve NQ 5m (tüm dönem): ikisinde de fark > 0 (A için ayrıca tetik ort > 0).
3. A hücreleri için **K1'den bağımsızlık:** K1 olmayan gecelerde de fark > 0 ∧ P ≥ 0,90.
4. Sürtünme: spread × 1,5 ile tetik ort > 0.
Hepsi → B; 1+2 → C+; değilse X.

## Bilgi (seçimsiz)
Son saatin ayrıştırılması: 15:00 → 15:50 ve 15:50 → 16:00 ayrı ayrı ≤ −%0,2 / ≤ −%0,1 olan K3 geceleri; "müzayede ters döndü"
(15:00 → 15:50 ≤ −%0,3 ∧ M10 ≥ +%0,1) kümesi.
