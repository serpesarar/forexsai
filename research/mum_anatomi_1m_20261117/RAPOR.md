# 1m mum anatomisi — gözle keşif → algoritma (2026-11-17)

Ön kayıt `PROTOCOL.md` (+ EK-1). Kod `src/draw.py` (1m mum çizici, gözle inceleme), `p1_orb.py`, `p23.py`, `p1_ek1.py`.
Veri Dukascopy NDX 1m 2018-01 → 2026-11 (`research/ndx_10y_1m_20261116` motoru). Grafikler `charts/` (git dışı; `draw.py <tarih>` ile yeniden üretilir).

## Yöntem: önce bak, sonra say
Sekiz gün çizildi ve incelendi (tam seans: 2020-03-12 panik, 2023-07-18 trend, 2024-08-05 VIX sıçraması, 2019-05-13 düşüş; ORB × VIX sabahları:
en iyi 2026-04-02 / 2022-05-26, en kötü 2024-10-24 / 2018-02-28). Gözle görülen üç yapı sayıya çevrildi ve sonuçlara bakmadan ön kayda yazıldı:
G1 itki bacağı (sıkışmadan çıkan devam, uzamanın ucundaki döner), G2 temiz vs dağınık kırılım, G3 uçta ret fitili.

## Sonuçlar
| ID | soru | sonuç | hüküm |
|---|---|---|---|
| AN-01 | P1 ORB × VIX (TP 3R) içinde kırılım anatomisi: kapanış konumu, son 5 barda üst fitil, renk değişimi (öngörülü) + ardışık yeşil dizi (öngörüsüz); KEŞİF 2021-26, TEST 2018-21 | Öngörülen üçü KEŞİF'te ters/boş, seçim maxT p 0,92 → **geçmedi**. Ama iki dönemde tutarlı iki iz: **f_run ≥ 3** (girişe ≥3 ardışık yeşil 1m) +0,30 vs +0,13R / TEST +0,37 vs −0,00R (P 0,83 / 0,97); **f_uw5 yüksek (üst fitil fazla) daha iyi** +0,28 vs +0,05 / +0,33 vs −0,01R — sezginin TERSİ | ön kayıt X · iz C |
| AN-02 | EK1-a kitap dozu (ORB lotu iyi anatomide ×1,5, ortalama sabit) | f_run: YENİ Sharpe 2,18 → 2,31 (P 0,98), ESKİ 1,69 → 1,67; f_uw5 ve "biri" aynı desen → iki dönem şartı tutmadı | X (doz) |
| AN-03 | EK1-b mekanizma: üst fitil = OR tepesi önceden yoklandı mı? | Korelasyon 0,10; az yoklanan kırılım daha iyi (0–1 yoklama +0,32 / +0,33R) — "ikinci deneme" açıklaması tutmadı | X (mekanizma) |
| AN-04 | EK1-c en kötü hücre (f_run ≤ 1 ∧ düşük üst fitil) veto mu? | YENİ −0,01R (n 69), ESKİ +0,09R (n 63) | X (veto) |
| AN-05 | P2 itki bacağı (≥4 ardışık aynı renk, CLV ≥ 0,7/≤ 0,3, hareket ≥ 4×a60), 30 dk; sıkışma → devam / uzama → ters | sıkışma devam KEŞİF +0,2 / TEST −0,4 / BAĞIMSIZ −3,6 bp; uzama ters −5,6 / +0,0 / +2,5; tümü devam +0,9 / −0,7 / −2,3; plaseboyu geçen yok | **X** — gözle görülen ayrım tek örnekteydi |
| AN-06 | P3 1m aşırı fitil reddi (fitil ≥ 6×a60, pay ≥ 0,6) | 9 yılda 8 olay (eşik çok uçta) | sınanamadı (eşik gevşetilmedi: sonradan seçim olurdu) |

## Hüküm ve uygulama
Gözle seçilen 1m yapıların hiçbiri tek başına işlem kuralı olmadı. Maliyet bariyeri (≈ 3–5 puan) gün içi 30 dk'lık mum yapılarının taşıdığı
bilgiden büyük (YL-03/04 ile aynı sonuç, bu kez gözle önerilmiş yapılarla). Tek kalıcı bilgi, maliyeti zaten ödenmiş ORB × VIX kırılımının
**içinde**: girişe art arda yeşil 1m mumlarla gelinmesi ve (ters sezgiyle) son mumlarda üst fitil bulunması işlemi iki dönemde de iyileştiriyor;
ama kitap Sharpe'ını iki dönemde artırmadığı için lot değiştirilmedi.
**Uygulama:** `yeni deneme/orb_vix_live.py::anatomy_1m` — ORB × VIX tetik anında f_run, f_uw5, f_clv, f_flip olay kaydına (`kural_canli_olaylar.jsonl`,
`anatomi_1m`) yazılır; karar vermez (gölge etiketi). n ≥ 100 canlı işlemde f_run ≥ 3 kolu diğerinden iyi ve kitap dozu iki dönemde artırırsa doz önerilir.

Ders (defter E140): **grafikte göze çarpan bağlam ayrımı (sıkışma→devam, uzama→dönüş) seçilmiş örneklerden doğar**; aynı ayrım yüzlerce olayda
yok. Görsel sezgi hipotez üretir, kanıt değildir; sezginin yönü bile ters çıkabilir (üst fitil).
