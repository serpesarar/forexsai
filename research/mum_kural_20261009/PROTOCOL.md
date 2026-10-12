# Mum formasyonu kural taraması — ön kayıt (2026-10-09, sonuçlara bakılmadan)

Kullanıcı isteği: tüm zaman dilimlerinde pozitif, kâr faktörü (PF) ≥ 1,05 veren, karar verdiren mum modeli.
Defter kontrolü: GF-01 (tek-özellik durum kapıları plasebo altı), OLD-15 (1m/5m dönüş aileleri sürtünmeye yenik),
OLD-21 (büyük kırmızı mum SELL kenarsız), PM/PM-2 (birebir mum dizileri tesadüf). Bu tarama **yeni tanım**:
klasik formasyon × bağlam × çıkış, ve ölçüt "tek TF'de anlamlı" değil "4 TF'nin hepsinde pozitif".

## Veri ve kilitli kasa
- NDX: M1, M5 (2025-01 → 2026-06-30), M15, M30 (2023-10 → 2026-06-30) = **keşif**.
- **Kilitli kasa 1:** NDX 2026-07-01 → 2026-10-02, 4 TF. **Kilitli kasa 2:** DAX 15m (2022-11+), 30m (2021-03+), 1h (2019+).
  Kasalar yalnız keşfi geçen adaylar için, bir kez açılır.

## Kurallar (karar = sinyal mumu KAPANIŞI; giriş = sonraki mumun açılışı)
Tanımlar: ATR14 (önceki 14 mum), gövde B = |C−O|, aralık R = H−L, üst/alt fitil, EMA50, 20 mumluk tepe/dip (önceki 20 mum).
Bağlam: `dip` = mum düşüğü ≤ önceki 20 mumun en düşüğü; `tepe` = yükseği ≥ önceki 20 mumun en yükseği; `yukari` = C > EMA50.
1 yutan boğa (önceki kırmızı, şimdiki yeşil, gövde öncekini kapsar) · 2 yutan ayı · 3 çekiç @dip (alt fitil ≥2B, üst ≤B) ·
4 kayan yıldız @tepe · 5 kapitülasyon kırmızı @dip (R ≥2 ATR, kapanış alt %25) · 6 coşku yeşil @tepe (R ≥2 ATR, kapanış üst %25) ·
7 iç bar sonrası yukarı kırılım (önceki iç bar; şimdiki kapanış ana mumun tepesinin üstünde) · 8 aşağı kırılım ·
9 üç beyaz asker · 10 üç kara karga · 11 sabah yıldızı · 12 akşam yıldızı · 13 pin bar @dip (alt fitil ≥ 2/3 R) ·
14 pin bar @tepe · 15 dış bar yeşil kapanış · 16 dış bar kırmızı kapanış · 17 yükselişte 3 düşen kapanış (yukari ∧ 3 ardışık
daha düşük kapanış) · 18 düşüşte 3 yükselen kapanış (¬yukari) · 19 NR7 (son 7'nin en dar aralığı) sonrası yukarı kapanış ·
20 NR7 sonrası aşağı kapanış.
Her kural **iki yönle**: TAKİP (formasyonun beklenen yönü) ve TERS. → 40 kural-yön.

## Çıkışlar
T5, T10, T20 (mum sonra kapanış), B11 (TP 1 ATR / SL 1 ATR), B21 (TP 2 / SL 1), en çok 60 mum, aynı mumda ikisi → SL.
Getiri birimi: ATR (R = getiri/ATR; braketlerde SL=1 ATR olduğundan R ile aynı). Maliyet: 1,5 puan spread/ATR.
→ 40 × 5 = 200 yapılandırma.

## Geçme (keşif)
Her 4 TF'de: n ≥ 100, ort. net R > 0, PF ≥ 1,05; VE keşfin iki kronolojik yarısında (TF'ler havuzlanmış) ort. R > 0.
**Plasebo:** her yapılandırmanın olay zamanları TF içinde rastgele dairesel kaydırılır (sayı ve rejim korunur), aynı ölçüt;
20 tekrar → geçen sayısı dağılımı. Gerçek geçen sayısı plasebonun %95'ini aşmıyorsa "aile düzeyinde kenar yok".
## Kasa
Keşfi geçen her yapılandırma: kasa 1'de 4 TF'nin her birinde ort. R > 0 ve havuzda PF ≥ 1,05; kasa 2'de (DAX 15m/30m/1h)
3'ünde de ort. R > 0. İkisini de geçen = **bulgu** → canlıya alma kartına aday. Hiçbiri geçmezse bu açıkça raporlanır.

## TUR 2 (2026-10-09, tur 1 sonucundan SONRA yazıldı — bu açıkça bir değişikliktir)
Tur 1: 200 yapılandırmanın 0'ı geçti; M1'de hepsi −0,14…−0,20R (spread 1,5 puan ≈ M1 ATR'nin %19'u → yapısal),
M15/M30'daki pozitifler çoğunlukla uzun tutulan BUY'lar (2023–26 sürüklenmesi). Değişiklikler (gerekçe: ölçülen
maliyet/ATR ve sürüklenme; eşikler değişmedi):
1. TF'ler: **M5, M15, M30** (M1 dışarıda). DAX kasası aynı (15m/30m/1h).
2. Ek şart: her TF'de ort. R − **taban** > 0; taban = aynı TF, aynı yön, aynı çıkışla TÜM geçerli mumlarda giriş.
3. Diğer her şey aynı (n≥100, R>0, PF≥1,05, iki yarı, 20 dairesel-kaydırma plasebosu, kasa bir kez).
