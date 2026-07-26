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

---

## Panel → kutu Claude köprüsü (2026-07-26)

Panelden (Mac) bu kutudaki **Claude Code'a doğrudan görev verilebilir**:

```bash
python3 scripts/remote.py ask "botun son 2 saatteki TREND KAPISI satırlarını say"
python3 scripts/remote.py ask "..." --model opus --timeout 1800 --cwd "yeni deneme"
python3 scripts/remote.py sh   "git log --oneline -5"
python3 scripts/remote.py pull
python3 scripts/remote.py restart decider|bot|backend|agent
python3 scripts/remote.py status | watch <id> | health
```

Akış: panel komutu `evolution_commands`'a yazar → ajan 30 sn içinde çeker →
`claude_task` handler'ı Claude Code'u headless koşturur → çıktı canlı geri akar.
Kutudaki Claude sonunda `=== SONUÇ ===` bloğu yazar (durum / özet / bulgular /
önerilen_adım); panel bunu ayrıştırıp iş devrini sürdürür.

**Kurulum:** `agent_config.py` içinde `CLAUDE_TASK_ENABLED = True` (varsayılan) ve
gerekiyorsa `CLAUDE_BIN` (ajan sırayla dener: config → env → PATH → npm/
node_modules glob). Kapatmak için `CLAUDE_TASK_ENABLED = False`.

**Sınırlar:** cwd repo kökü altına kilitli · prompt ≤100 KB · timeout ≤1 saat ·
görev protokolü kutudaki Claude'a "canlı trade süreçlerine izinsiz dokunma,
MT5'te elle emir açma, önce gözlemle" der.
