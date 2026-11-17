# akntrade — 1H iğne → 15m süpürme → 5m/3m CHoCH → FVG geri çekilmesi (NDX) — ön kayıt (2026-11-16, HİÇBİR sonuç görülmeden)

## İstek
Kullanıcı akntrade'in Instagram Reel'ini (ses dökümü + 4 kare) paylaştı: "analiz et, sistemini kur, tüm NASDAQ verisiyle backtest yap."

Kural (videodan):
1. **1H:** mum gövdesi küçük, iğnesi uzun; fiyat bir likiditeyi süpürmüş.
2. **15m:** yükselişte YEŞİL mum likiditeyi süpürür, sonraki mum KIRMIZI. Düşüşte tersi: kırmızı mumla süpürme, sonraki yeşil.
3. **5m'de CHoCH:** 5–6 mum içinde gelmezse 3m'ye inilir (5 ve 3 arasında gidip gelinir).
   - 1m'de CHoCH hızlı oluşur ama video sahibi "testlerimde %50 isabet" diyor.
4. **FVG ve geri çekilme:** CHoCH sonrası FVG beklenir; FVG'ye ilk dokunuşta ya da FVG'nin %50'sinde ters yöne işlem açılır.
5. **Stop ve hedef:**
   - Stop süpürülen likiditenin biraz üstünde.
   - Hedef "1–2R değil": en yakın likidite, ya da aşağıdaki order block teması.

## Defter (3. KURAL)
- SM-01 (süpürme + CHoCH + FVG, 1m/5m, gün-içi seviyeler): KEŞİF +0,221 → TEST −0,039 → bağımsız −0,118 → X.
- MZ-01…04 (1H süpürme → 5M giriş): X. Süpürme dönüş sinyali değil, devam hafif artı.
- HL-02a (CHoCH): X. FS-01…05: X.
- **FR-15 (1H teyitli çekiç AL, TP 5R): B. Üst fitil SAT: X.**

**Yeni tanım:** dört katmanın zinciri (1H iğne + 15m renk-dönüşlü süpürme + 5m/3m CHoCH + FVG limit girişi).
**Yeni veri:** NDX Dukascopy 1m 2018-01 → 2026-11 (`research/nom_20261113/data/ndx_1m_v3_duka.parquet`, gerçek bar spread'i).
Önsel beklenti: SAT tarafı negatif, AL tarafı taban civarı.

## Tanımlar (SAT; AL tam aynası)
Barlar NY yerel saatiyle kovalanır (1m tabandan 3m / 5m / 15m / 1H). Bir bar ancak kapanınca bilinir. Fraktal salınım = sol 2 bar kesin, sağ 2 bar ≤, sağdaki 2. bar kapanınca bilinir. Seviye ilk aşıldığında ölür.

- **K1 — 1H iğne süpürmesi:**
  - 1H barı ≥ 1 aktif 1H fraktal tepeyi fitille aşar ve hepsinin altında kapanır.
  - Üst fitil ≥ 0,5 × aralık, |gövde| ≤ 0,33 × aralık.
  - Aynı bar iki yönü süpürürse olay atılır.
- **K2 — 15m:**
  - 1H barı kapandıktan sonra, 3 saat içinde bir 15m barı j: YEŞİL (c > o), aktif bir 15m fraktal tepeyi aşar ve onun altında kapanır.
  - j+1 barı KIRMIZI. Onay anı = j+1 kapanışı.
  - Uç = 15m süpürme barının (j) tepesi ile o ana kadarki en yüksek.
- **K3 — CHoCH (LTF):**
  - Seviye: onay anında bilinen en son LTF fraktal dibi.
  - CHoCH: onaydan sonraki ilk LTF barının bu dibin ALTINDA kapanması, 60 dk içinde.
  - Bu arada fiyat ucu aşarsa kurulum ölür.
  - LTF varyantları:
    - **C53 (birincil):** 5m ve 3m'den hangisi önce;
    - C5: yalnız 5m;
    - C3: yalnız 3m;
    - C1: yalnız 1m (videonun "%50" iddiası).
- **K4 — FVG:**
  - CHoCH'un olduğu LTF'de ayı FVG: (a, b, c) barları, h_c < l_a.
  - Arama: c barı uç barı ile CHoCH barı arasındaysa en sondaki FVG; yoksa CHoCH'tan sonraki ilk 3 bar içinde ilk oluşan.
  - FVG c barı kapanınca bilinir.
- **Giriş:** satış limiti; 60 dk geçerli.
  - E1 (ilk dokunuş) = FVG alt kenarı h_c.
  - E50 = FVG ortası.
  - Dolmadan uç aşılırsa ya da hedef görülürse emir iptal.
  - Dolum 1m'de bid ≥ limit; dolum barında hedef sayılmaz, stop sayılır.
- **Stop:** uç + 1 tick (SAT stopu ask ile tetiklenir). Risk < 2 × spread → işlem yok.
- **Hedefler:**
  - T1 "en yakın likidite": girişte aktif, ≥ 0,5R uzak en yakın 15m fraktal dip.
  - T2 "order block teması": ≥ 1R uzak en yakın aktif 1H fraktal dip (yükselişin kökü).
  - Ayrıca 1R / 2R raporlanır.
  - Zaman stopu 24 saat ya da hafta sonu boşluğundan önceki son bar. Hedef yoksa zaman stopu.

## Birincil hipotezler (Holm, 3)
- P1 = C53 · E1 · T1
- P2 = C53 · E50 · T1
- P3 = C53 · E50 · T2

## Kümeler
Dönem A 2018–2020 · B 2021–2023 · C 2024-01 → 2026-11. Seçim yok, kurallar sabit.

## Kontroller
- **Ayna:** aynı dolum anı, aynı risk, ters yön, aynı hedef R.
- **Zaman plasebosu (E79 uyumlu):** onay anı (K2) + 60 dk içinde rastgele piyasa girişi; aynı yön / risk / hedef R; 200 tekrar.
- **Katman katkısı:**
  - K1 yok (yalnız K2 → K4);
  - K2 yok (K1 → K3 → K4);
  - yalnız K3 → K4 (her CHoCH + FVG).
- **Spread × 1,5.** **Tek pozisyon.** Yön ayrımı (SAT / AL) ayrıca raporlanır.

## Hüküm (her birincil hipotez)
1. A, B, C dönemlerinin üçünde de ort. R > 0.
2. Birleşik gün-blok bootstrap P(EV > 0) ≥ 0,95.
3. Birleşikte aynadan iyi ve zaman plasebosu dağılımının ≥ %50'liğinde.
4. Spread × 1,5 birleşik > 0.
5. Tek pozisyon birleşik > 0.
6. n ≥ 150.

Sınıflar:
- **B:** tümü + Holm.
- **B−:** tümü, Holm'suz.
- **C:** birleşik > 0 ve P ≥ 0,90, ama bir ölçüt düşüyor.
- **X:** aksi.

B bile yalnız gölge adayıdır (2. KURAL kartı ayrıca).

## EK-0 (2026-11-16, yalnız olay SAYILARI görülerek, hiçbir sonuç/R görülmeden)
Sayım (`sayim.py`, 9 yıl, C53 · E50):
- 1H iğne süpürmesi 1.410.
- Sıralı K1→K2 (15m süpürmesi 1H kapanışından SONRA yeni olay) yalnız **39 işlem**: ölçüt 6'yı yapısal olarak geçemez.
- Videonun 3. karesi 15m süpürmesini 1H iğnesinin İÇİNDEKİ aynı hareket olarak gösteriyor.

**Birincil zincir K1K2n (iç içe):**
- 1H iğnesinin ucunu yapan 15m barı süpürme yönü renginde (SAT: yeşil), sonraki 15m barı ters renkte.
- Onay = max(1H kapanışı, o sonraki 15m barının kapanışı) — iki bilgi de kesinleştikten sonra.
- 193 işlem.

P1–P3 bu zincirle; sıralı K1K2 tanı olarak raporlanır. Diğer her şey değişmedi.
