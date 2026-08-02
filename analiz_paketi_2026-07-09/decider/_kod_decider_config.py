"""
decider_config.py — Pepperstone TEK-BROKER decider ayarı (kendi-yeten).
=============================================================================
Decider artık YALNIZ Pepperstone'a bağlanır: NASDAQ/DAX/Altın/Petrol + VIX hepsi tek
terminalden. Bot klasörüne bağımlılık YOK. İki terminal/poller/yfinance YOK.

⚙️ SENİN DEĞİŞTİRECEĞİN TEK ŞEY: aşağıdaki PEPPERSTONE_TERMINAL_PATH.
   (Pepperstone MT5 açık + demo'ya giriş yapılmış olmalı; decider path ile attach eder,
    şifre koda gerekmez.)
"""

# ── Pepperstone MT5 terminali (TEK düzenlenecek satır) ───────────────────────
PEPPERSTONE_TERMINAL_PATH = r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"

# ── Sembol otomatik-tespit: iç ad → Pepperstone aday adları (ilk bulunan kullanılır) ──
# Decider ilk koşuda gerçek adları bulup yazar; biri yanlışsa adayı buraya ekle.
SYMBOL_CANDIDATES = {
    "NDX.INDX":    ["NAS100", "US100", "USTEC", "NAS100.cash", "USTECH", "US Tech 100"],
    "GDAXI.INDX":  ["GER40", "DE40", "GER40.cash", "GERMANY40", "DE40.cash"],
    "USOIL.FOREX": ["SpotCrude", "SPOT.US", "WTOIL-PERP", "XTIUSD", "USOIL", "WTI", "XTI/USD", "OILUSD", "USOUSD"],
    "XAUUSD":      ["XAUUSD", "GOLD", "XAU/USD", "XAUUSD.cash"],
}
VIX_CANDIDATES = ["VIX", "Volatility Index", "VIX.cash", "USVIX", "VOL.US"]

# ── Karar parametreleri ──────────────────────────────────────────────────────
VIX_REGIME_THRESHOLD = 18.4               # NDX yön rejimi eşiği (futures ~spot; gerekirse kalibre)
VIX_REGIME_SYMBOL = "NDX.INDX"
VIX_CACHE_SEC = 60
BLOCKED_SYMBOL_DIRECTIONS = {("XAUUSD", "SELL")}   # sert yasak (USOIL BUY decide.HARD_BANS'te)

# ── Supabase (outcome kaydı + journal için) ──────────────────────────────────
SUPABASE_URL = "https://xdmtbykebfpqutfgdfqs.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhkbXRieWtlYmZwcXV0ZmdkZnFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODI0NDIwNSwiZXhwIjoyMDgzODIwMjA1fQ.oOr7u4poVBy3tdNaA0sHETTODHlxc7SfZTYAW-nxrQk"
