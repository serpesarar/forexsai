# FAZ 1 — Hedef (etiket) tanımı ve taban oranlar (NOM, 2026-11-13)

Kod: `backend/services/nom/labels.py` (canlı notlama da bunu kullanır), `src/faz12_build.py`, `src/faz1_tick_check.py`.
Çıktı: `data/labels_{15m,1h,4h,session}.parquet`, `results/faz1_base_rates.csv`, `results/faz1_tick_ambiguity.csv`.
Ön kayıt: `PROTOCOL.md` §B (sonuçlardan önce yazıldı, değişiklik yok).

## Tanım (özet)
- Karar anı t = 1m bar kapanışı (5 dk ızgarası; 4s/seans için 15 dk). Giriş = t'de açılan barın açılışı:
  LONG ask + 1 puan kayma, SHORT bid − 1 puan. Bariyerler gerçek dolum fiyatından; LONG bid yolu, SHORT ask yolu.
- ATR birimi ufka göre (KAPANMIŞ barlar): 15dk→ATR14(M5) medyan 14,6 p · 1s→ATR14(M15) 27,3 p ·
  4s ve seans→ATR14(H1) 56,3 p.
- Aynı 1m barda TP ve SL → SL. Boşluk dolumu (bar bariyerin ötesinde açılırsa açılıştan). SL dolumu 1 p aleyhte.
- Zaman bariyeri: ufuk sonu son bar kapanışından çıkış (− kayma). R birimi = SL mesafesi.
- Etiketlenen karar sayısı: 15dk 320.402 · 1s 314.779 · 4s 104.369 · seans 29.457 (2021-12 → 2026-11-03).

## Taban oranlar (tüm dönem, sürtünme dahil)

| Ufuk | Yön | Geometri TP/SL | P(TP) | P(SL) | P(zaman) | EV (R) | Başabaş (TP vs SL) |
|---|---|---|---|---|---|---|---|
| 15dk | long | 1/1 | 0,183 | 0,512 | 0,305 | **−0,418** | 0,50 |
| 15dk | long | 1/1,5 | 0,207 | 0,288 | 0,505 | −0,278 | 0,60 |
| 15dk | short | 1/1 | 0,196 | 0,509 | 0,295 | −0,417 | 0,50 |
| 1s | long | 1/1 | 0,264 | 0,426 | 0,310 | −0,199 | 0,50 |
| 1s | long | 1,5/1 | 0,150 | 0,444 | 0,406 | −0,200 | 0,40 |
| 1s | long | 1/1,5 | 0,296 | 0,258 | 0,446 | −0,133 | 0,60 |
| 1s | short | 1/1 | 0,275 | 0,424 | 0,301 | −0,210 | 0,50 |
| 4s | long | 1/1 | 0,293 | 0,368 | 0,339 | −0,077 | 0,50 |
| 4s | long | 1,5/1,5 | 0,197 | 0,251 | 0,552 | −0,050 | 0,50 |
| 4s | short | 1/1 | 0,307 | 0,358 | 0,335 | −0,096 | 0,50 |
| seans | long | 1/1 | 0,366 | 0,402 | 0,231 | −0,040 | 0,50 |
| seans | long | 1,5/1,5 | 0,270 | 0,294 | 0,436 | −0,014 | 0,50 |
| seans | short | 1/1 | 0,364 | 0,408 | 0,229 | −0,066 | 0,50 |

(40 hücrenin tamamı `results/faz1_base_rates.csv`'de; yıl kırılımı aynı dosyada.)

**Okuma:**
1. **Her hücre negatif.** Rastgele anda açılan bir işlem, sürtünme yüzünden kaybeder. Sürtünme ATR'ye göre ne kadar
   büyükse kayıp o kadar büyük: 15dk'da (ATR M5 ≈ 15 p, gece spread 3,4 p + 2 p kayma ≈ 0,35 ATR) −0,42R;
   seans sonunda (ATR H1 ≈ 56 p) −0,04R. Yani **kısa ufuklu her olasılık, işlem için ancak sürtünmeyi aşacak kadar
   ayırt ediciyse değerlidir**; 15dk'da bunun için P(TP)'nin tabandan ~+20 puan sapması gerekir.
2. **Yıl kırılımı:** 1/1 EV her yılda negatif (15dk −0,20…−0,61; 4s −0,05…−0,15; seans −0,00…−0,14). Long ile short
   arasında belirgin asimetri yok (4s'te long −0,077 vs short −0,096 — boğa sürüklenmesi küçük).
3. **P(zaman aşımı)** geometriye ve oynaklığa güçlü bağlı (15dk 1,5/1,5'te %60) → modelin en kolay öğreneceği şey
   budur (DTS-03 ile tutarlı: oynaklık öngörülebilir, yön değil).
4. Bu tablo modelin yenmesi gereken **iklim tabanıdır** (Faz 4'te saat kovasına göre de ayrılır).

## Aynı-bar belirsizliği ve tick kontrolü (E57/E58)
- Belirsiz (TP ve SL aynı 1m barda) etiket payı: tüm hücrelerde **%0,0–0,1**.
- 2025 Oca–Haz Dukascopy tick'leriyle 436 belirsiz etiket: tick sırası 12 TP-önce, 59 SL-önce, 365 tick yolunda
  ikisi birden yok (1m bar ile tick akışı arasındaki küçük farklar). Muhafazakâr SL kuralının yarattığı EV yanlılığı
  en kötü hücrede **0,0013R** → ihmal edilebilir. 1m çözünürlük bu geometriler için yeterli.

## Sınırlılıklar
- 2018-2021 (2020 çöküşü) ve 2026-01-01→02-07 eksik (Faz 0 §4). Spread 2025 dışında modeldir.
- Seans ufku yalnız NY nakit saatinde tanımlı (09:30 → kapanış − 30 dk).
- Etiketler örtüşür (5 dk ızgarada 1s ufuk = 12 komşu satır aynı yolu paylaşır) → Faz 3'te arındırma + bağımsız
  karar sayımı zorunlu.
