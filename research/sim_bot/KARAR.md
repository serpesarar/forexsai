# Genişletilmiş Deney — Karar Raporu (2026-07-28)

Kullanıcı isteği: "daha çok test, farklı zaman dilimleri, kesin emin ol · çok
sıkı olmasın, günde 1-2 işleme düşmesin · örüntü yakalayıp doğru noktadan
girsin · son 400 mumun destek/direnç seviyelerini hesaba katsın · geleceği
görme kesinlikle olmasın."

## Test edilen dört varyant

| | Ne yapar |
|---|---|
| **A ham-market** | Sinyal anında market emri (VIXREG'in BUGÜNKÜ davranışı) |
| **B kapı-at** | trend+konum kapısı; takılan sinyali ATAR (bugünkü canlı ROBUST) |
| **C kapı+SR-limit** | Kapıyı geçen market; **takılanı en yakın S/R seviyesine LIMIT taşır** (90dk geçerli) |
| **D hepsi-SR-limit** | HER sinyali S/R seviyesine limit olarak taşır |

S/R: son **400×5m mum**, ≥4 dokunuşlu bölge kümeleme, max 2.5×ATR uzaklık.
Sızıntı: seviyeler yalnız karar anına kadarki barlardan; dolum sonraki
barların high/low'u ile; çözüm dolumdan sonraki barlarla; aynı barda TP+SL →
konservatif SL. Eşik ayarı hiçbir dilimde yapılmadı (tüm dilimlerde aynı sabit).

## Haftalık dilim dayanıklılığı — 48 sembol-yön-hafta

| Varyant | Pozitif hafta | Toplam R | İşlem/gün |
|---|---|---|---|
| A ham-market (bugünkü VIXREG) | 28/48 (%58) | **+14.4** | 2.55 |
| **B kapı-at** | **37/48 (%77)** | **+81.7** | 0.96 |
| C kapı+SR-limit | 30/48 (%63) | +64.0 | 1.93 |
| D hepsi-SR-limit | 31/48 (%65) | +63.1 | 1.83 |

## Üç net sonuç

**1. Mevcut ham-market davranışı kesin kaybediyor.** A hem toplam kârda
(+14.4R) hem dayanıklılıkta (%58 hafta) sonuncu. VIXREG'in bugünkü giriş
biçimi değişmeli — bu artık şüphe değil, ölçüm.

**2. Senin S/R-limit fikrin işlem sayısını KORUYOR ama net ZARAR ettiriyor.**
C = B + (kapıya takılıp S/R'da dolan işlemler). Aradaki fark:
**64.0 − 81.7 = −17.7R**. Yani kapıya takılan sinyali doğru fiyata taşımak,
onu atmaktan **daha kötü**. Sebep: kapıya takılan sinyal zaten bozuk (yanlış
yön veya yanlış konum); girişi düzeltmek sinyalin kendisini düzeltmiyor.
Fikir mantıklıydı, veri desteklemedi — dürüstçe raporluyorum.

**3. Kalite ve hacim burada gerçekten çelişiyor.** İşlem sayısını 0.96→1.93/gün
çıkarmanın bedeli 17.7R. "Az ve kaliteli" ile "çok ve ortalama" arasında
seçim yapmak gerekiyor; ikisini birden veren bir varyant bu testte çıkmadı.

## Önerim

**B'yi uygula** (canlıda zaten bu var — trend+konum kapıları). İşlem sayısını
artırmak için kapıyı gevşetmek yerine **kapsam genişletmek** daha doğru yol:
- NDX SELL şu an yalnız VIXREG'den geliyor (momentum scope'u yok)
- XAUUSD icra dışı (`TRADING_DISABLED_SYMBOLS`)
- GDAXI SELL kapalı
Bunlar açılırsa işlem sayısı kaliteden ödün vermeden artar. Her biri ayrı
kanıt ister — sırayla test edilebilir.

## Sabır kapısı — hâlâ çelişkili, karar ertelendi

| Kanıt | Yön |
|---|---|
| bot_trades replay (132 gerçek VIXREG SELL) | +39.3R **faydalı** |
| timelapse OUT-of-sample (3/3 SELL scope) | **zararlı** (NDX +10.3R→+5.2R) |
| canlı 2026-07-27 | 8 kuyruktan geçen 1 işlem SL |

Timelapse'te VIXREG mantığı (VIX rejimi) simüle edilemiyor — yani iki ölçüm
farklı popülasyonlara bakıyor ve doğrudan karşılaştırılamaz. **Kapı duruyor**,
`gate_skipped.jsonl`'deki `patience_*` kayıtları n≥20 olunca `gate_audit.py`
ile hükme bağlanacak. Kullanıcı isterse tek bayrakla kapatılır
(`VIXREG_SELL_PATIENCE=False`).

**Dosyalar:** `sim.py` · `sim2.py` (S/R limit varyantları) · `regime_test.py`
(haftalık dayanıklılık) · `walkforward.py` · `FINDINGS.md`

---

## EK — 2026-07-28 gece: uygulananlar + bir öz-düzeltme

### Öz-düzeltme: "candle_cache 400 puan sapmış" teşhisi YANLIŞTI
Bot log satırlarındaki saati UTC sandım; aslında **UTC−4** (kutu lokal saati).
Botun `10:03`'te gördüğü 28153 fiyatı, gerçekte **14:03 UTC** — ve candle_cache
o saatte 27790–28207 aralığında, yani **tam uyumlu**. Kutudan alınan canlı MT5
bid'i (NAS100 27930.4) ile candle_cache son barı (27928.4) de örtüşüyor.
**Veri sağlam, simülasyonlar geçerli** (zaten prediction_logs + candle_cache
kullanıyorlar, ikisi de gerçek UTC; bot log saati simülasyona hiç girmiyor).

### Uygulanan 1: SABIR kapısı varsayılan KAPATILDI
Kanıt dengesi kapatma yönünde: timelapse OUT 3/3 SELL scope'ta zararlı ·
haftalık dilim testinde en iyi varyant sabırsız · canlıda geçen tek işlem SL.
Kod silinmedi (karşı kanıt çürütülmedi) — `VIXREG_SELL_PATIENCE=True` ile döner.

### Uygulanan 2: XAUUSD GÖLGE scope'u
Kapsam testinde XAU açık ara en kârlı çıktı (B varyantı: BUY +55.3R/6-9 hafta,
SELL +103.7R/8-9; spread 0.30'da bile +44/+51R; ~11.6 işlem/gün — kullanıcının
istediği hacim). **AMA canlıya AÇILMADI**, gerekçe:
- XAU 2026-06'da canlıda para kaybettiği için icra dışı bırakılmıştı
- Hafızada iki bağımsız araştırma: "XAU intraday edge yok", "dar stop öldürür"
  (sim'deki SL 6 puan = %0.148 — tam da o dar stop)
- Simülasyonda **A varyantı da pozitif** (+33/+70.7R) çıkıyor ama canlı A
  negatifti → simülasyonun modellemediği bir şey var (icra, slippage, seans)

Bu çelişki çözülmeden gerçek para riske edilmez. Onun yerine `check_shadow_scopes()`:
bot XAU sinyallerini her taramada kapılardan geçirir, geçenleri
`gate_skipped.jsonl`'e `shadow_signal` olarak yazar, **işlem AÇMAZ**.
2 hafta sonra `gate_audit.py --reason shadow_signal` ile gerçek sonuç ölçülüp
açma kararı verilecek.

### Uygulanmayan: GDAXI SELL / NDX SELL momentum
Haftalık dilim testinde ikisi de zayıf çıktı (GDAXI SELL B: 4/7 hafta, +1.1R;
NDX SELL zaten VIXREG üzerinden açık). Kapsam genişletmede tek güçlü aday XAU.
