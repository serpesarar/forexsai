# Evrim Ajanı — MT5 Kutusu Kurulumu (tek seferlik, ~5 dakika)

Panel ile MT5 kutusu arasındaki çift yönlü köprü. Kurulduktan sonra kutuya
bir daha dokunmak gerekmez — analiz çalıştırma, ders gönderme, bot yeniden
başlatma ve haftalık işler panelden yönetilir.

## Kurulum (Windows MT5 kutusunda)

1. Repoyu güncelle: `git pull`
2. Bağımlılık: `pip install supabase` (MetaTrader5 zaten kurulu)
3. Ayar dosyası:
   ```
   cd remote_agent
   copy agent_config.example.py agent_config.py
   ```
   `agent_config.py` içinde doldur:
   - `SUPABASE_SERVICE_KEY` → `yeni deneme/config.py`'den kopyala
   - `REPO_ROOT` → reponun Windows'taki gerçek yolu
   - İstersen `WEEKLY_JOBS`'a diğer haftalık komutlarını ekle
4. `restart_bot.bat` oluştur (botunu nasıl başlatıyorsan ona göre; örnek
   `agent_config.example.py` içinde).
5. Başlat: `start_agent.bat` (veya `python evolution_agent.py`)
6. Otomatik başlangıç (önerilir): `start_agent.bat`'a sağ tık → kısayol
   oluştur → kısayolu `shell:startup` klasörüne at.

## Doğrulama

Panel → **Canlı Bot & Decider** bölümünde kutu 3 dakika içinde 🟢 görünmeli.
İlk push'ta son 30 günün MT5 deal'leri ve decider journal'ı yüklenir.

## Ne yapar / ne yapmaz

- ✅ MT5 kapanan işlemleri + decider kararlarını Supabase'e iter (5 dk)
- ✅ Panelden gelen komutları işler: analiz çalıştır, ders senkronu,
  git pull, güvenli bot restart (açık pozisyon varsa bekler)
- ✅ Haftalık işleri kendisi koşturur, sonuç panele düşer
- ❌ Serbest shell komutu KABUL ETMEZ (yalnız tanımlı 4 komut türü)
- ❌ Kod değiştirmez — kod değişikliği yalnız `git pull` ile, commit'li gelir
