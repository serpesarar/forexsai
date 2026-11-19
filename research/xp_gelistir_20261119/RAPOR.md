# XG — korku gecesi + XP: "kârı koru, zararı yarıya indir" araştırması (2026-11-19)

Ön kayıt `PROTOCOL.md` (+ EK-1…3). Kod `src/veri.py` (işlem veri seti: 1.013 işlem, 30+ giriş özelliği + yol), `anatomi.py`, `kural.py`,
`ek1.py`, `ek2_hedge.py`, `ek3_kademe.py`. KEŞİF ≤ 2021-10 (seçim), TEST 2021-11 → (kör). Hedef: TEST'te kâr× ≥ 1,0 ve zarar× ≤ 0,5.

**Sonuç: hedef kör testte tutmadı.** Hiçbir yapı kârı koruyup zararı yarıya indirmedi.

## Ne öğrendik (KEŞİF anatomisi)
- Zarar toparlanmayan pozisyonu 5 güne kadar taşımaktan geliyor: 1 günde çıkan +165 bp, 3/4/5 günde çıkan −166/−254/−602.
- Kaybedenler erken belli: ertesi 04:00'te −56 / 09:30'da −92 (kazananlar +29 / +49). Ama kazananların %10'u da −248 bp'ye kadar düşüyor
  → erken kesmek kazananları da öldürüyor.
- Zararın %39'u en kötü 10 işlemde (piyasanın toptan çöktüğü geceler).

## Ne denendi (TEST kâr× / zarar×, Duka NDX · MT5 NAS100)
| Yaklaşım | En iyi sonuç | Neden olmadı |
|---|---|---|
| Çıkış/stop: tutuş tavanı 1–3 gün, 09:30 stopu, 04:00 stopu | KEŞİF'te bile zarar ×1,04–1,44 | kaybedenler sonra kısmen toparlanıyor; kesmek kaybı kilitliyor |
| Giriş vetoları (son saat hafif, VIX düşük, olay günü, OPEX) | 4'lü veto: kâr ×0,52 · 0,55, zarar ×0,39 · 0,42, işlem başı +111 vs +78, DD ×0,70 | KEŞİF'te kârı koruyordu; TEST'te vetolanan işlemler hâlâ kârlı |
| Seri / strateji eğrisi freni | kâr ×0,80–0,91, zarar ×0,83–0,99 | kayıplar ardışık değil |
| Çok özellikli sınıflandırıcı (lojistik, GBM) | AUC 0,50–0,62 | kaybeden giriş anında tanınmıyor |
| Korumalı (NDX al + US500/US30/US2000 sat) | h 0,5: kâr ×1,07–1,10, zarar ×0,99–1,07 | korku toparlanması piyasa geneli; koruma kazancı da siliyor |
| Teyitli kademeli giriş (16:00 kısmi, sabah artıdaysa ekle) | A: kâr ×1,09 · 1,14, zarar ×0,97 · 0,89; B: zarar ×0,52 · 0,51 ama kâr ×0,40 | lot küçültmekle aynı etki |

## Kullanılabilir en iyi takaslar (hedef değil, seçenek)
1. **4'lü veto** (OPEX + olay + son saat hafif + VIX düşük): işlem sayısı ~1/3'e iner, işlem başı kâr +%40, zarar ×0,4, kâr ×0,5.
   Aynı sermayeyle "daha az ama daha kaliteli işlem" isteyen için.
2. **Teyitli kademe A** (½ lot 16:00 + 04:00'te ≥ +25 bp ise 1,5 lot ekle): NDX'te kâr ×1,09–1,14, zarar ×0,89–0,97 (küçük iyileşme,
   kör US30'da tutmadı → C).
3. Mevcut önerilen paket (OPEX vetosu + XP) zaten bu ailenin en iyi risk/getiri dengesi; zararı yarıya indirmenin tek gerçek yolu lotu
   yarıya indirmek (kâr da yarıya iner).

## EK-4 — derin felaket stopu (−200…−600 bp, işlem yolunda)
Zarar her piyasada ve her dönemde ×1,2–2,0 arttı; stopla kesilen işlemlerin çoğu sonradan kazanana dönüyordu. 4'lü vetoyla birlikte
zarar ×0,29–0,44, kâr ×0,27–0,61. **Yedinci yol da hedefi tutmadı.**

## EK-5 — oynaklığa göre lot (risk eşitleme)
1/rv20, 1/VIX, 1/max(rv20, VIX); ölçek KEŞİF'te kârı tabana eşitler. TEST'te zarar ×1,07–1,97 → X. Korku gecesinin kazancı yüksek
oynaklık gecelerinde; lotu orada küçültmek kazancı, sakin günlerde büyütmek zararı artırıyor. **Sekizinci yol da hedefi tutmadı.**

## EK-6 — hedefe en yakın yapı: 4'lü veto + −400 bp felaket stopu + lot ×1,2–1,4 (KEŞİF'ten dondurulmuş)
| | Kâr× | Zarar× | En kötü %10× | En büyük düşüş× |
|---|---|---|---|---|
| Duka NDX 2021–26 | 0,81 | **0,40** | 0,52 | 0,52 |
| MT5 NAS100 2021–26 | 0,75 | **0,38** | 0,48 | 0,44 |
| Kör US500 / US30 / US2000 | 0,36 / 0,60 / 0,33 | 0,43 / 0,54 / 0,36 | — | — |
NASDAQ'ta zarar yarıdan fazla düşüyor ama kâr %19–25 eksik; kör piyasalarda kâr/zarar oranı iyileşmiyor (0,84–1,11) → **C**, hedef
tutmadı. Birleşim TEST görüldükten sonra seçildiği için ancak ileriye dönük gölgede doğrulanabilir.

## EK-7 — tutuşu uzatmak / "zarardayken satma, başabaşı bekle"
XP ilk yükselen kapanışta giriş altındayken de çıkıyor; bunun yerine başabaşa kadar en çok H gün (5–40) beklemek. KEŞİF'te BE40 hedefi
geçti (kâr ×1,42, zarar ×0,41), **TEST'te çöktü** (NDX kâr ×0,85–0,98, zarar ×1,28–1,52, en büyük düşüş ×3,1–3,7; 2022 ayısı).
**Onuncu yol da hedefi tutmadı.**
