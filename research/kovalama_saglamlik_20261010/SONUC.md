# Sonuç — IO-18 "NDX SELL düşüşü kovalama" sağlamlık turu (2026-10-10)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · `run.py` → `results/rapor.txt` · keşif kontrolleri `posthoc.py` → `results/posthoc.txt`.
Koşullar sabit: C1 = 1h fiyat EMA50'nin ≥2 ATR altında · C2 = 1h RSI ≤ 35. Simülasyon: sonraki 1m açılış + 1,5 puan spread,
risk %0,373 × fiyat, RR 0,73 (G1); 0,84×ATR1h (G2) aynı yönde.

| test | veri | C1 SL farkı (gün-blok %95) | hüküm |
|---|---|---|---|
| A1 bot içi | 237 gerçek NDX SELL | +23,4pp [+11,7…+34,9], +16,0R [+3,7…+29,9] | keşif kümesi — beklendiği gibi |
| A2 ay-dışarıda | Temmuz çıkarılınca | C1 **−0,6R** (+15,6pp), C2 +3,0R | kazancın neredeyse tamamı Temmuz |
| A4 plato | 1h EMA50 1,0–3,0 ATR / RSI 33–40 | hepsi + (+8…+16R); 5m/15m karşılıkları ≈0 | yalnız 1h ölçeğinde |
| **A5 seçim düzeltmesi** | 99 özellik × 2 kuyruk × 9 eşik | en iyi kural +18,0R, boş dağılım medyan +16,5R → **p=0,30**; C1 düzeyi **p=0,57** | **madencilik gürültüsünden ayırt edilemiyor** |
| **B yeni olaylar** | botun ENGELLENEN 949 NDX SELL sinyali (07-28→10-10) | **−0,4pp** [−26…+27]; C2 −19,7pp (tersi) | **tekrarlanmadı** |
| C panel modelleri | 753 NDX SELL (pulse1/2/3, ml, meta) | +20,3pp [+8,5…+34,2] ✓, iki yarıda ✓ | tekrarlandı — ama aşağıya bak |
| C-x | aynısı, bot girişine ±30 dk hariç (548) | +15,3pp [+2,3…+33,2] | zayıflıyor |
| D decider | 451 NDX SELL kararı | +1,2pp [−20…+20] | yok |
| E aynı dönem piyasa | 1.149 sinyalsiz SELL, 06–20 UTC | +6,3pp [−4,4…+17,7]; US 13–20'de +9,1pp | bu dönemde hafif aynı yön (2025-26'da tersiydi) |
| F fark-içinde-fark | bot − piyasa | +17,1pp [+3,0…+31,3] ✓ | bot lehine |
| F' | panel (bot-yakın hariç) − piyasa | +9,0pp [−6,2…+27,7] | panel etkisi ≈ piyasa etkisi |

**Ön-kayıtlı hüküm: ZAYIFLADI.** "Güçlendi" için gereken üç şarttan ikisi tutmadı. Bağımsız olaylarda (B) etki yok. Seçim
düzeltmeli p de 0,30 ≥ 0,10.
- Botun +16R'si büyük ölçüde **Temmuz'a ait**; 99 özellikte arama yapınca bu büyüklükte bir "kural" tesadüfen de bulunuyor.
- Aynı sinyal üreticisinin engellenen 949 sinyalinde kovalama SL'yi artırmıyor; bunların çoğu Asya/Cuma saatlerinde
  (entry_window_gate). Bot işlemlerinde Asya'da da etki var (n=17), yani yalnız seansla açıklanmıyor ama küçük örneklem.
- Panel sinyallerindeki etki (hepsi US seansı) aynı dönemin genel piyasasındaki US seansı eğilimine yakın (+9pp; F' anlamsız).
  2025-26'da bu eğilim tersti → **rejime bağlı**, kalıcı mekanizma kanıtı yok.
- Ters BUY (IO-19) zaten elenmişti; bu tur onu canlandıran bir şey göstermedi.

**Kanıt sınıfı B− → C.** Veto canlıya alınmamalı. Gölge kaydı ucuz olduğu için açık kalabilir, ama beklenti düşük.
Yeniden açmak için: ≥30 yeni gerçek bot NDX SELL işleminde C1 SL farkı ≥ +15pp **ve** aynı dönem piyasa kontrolüne göre
fark-içinde-fark alt sınırı > 0.
