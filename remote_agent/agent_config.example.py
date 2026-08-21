"""
agent_config.py — Evrim Ajanı ayarları (bu dosyayı agent_config.py olarak kopyala)
Windows MT5 kutusunda doldurulacak TEK dosya budur.
"""

# ── Supabase (yeni deneme/config.py'deki ile AYNI değerler) ──────────────
SUPABASE_URL = "https://xdmtbykebfpqutfgdfqs.supabase.co"
SUPABASE_SERVICE_KEY = "<yeni deneme/config.py içindeki SUPABASE_SERVICE_KEY>"

# ── Kimlik ────────────────────────────────────────────────────────────────
AGENT_HOST = "mt5_box"          # panelde görünen kutu adı

# ── Yollar (Windows kutusundaki gerçek yollar) ────────────────────────────
REPO_ROOT = r"C:\Users\<kullanici>\Desktop\panel"   # panel reposunun kökü
DECIDER_JOURNAL = REPO_ROOT + r"\claude_decider\memory\journal.jsonl"

# ── MT5 (data_recorder ile aynı; boş bırakılırsa çalışan terminale bağlanır) ─
MT5_TERMINAL_PATH = None        # ör: r"C:\Program Files\MetaTrader 5\terminal64.exe"
MT5_ACCOUNT = None
MT5_PASSWORD = None
MT5_SERVER = None

# ── Bot yeniden başlatma scripti (restart_bot komutu bunu çalıştırır) ─────
# Örnek restart_bot.bat içeriği:
#   taskkill /F /FI "WINDOWTITLE eq forexsai_bot" & timeout /t 5
#   start "forexsai_bot" cmd /k "cd /d %REPO%\yeni deneme && python forexsai_demo_bot.py"
BOT_RESTART_SCRIPT = REPO_ROOT + r"\remote_agent\restart_bot.bat"

# ── Oto-güncelleme (push et → kutu kendini günceller + süreçleri tazeler) ──
AUTO_UPDATE_ENABLED = True
AUTO_UPDATE_INTERVAL_SECONDS = 600   # 10 dk'da bir git fetch
# Değişen klasöre göre yeniden başlatılan süreçler agent içinde tanımlı
# (DEFAULT_PROCESS_TARGETS); farklı .bat adları kullanıyorsan burada ez:
# PROCESS_TARGETS = {"decider": {"match": "run_decider.py", "bat": r"calistir\3_claude_decider.bat"}}

# ── Haftalık işler (pazar 06:00 UTC varsayılan; panel komut kaydı olarak görür) ─
WEEKLY_JOBS = [
    {
        "id": "sl_forensics_bot",
        "name": "Bot SL Otopsisi (haftalık)",
        "command": "python sl_forensics.py --days 7",
        "cwd": "yeni deneme",
        "day": "sun", "hour_utc": 6,
    },
    {
        "id": "sl_indicator_join",
        "name": "Bot SL × Gösterge JOIN (haftalık)",
        "command": "python sl_indicator_analysis.py --days 14",
        "cwd": "yeni deneme",
        "day": "sun", "hour_utc": 7,
    },
    {
        "id": "mt5_pull_1m",
        "name": "Eksik 1m Bar Kurtarma (haftalık)",
        "command": "python research/mt5_pull_missing_1m.py",
        "cwd": "",
        "day": "sun", "hour_utc": 8,
    },
    # Diğer haftalık komutlarını buraya ekle (decider batch_eval, exit_compare,
    # analyze_missed, baseline_compare, distill_journal, calibration...):
    # {"id": "decider_batch_eval", "name": "Decider Batch Eval",
    #  "command": "python batch_eval.py", "cwd": "claude_decider",
    #  "day": "sun", "hour_utc": 9},
]

# ─── Claude görev köprüsü (2026-07-26) ───────────────────────────────────────
# Panel (Mac) → kutu: `python3 scripts/remote.py ask "<görev>"` ile buradaki
# Claude Code headless çalışır, çıktısı panele geri akar. Panelin Claude'u ile
# kutunun Claude'u arasında yapılandırılmış iş devri (=== SONUÇ === protokolü).
CLAUDE_TASK_ENABLED = True          # False → köprü kapanır (komut reddedilir)
CLAUDE_TASK_MODEL = "sonnet"        # varsayılan model; görev bazında ezilebilir
CLAUDE_TASK_EFFORT = "high"         # düşünme eforu (low|medium|high); "" → CLI varsayılanı
# CLAUDE_BIN = r"C:\Users\Mael\node_modules\@anthropic-ai\claude-code-win32-x64\claude.exe"
#   Ajan sırayla dener: agent_config.CLAUDE_BIN → CLAUDE_BIN env → PATH →
#   bilinen npm/node_modules yolları. Hiçbiri yoksa görev net hatayla düşer.
