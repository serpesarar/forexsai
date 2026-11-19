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
