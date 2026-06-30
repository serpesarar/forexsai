# Bot Makinesi — KURULUM (Windows) ve GÜNLÜK KULLANIM

## 🆘 Sistem silindiyse — sıfırdan kurtarma
Bu klasör (`calistir/`) ile `yeni deneme/` ve `claude_decider/` GitHub'da. Tek `git clone` ile geri gelir.

### 1) Klonla (boş bir klasörde CMD aç — ör. Masaüstü)
```bat
git clone --filter=blob:none --no-checkout https://github.com/serpesarar/forexsai.git forexsai-bot
cd forexsai-bot
git sparse-checkout init --cone
git sparse-checkout set "yeni deneme" claude_decider calistir
git checkout main
```
→ Sadece bu 3 klasör iner (~400K, 544MB değil).

### 2) Bağımlılıkları kur
```bat
pip install MetaTrader5 numpy requests pandas
pip install -r "yeni deneme\requirements.txt"
```

### 3) 2 config dosyasını KOY (şifreli — git'te YOK, elle eklenecek)
- `forexsai-bot\yeni deneme\config.py`   (IC Markets şifresi, Supabase, scope ayarları)
- `forexsai-bot\claude_decider\decider_config.py`   (Pepperstone yolu, Supabase)
> Bu 2 dosyanın dolu hali ana bilgisayardaki `panel\` içinde duruyor — oradan kopyalanır.

### 4) `4_vix_kaydedici.bat` içindeki Pepperstone yolunu düzenle
Bat'a sağ tık → Düzenle → `--terminal "..."` kısmını kendi Pepperstone `terminal64.exe` yoluna ayarla.

---

## ▶️ GÜNLÜK KULLANIM — çift tıkla çalıştır
Önce **MT5 terminallerini aç** (IC Markets + Pepperstone), giriş yap, AutoTrading yeşil.
Sonra `calistir\` klasöründeki bat'lara **çift tıkla** (her biri ayrı pencere, açık kalsın):

| Bat | Ne yapar | Hangi terminal |
|---|---|---|
| `1_veri_kaydedici.bat` | OHLC+indikatör → Supabase | IC Markets |
| `2_oto_trade_bot.bat` | Kural-bazlı oto-trade | IC Markets |
| `3_claude_decider.bat` | Opus decider (shadow) | Pepperstone + Claude login |
| `4_vix_kaydedici.bat` | Canlı VIX → Supabase | Pepperstone |
| `5_decider_ozet.bat` | Decider WR/EV özeti (ara sıra) | — |
| `6_decider_ogrenme.bat` | Haftalık öğrenme | — |

## 🔄 Güncelleme (yeni kod gelince — WhatsApp YOK)
`forexsai-bot` klasöründe CMD aç:
```bat
git pull
```
Sonra ilgili bat'ı kapat-aç. config dosyaların dokunulmaz (git'te yok).

## ⚠️ Mimari (silinen ne çalışıyordu — kontrol listesi)
4 süreç sürekli çalışmalı: **veri kaydedici + oto-trade bot** (IC Markets), **decider + vix kaydedici** (Pepperstone). Detaylı sistem haritası: `yeni deneme\SYSTEM_README.md`.
