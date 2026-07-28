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
