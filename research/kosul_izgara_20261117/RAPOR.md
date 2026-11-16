# Koşul ızgarası — giriş anı × tutuş × yön × seans/gün/VIX/EMA-SMA (2026-11-17)

Ön kayıt `PROTOCOL.md` (+ EK-1…3). Kod `src/grid.py` (işlem tablosu + ızgara + maxT), `src/grid_ek1.py`, `src/grid_ek2.py` (kör tekrar sayımı),
`src/ek3.py` (Pazartesi kartı + kontroller). Veri Dukascopy NDX 1m 2018-01 → 2026-11; VIX dünkü kapanış.

## Izgara
13 giriş anı (18:00, 20:00, 03:00, 08:30, 09:30, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 15:30, 16:00 ET) × 5 tutuş (60/120/240 dk, seans sonu,
1 gün) × AL/SAT × koşullar: VIX kovası (<15, 15–18,4, 18,4–25, ≥25), dünkü kapanış EMA/SMA 20/50/200 üstü/altı, dün yukarı/aşağı,
haftanın günü, açılış boşluğu, girişte fiyat günün açılışının üstü/altı; tekli + iki koşul kesişimi.

| tur | hücre | KEŞİF | en büyük t | maxT %95 eşiği | sonuç |
|---|---|---|---|---|---|
| ön kayıt | 23.994 | 2018–21 | 3,94 | 4,81 (perm ort 4,12) | seçilen 0 |
| EK-1 | 11.340 (tekli + VIX×diğer) | 2018–23 | 3,59 | 4,25 (perm ort 3,67) | seçilen 0 |
**Güç kontrolü:** iki dönemde doğrulanmış S4 (korku günü 12:00 açılış üstü → 15:55 AL) bu ızgarada t 1,3–1,6 → aile düzeyli maxT gerçek NDX
kenarlarını da eler (E141). Bu yüzden EK-2: KEŞİF en iyi 30 hücre → KÖR 2024–26 tekrar sayımı: **8/30 tekrar** (beklenen 3, binom p 0,008).

## Aday: Pazartesi Avrupa açılışından Salı'ya uzun (kart `go_live_cards/ndx_pazartesi_uzun.json`, 6/6)
Kural: Pazartesi 03:00 ET AL (ask) → Salı 03:00 ET SAT (bid), stopsuz, finansmanlı.
| ölçü | değer |
|---|---|
| n / ort / medyan / isabet | 413 / **+22,7 bp** / +19,2 / %57,1 |
| P (ay-blok) | 0,999 |
| yarılar · ESKİ / YENİ | +21,3 / +24,2 · +22,0 / +23,3 |
| spr×1,5 · 1 dk geç · en iyi 5 hariç · en kötü | +21,2 · +22,2 · +16,0 · −470 |
| yıllar | 2018 −30 · 2019 +4 · 2020 +104 · 2021 +13 · 2022 +7 · 2023 +28 · 2024 +13 · 2025 +35 · 2026 +37 (8/9) |
| gün plasebosu (aynı kural) | Sal +6,3 · Çar +4,9 · Per −3,1 · Cum −9,4 → P(Pzt > diğer) 0,999 |
| yan girişler | 08:30 +20,9 · 09:30 +24,0 |
| canlı kitaba 0,5 lot | aylık Sharpe 1,86 → 1,92 (P 0,85; ESKİ 1,69 → 1,67, YENİ 2,18 → 2,25) |
Sınırlar: ızgara kökenli (çoklu bakış) — kanıt KEŞİF iki yarısı + kör 2024–26; mekanizma belirsiz (GF-06 "Pazartesi SAT yok" ile aynı yön);
stopsuz, en kötü hafta −470 bp. **Sınıf B.** Canlı kararı kullanıcıda (öneri: önce gölge ya da küçük lot).

## Diğer
KI-05: VIX 18–25 ∧ ortalama üstü → 16:00 AL → akşam (18:00–18:30): +4,6…+5,1 bp; yeniden açılış artefaktı değil ama küçük, gece primi ailesi → C.
