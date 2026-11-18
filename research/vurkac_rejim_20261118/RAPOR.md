# Rejime bağlı vurkaç — 5 dk aşırı uzamadan kısa TP'li dönüş (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/vr.py`.

## Sonuç: X (aday yok), ama mekanizma kısmen doğrulandı

5 dk "dalga" tespiti: son 1 saatin ortalamasından z ≥ 2 sapma. Dönüş yönünde kısa TP'li işlem:
- TP 0,5–1σ, SL 1–2σ, 30 dk.
- Rejimler: hepsi, VIX ≥ 25, dünkü aralık ≥ %2, anlık oynaklık 2×.
- AL ve SAT ayrı.

48 hücrenin **hiçbiri** ölçütü geçmedi: ort R > 0, P ≥ %90, rastgele girişten iyi, spread × 1,5 > 0.

| yön / rejim (2018–21 ort R, geometriler ortalaması) | dalga girişi | aynı gün rastgele giriş |
|---|---|---|
| AL, hepsi | −0,088 | −0,112 |
| AL, VIX ≥ 25 | −0,067 | −0,068 |
| AL, dünkü aralık ≥ %2 | −0,044 | −0,081 |
| AL, anlık oynaklık 2× | −0,036 | −0,110 |
| SAT, hepsi | −0,130 | −0,121 |
| SAT, anlık oynaklık 2× | −0,035 | −0,070 |

En iyi hücre: AL, z ≤ −2, TP 0,5σ / SL 1σ, VIX ≥ 25.
- +0,040R (n 485, isabet %69).
- Rastgele girişten çok iyi: P %99,9.
- Ama spread × 1,5'te −0,001R, gün-küme P %90,6.

**Ne öğrendik:**
1. **Dalga tespitinin bilgisi gerçek.** Rastgele girişten tutarlı olarak iyi; YL-03 bulgusunun 5m hâli.
2. **Oynaklık yükseldikçe sonuç başabaşa yaklaşıyor** (−0,09R → +0,04R), ama maliyeti açıkça aşmıyor. Gerekçe (dönüş boyu
   oynaklıkla ölçeklenir) yönce doğru; büyüklüğü yetmiyor.
3. **Düşüşü almak yükselişi satmaktan iyi.** "Korku döner, coşku dönmez" dakika ölçeğinde de var.
4. **Yüksek isabet tuzağı:** TP 0,5σ / SL 1σ ile %65–69 isabet, beklenti ≈ 0.

**Vurkaç için kalan tek yol:** maliyeti düşürmek ya da dönüşü daha erken ve kesin yakalamak. Örneğin daha dar spreadli bir
broker ya da emir defteri / agresör akışı verisi (YL-06'da ücretsiz kaynaklar şans düzeyindeydi). Bu veri olmadan NDX'te kısa
TP'li vurkaç kârlı değil.
