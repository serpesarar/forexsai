# ForexSAI — Demo Deney Botu

İkinci MT5 (IC Markets demo) hesabında **yeni TP/SL düzenini** test eden bot.
Walk-forward analiziyle doğrulanmış 3 robust scope'ta, en başarılı model
ailesi olan **PULSE** sinyallerini işler.

## Ne yapar

- ForexSAI backend'inden pulse1/2/3 sinyallerini çeker.
- Sadece şu 3 scope'ta işlem açar (rolling walk-forward'da robust çıkanlar):

  | Scope | Türetilmiş TP | Türetilmiş SL |
  |---|---|---|
  | NDX BUY | 80 puan | 110 puan |
  | GDAXI SELL | 67 puan | 119 puan |
  | USOIL SELL | %1.04 | %1.49 |

- Diğer her şeye (XAUUSD, NDX SELL, GDAXI BUY, USOIL BUY) dokunmaz.
- Ana ForexSAI sistemine / diğer MT5 terminaline müdahale etmez.

## Kurulum (Windows)

İkinci MT5'i ayrı klasöre kurduğundan emin ol (ör. `C:\MT5_Demo\`).
PowerShell veya CMD'de, bu klasörün içinde:

```bat
:: 1. Sanal ortam oluştur
python -m venv venv

:: 2. Sanal ortamı aktifleştir
venv\Scripts\activate

:: 3. Kütüphaneleri kur
pip install -r requirements.txt
```

(macOS/Linux'ta aktifleştirme: `source venv/bin/activate` — ama MetaTrader5
paketi yalnızca Windows'ta çalışır, botu Windows'ta çalıştır.)

## Ayar

`config.py` dosyasını aç:

1. **`MT5_TERMINAL_PATH`** — 2 MT5 aynı anda çalışıyorsa demo terminalinin
   `terminal64.exe` yolunu yaz (ör. `r"C:\MT5_Demo\terminal64.exe"`).
   Tek terminal varsa boş bırakabilirsin.
2. Hesap bilgileri (ID/şifre/sunucu) zaten dolu — IC Markets demo.
3. **`LIVE_TRADING`** — varsayılan `False`. Bot önce sadece "şu işlemi
   açardım" diye loglar, **gerçek emir açmaz**. Birkaç saat izle, mantıklıysa
   `True` yap.

## Çalıştırma

```bat
venv\Scripts\activate
python forexsai_demo_bot.py
```

Bot başlayınca broker'daki sembol adlarını yazdırır. Eğer `NAS100 / GER40 /
XTIUSD` IC Markets'te farklı adlandırılmışsa (`config.py` → `SYMBOL_MAP`)
düzelt — bot çoğu varyantı otomatik bulmaya da çalışır.

## Çıktılar

- `demo_bot.log` — tüm faaliyet günlüğü
- `demo_trades.csv` — açılan (veya gözlem modunda "açılacak") işlemler

## Güvenlik

- Bu bir **demo** hesabı — gerçek para yok.
- `config.py` hesap şifresi içerir → bu klasör git'e dahil EDİLMEZ
  (repo `.gitignore`'unda `yeni deneme/`).
- Kill switch: `LIVE_TRADING=False` yap → bot işlem açmayı anında durdurur.

## Sonuçları değerlendirme

Birkaç hafta sonra IC Markets demo'nun işlem geçmişini, ana sistemdeki
`/api/mt5/upload-deals` + `/api/mt5/reconcile` araçlarıyla içe aktarıp
türetilmiş TP/SL'nin canlıda da tuttuğunu doğrulayabilirsin.
