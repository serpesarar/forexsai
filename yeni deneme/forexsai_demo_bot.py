"""
ForexSAI — Demo Deney Botu
==========================
PULSE sinyallerini (rolling walk-forward'da en başarılı model ailesi)
ForexSAI backend'inden çeker; walk-forward ile doğrulanmış 4 robust scope
(NDX BUY / GDAXI BUY / USOIL SELL / USOIL BUY) için TÜRETİLMİŞ TP/SL ile
IC Markets demo hesabında işlem açar. Güncel scope listesi: config.ROBUST_SCOPES
(GDAXI SELL 2026-06-24'te çıkarıldı — OOS'ta çöktü).

Çalıştırma:  python forexsai_demo_bot.py
Ayarlar:     config.py
Güvenlik:    config.LIVE_TRADING=False iken sadece loglar, emir açmaz.
"""
from __future__ import annotations

import sys
import time
import csv
import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import requests

try:
    import MetaTrader5 as mt5
except ImportError:
    print("HATA: MetaTrader5 paketi yok. Kur:  pip install -r requirements.txt")
    sys.exit(1)

import config
import reflex_exec
from sr_zones import detect_zones, plan_sr_entry, momentum_stretch
from channel_filter import is_channel_rejection, is_mean_reversion, adx_from_bars

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("demo_bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("demo-bot")

TRADE_CSV = "demo_trades.csv"
FINGERPRINT_FILE = "entry_fingerprints.jsonl"   # SL forensiği için giriş bağlamı
_ENTRY_CTX: dict = {}                            # _route_open doldurur, parmak izi okur

# ForexSAI sinyal endpoint'leri (model adı → URL şablonu, cevap alanı)
PULSE_ENDPOINTS = {
    "pulse1": ("/api/panel/pulse/{sym}", "signal"),
    "pulse2": ("/api/panel/pulse-ml/{sym}", "signal"),
    "pulse3": ("/api/panel/pulse-v3/{sym}", "direction"),
}


# ─── MT5 bağlantısı ──────────────────────────────────────────────────────────

def connect_mt5() -> bool:
    """Demo terminaline bağlan + hesaba giriş yap.

    İki mod (2026-07-22 kutu düzeltmesi):
      * LOGIN modu  — MT5_ACCOUNT dolu: login/password/server ile bağlan.
      * ATTACH modu — MT5_ACCOUNT 0/boş: AÇIK terminale kwargs'sız bağlan
        (login=0 göndermek MT5'te '(-2, Invalid params)' verir ve bot açılışta
        ölür — kutu 1 gün bu yüzden kapalı kaldı).
    """
    if config.MT5_ACCOUNT:
        kwargs = dict(login=config.MT5_ACCOUNT,
                      password=config.MT5_PASSWORD,
                      server=config.MT5_SERVER)
        if config.MT5_TERMINAL_PATH:
            ok = mt5.initialize(config.MT5_TERMINAL_PATH, **kwargs)
        else:
            ok = mt5.initialize(**kwargs)
    else:                                   # attach: açık terminale bağlan
        if config.MT5_TERMINAL_PATH:
            ok = mt5.initialize(config.MT5_TERMINAL_PATH)
        else:
            ok = mt5.initialize()
    if not ok:
        log.error("mt5.initialize başarısız: %s", mt5.last_error())
        return False
    info = mt5.account_info()
    if info is None:
        log.error("account_info None — giriş başarısız: %s", mt5.last_error())
        return False
    log.info("Bağlandı | hesap=%s  bakiye=%.2f %s  broker=%s",
             info.login, info.balance, info.currency, info.company)
    return True


def _looks_like_stock(name: str) -> bool:
    """Hisse sembolleri borsa son ekiyle gelir (AAPL.NAS, X.NYSE) — endeks/
    emtia asla nokta içermez. Bu sembolleri ASLA endeks diye seçme."""
    return "." in name


def check_autotrading(verbose: bool = True) -> bool:
    """AutoTrading açık mı? retcode 10027'nin tek sebebi budur.

    Botun BAĞLANDIĞI terminalin yolunu da yazar — 2 MT5 varsa, AutoTrading'i
    yanlış terminalde açmış olabilirsin; doğru terminali burası gösterir."""
    term = mt5.terminal_info()
    acc = mt5.account_info()
    if term is None:
        log.error("terminal_info() None — terminale bağlı değil"); return False
    if verbose:
        log.info("Bağlı terminal:  %s", term.path)
        log.info("  AutoTrading (terminal düğmesi): %s",
                 "AÇIK ✓" if term.trade_allowed else "KAPALI ✗")
        if acc is not None:
            log.info("  Hesap işlem izni: %s | EA/algo izni: %s",
                     getattr(acc, "trade_allowed", "?"),
                     getattr(acc, "trade_expert", "?"))
    if not term.trade_allowed:
        log.error("══════════════════════════════════════════════════════════")
        log.error(" AUTOTRADING KAPALI → tüm emirler retcode 10027 ile reddedilir")
        log.error(" ŞU terminalde 'Algo Trading' düğmesine bas (yeşil olsun):")
        log.error("   %s", term.path)
        log.error(" + Tools → Options → Expert Advisors → 'Allow algorithmic")
        log.error("   trading' kutusunu işaretle.")
        log.error("══════════════════════════════════════════════════════════")
        return False
    if acc is not None and getattr(acc, "trade_expert", True) is False:
        log.error("Hesap EA/algo işlemine kapalı (account.trade_expert=False) — "
                  "brokerla/hesap tipiyle ilgili olabilir.")
        return False
    return True


def resolve_symbol(forexsai_sym: str) -> str | None:
    """ForexSAI sembolünü broker sembolüne çevir, terminalde doğrula.

    GÜVENLİK: yanlış enstrümanda işlem açmamak için — config'teki ad birebir
    bulunamazsa, sadece NOKTA İÇERMEYEN (hisse olmayan) ve spesifik endeks
    anahtar kelimelerini içeren bir aday kabul eder. Hiçbiri yoksa None
    döner ve o scope atlanır (yanlış sembolde işlem açmaktansa hiç açma)."""
    want = config.SYMBOL_MAP.get(forexsai_sym, forexsai_sym)
    if mt5.symbol_info(want) is not None:
        mt5.symbol_select(want, True)
        return want

    # Bilerek dar, spesifik anahtar kelimeler — kısa "NAS"/"GER" yok.
    needles = {
        "NDX.INDX":    ["USTEC", "NAS100", "US100", "NDX100", "USTECH", "NQ100"],
        "GDAXI.INDX":  ["DE40", "GER40", "GER30", "DAX40", "GERMANY40", "DAX30"],
        "USOIL.FOREX": ["XTIUSD", "USOIL", "WTIUSD", "WTI", "CRUDOIL"],
        # 2026-07-28: XAU gölge scope'u için — SYMBOL_MAP'te yoktu, bu yüzden
        # gölge hiç tetiklenmiyordu (sinyal vardı ama sembol çözülemiyordu).
        "XAUUSD":      ["XAUUSD", "GOLD", "XAUUSDm", "XAU_USD"],
    }.get(forexsai_sym, [])

    for s in mt5.symbols_get() or []:
        nm = s.name.upper()
        if _looks_like_stock(s.name):       # AAPL.NAS, GERN.NAS → ASLA
            continue
        if any(nm == n or nm.startswith(n) for n in needles):
            log.warning("%s için SYMBOL_MAP '%s' bulunamadı — '%s' kullanılıyor. "
                        "config.py SYMBOL_MAP'i bu isimle güncelle.",
                        forexsai_sym, want, s.name)
            mt5.symbol_select(s.name, True)
            return s.name

    log.error("%s için güvenli broker sembolü bulunamadı (denenen: '%s'). "
              "Bu scope ATLANIYOR — config.py SYMBOL_MAP'e doğru adı yaz.",
              forexsai_sym, want)
    return None


# ─── ForexSAI sinyal çekme ───────────────────────────────────────────────────

def fetch_pulse(model: str, forexsai_sym: str) -> dict | None:
    """Bir pulse modelinin canlı sinyalini çeker."""
    path, _ = PULSE_ENDPOINTS[model]
    url = config.FOREXSAI_API + path.format(sym=forexsai_sym)
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("%s/%s sinyal alınamadı: %s", model, forexsai_sym, e)
        return None


def fetch_bot_trade_signal(forexsai_sym: str, direction: str,
                            confidence: float = 75.0,
                            model_type: str = "ensemble") -> dict | None:
    """ForexSAI backend'in tek-paket trade endpoint'ini çağır.
    Stage 4 sizing + Entry Optimizer + Precision Veto kararlarını birleştirir.
    None döner = network hatası → bot eski mantıkla fallback yapsın."""
    url = config.FOREXSAI_API.rstrip("/") + "/api/bot/trade-signal"
    body = {"symbol": forexsai_sym, "direction": direction,
            "confidence": confidence, "model_type": model_type, "timeframe": "15m"}
    # Railway backend trafik kesilince UYUR; ilk istek cold-start'ta 502/503/504 döner
    # (~5-15s uyanır). Geçici hatada kısa bekleyip RETRY → 2. istek 200 alır. Yoksa momentum
    # scope'ları (NDX:BUY dahil) backend uyandığı sırada sürekli atlanır.
    for attempt in range(3):
        try:
            r = requests.post(url, json=body, timeout=25)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (502, 503, 504) and attempt < 2:
                time.sleep(4 + attempt * 3)        # 4s, 7s — cold-start'ı uyandır
                continue
            log.warning("[bot-signal] %s %s HTTP %d", forexsai_sym, direction, r.status_code)
            return None
        except Exception as e:
            if attempt < 2:
                time.sleep(4); continue
            log.warning("[bot-signal] %s %s ERR: %s", forexsai_sym, direction, e)
    return None


def signal_direction(model: str, payload: dict) -> tuple[str, str]:
    """(yön, signal_type) döndürür — yön: BUY/SELL/HOLD."""
    if not payload:
        return "HOLD", ""
    _, field = PULSE_ENDPOINTS[model]
    direction = str(payload.get(field) or "HOLD").upper()
    stype = str(payload.get("signal_type") or "").upper()
    return direction, stype


# ─── Pozisyon yönetimi ───────────────────────────────────────────────────────

def _bot_magics() -> set:
    """Botun tüm magic'leri (momentum + channel_reversion + vix_regime) — global sayım."""
    m = {config.MAGIC_NUMBER}
    if getattr(config, "CHANNEL_REVERSION_ENABLED", False):
        m.add(config.CHANNEL_REVERSION_MAGIC)
    if getattr(config, "VIX_REGIME_ENABLED", False):
        m.add(config.VIX_REGIME_MAGIC)
    return m


# Kod-seviyesi lot çarpanı varsayılanları (config.py gitignore'da olduğu için
# yeni scope'un DÜŞÜK lotu burada; config.SCOPE_LOT_FACTOR bunları ezer).
# DAYCOMBO 0.2 → kutudaki LOT_SIZE=5 ile 1.0 lot (kullanıcı kararı 2026-07-28:
# canlı ama düşük lot; n≥30 işlem doğrulaması sonrası artırılır).
SCOPE_LOT_FACTOR_DEFAULT = {"NDX.INDX:BUY:DAYCOMBO": 0.2}


def scope_lot(scope_key: str) -> float:
    """Scope'a özel lot (2026-07-28). LOT_SIZE global; kanıtı zayıf/yeni bir scope'u
    yarı riskle canlıya almak için scope başına çarpan gerekiyordu.

    config.SCOPE_LOT_FACTOR = {"XAUUSD:BUY": 0.5} gibi; tanımsızsa 1.0 (davranış aynı).
    Backend'in effective_lot_multiplier'ı bunun ÜSTÜNE çarpılır (ikisi bağımsız)."""
    defaults = dict(SCOPE_LOT_FACTOR_DEFAULT)
    defaults.update(getattr(config, "SCOPE_LOT_FACTOR", {}) or {})
    factor = float(defaults.get(scope_key, 1.0))
    return round(float(config.LOT_SIZE) * factor, 2)


def open_count(mt5_symbol: str, direction: str, magic: int | None = None) -> int:
    """Bu sembol+yön+magic'teki açık pozisyon sayısı (magic=None → momentum magic)."""
    magic = config.MAGIC_NUMBER if magic is None else magic
    positions = mt5.positions_get(symbol=mt5_symbol) or []
    want = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    return sum(1 for p in positions if p.magic == magic and p.type == want)


def pending_count(mt5_symbol: str, direction: str, magic: int | None = None) -> int:
    """Bu sembol+yön+magic'teki BEKLEYEN limit emir sayısı."""
    magic = config.MAGIC_NUMBER if magic is None else magic
    orders = mt5.orders_get(symbol=mt5_symbol) or []
    want = (mt5.ORDER_TYPE_BUY_LIMIT if direction == "BUY"
            else mt5.ORDER_TYPE_SELL_LIMIT)
    return sum(1 for o in orders if o.magic == magic and o.type == want)


def total_open_positions() -> int:
    """Botun TÜM açık pozisyonu (her iki magic; global tavan için)."""
    magics = _bot_magics()
    return sum(1 for p in (mt5.positions_get() or []) if p.magic in magics)


def today_realized_pnl() -> float:
    """Bugün (UTC) botun realize net P/L (her iki magic; günlük zarar freni)."""
    from datetime import time as _dtime
    magics = _bot_magics()
    start = datetime.combine(datetime.now(timezone.utc).date(), _dtime.min,
                             tzinfo=timezone.utc)
    deals = mt5.history_deals_get(start, datetime.now(timezone.utc)) or []
    return sum(d.profit + d.swap + getattr(d, "commission", 0.0)
               for d in deals if d.magic in magics)


def candles_1m(mt5_symbol: str, n: int) -> list[dict] | None:
    """Son n adet kapalı 1m mumu MT5'ten çek (high/low/close)."""
    return candles_tf(mt5_symbol, mt5.TIMEFRAME_M1, n)


def candles_tf(mt5_symbol: str, timeframe: int, n: int) -> list[dict] | None:
    """Son n adet kapalı mumu verilen timeframe'de MT5'ten çek (hacim dahil — VWAP için)."""
    rates = mt5.copy_rates_from_pos(mt5_symbol, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        return None
    return [{"high": float(r["high"]), "low": float(r["low"]),
             "close": float(r["close"]), "volume": float(r["tick_volume"])}
            for r in rates]


def atr_5m(mt5_symbol: str, n: int = 14) -> float | None:
    """ATR(n) — son KAPANMIŞ 5m barlardan (koşan bar hariç). Sızıntısız."""
    rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M5, 1, n + 1)
    if rates is None or len(rates) < n + 1:
        return None
    trs = []
    for i in range(1, len(rates)):
        h, l = float(rates[i]["high"]), float(rates[i]["low"])
        pc = float(rates[i - 1]["close"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / len(trs) if trs else None


def adaptive_sl(mt5_symbol: str, scope_key: str, fallback_sl: float) -> float:
    """Volatiliteye uyarlamalı SL = MULT × ATR(14, 5m), taban/tavan sınırlı.

    KANIT (research/sl_opt/RAPOR.md, 5.5 ay · 8.129 NDX SELL sinyali · zaman
    kayması düzeltilmiş · trend+konum kapılı):
        sabit TP80/SL110  → 4/6 ay pozitif · OUT +10.18R · P=%93.6
        TP80 / SL 2.0×ATR → 6/6 ay pozitif · OUT +23.61R · P=%99.5
    Mart hariç bile canlının 2.6 katı. Ortalama SL ≈104p (mevcut 110'a yakın) —
    kazanç "daha geniş stop"tan DEĞİL, stopun sakin piyasada daralıp oynak
    piyasada genişlemesinden geliyor. 36 varyant tarandı; aylık dayanıklılık +
    kronolojik split + blok-bootstrap ile dengelendi.

    Fail-safe: ATR alınamazsa sabit değere döner (davranış değişmez).
    """
    if not getattr(config, "VIXREG_SL_ATR_ENABLED", True):
        return fallback_sl
    atr = atr_5m(mt5_symbol)
    if not atr or atr <= 0:
        log.warning("%s — ATR alınamadı, sabit SL %.0f kullanılıyor",
                    scope_key, fallback_sl)
        return fallback_sl
    mult = float(getattr(config, "VIXREG_SL_ATR_MULT", 2.0))
    lo = float(getattr(config, "VIXREG_SL_MIN", 60.0))
    hi = float(getattr(config, "VIXREG_SL_MAX", 200.0))
    sl = max(lo, min(hi, mult * atr))
    log.info("%s — uyarlamalı SL: ATR(5m)=%.1f × %.1f = %.1f puan "
             "(sabit %.0f yerine)", scope_key, atr, mult, sl, fallback_sl)
    return round(sl, 1)


def _mk_comment(prefix: str, tag: str) -> str:
    """MT5 order comment'i GÜVENLİ üret: ASCII + ≤28 karakter. UZUN comment (≥31) →
    order_send '(-2, Invalid "comment" argument)' verir ve emir HİÇ açılmaz (CHREV/VIXREG
    market girişlerini bu öldürüyordu). 28 karakter brokerda doğrulanmış güvenli sınır."""
    c = f"{prefix}{tag}".encode("ascii", "ignore").decode()
    return c[:28]


def _send_market_order(request: dict, mt5_symbol: str):
    """order_send'i broker'ın DESTEKLEDİĞİ filling-mode'larla dene.

    retcode=10030 düzeltmesi (2026-07-22): SpotCrude/XTIUSD gibi bazı semboller
    IOC da FOK da kabul etmiyor → symbol_info.filling_mode bitmask'inden
    desteklenenleri sırayla dene (IOC → FOK → RETURN). 34 USOIL:BUY emri bu
    yüzden hiç açılamamıştı.
    """
    info = mt5.symbol_info(mt5_symbol)
    fm = getattr(info, "filling_mode", 0) if info else 0
    modes = []
    if fm & 2:
        modes.append(mt5.ORDER_FILLING_IOC)
    if fm & 1:
        modes.append(mt5.ORDER_FILLING_FOK)
    modes.append(mt5.ORDER_FILLING_RETURN)      # son çare (bazı broker default'u)
    # bitmask okunamadıysa eski davranışa yakın tam sıra dene
    if not (fm & 3):
        modes = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK,
                 mt5.ORDER_FILLING_RETURN]
    result = None
    for mode in modes:
        request["type_filling"] = mode
        result = mt5.order_send(request)
        if result is None:
            log.error("order_send None (mode=%s): %s", mode, mt5.last_error())
            continue
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return result
        if result.retcode != 10030:             # filling hatası değilse deneme boşa
            return result
        log.info("filling mode %s reddedildi (10030) — sonraki deneniyor", mode)
    return result


# ── ATR-ÖLÇEKLİ GEOMETRİ (2026-07-28, research/ndx_buy_lab/RAPOR.md) ─────────
# BULGU: NDX BUY'ın sabit TP 80 / SL 110 geometrisi (RR 0.73 = hedef yalnız
# 0.67 ATR) 11 yılda EV −0.056R, hafta-bloklu %95 GA [−0.068, −0.044], P(EV>0)=%0.
# Hedef çok yakın olduğu için momentum filtresinin seçtiği "devam edecek"
# hareketler devam etmeden kâr alınıyor.
#
# ÖLÇÜM (3.4 yıl, 79.902 deneme, saat-eşitlenmiş taban, 1.3 puan ÖLÇÜLMÜŞ
# sürtünme, hafta-bloklu güven aralığı):
#     geometri                    kapı yok    + momentum filtresi
#     bot eski (0.67/0.92 ATR)     −0.020R      +0.012R  (P=%77,   2/4 yıl)
#     ATR 2.0 / 1.0                +0.019R      +0.079R  (P=%96.4, 4/4 yıl)
#     ATR 3.0 / 1.0                +0.059R      +0.111R  (P=%97.9, 4/4 yıl)
# Filtrenin katkısı sürükleme çıkarılmış seride de ayakta (+0.054R) → beta değil.
#
# KAPSAM: yalnız "NDX.INDX:BUY" (momentum/SR). CHREV ve VIXREG scope anahtarları
# farklı (":CHREV" / ":VIXREG") → ETKİLENMEZ. SELL ve diğer semboller dışarıda —
# kanıt onları kapsamıyor.
# 2026-07-28 KULLANICI KARARI: varsayılan KAPALI. Kullanıcı yüksek kazanma
# oranı istiyor; uzak-hedef/düşük-WR profili istemiyor. Açmak için kutuda
# config.py'a ATR_GEOMETRY_ENABLED = True yaz.
ATR_GEOMETRY_DEFAULT = {
    "NDX.INDX:BUY": {
        # 2026-07-28 kullanıcı kararı: KAPALI (uzak-hedef/düşük-WR profili
        # istenmiyor). Kayıt olarak duruyor; "enabled": True ile açılır.
        "enabled": False,
        "tf": "1h", "period": 14, "tp_mult": 2.0, "sl_mult": 1.0,
        "sl_min": 70.0, "sl_max": 200.0, "tp_min": 140.0, "tp_max": 400.0,
    },
    # ── DAX: TP SABİT + SL uyarlamalı (2026-07-29 kullanıcı onayı) ──────────
    # Kanıt: research/sl_opt/USOIL_DAX_RAPOR.md — 5.5 ay, 14.043 sinyal,
    # zaman kayması düzeltilmiş, trend+konum kapılı:
    #   BUY  sabit 67/119 → 4/6 ay pozitif, +16.6R  |  SL 2.0×ATR → 6/6 ay, +72.4R
    #   SELL sabit 67/119 → 4/6 ay pozitif, +50.9R  |  SL 2.0×ATR → 5/6 ay, +110.4R
    # KAYMA TESTİ belirleyici oldu: sürtünme 3× yapıldığında DAX'ta ATR-SL hâlâ
    # sabitten iyi (SELL +90 vs +40) — USOIL'de tersi olduğu için USOIL'e
    # DOKUNULMADI (orada 3× kaymada −134'e düşüyor).
    # ⚠️ Ödünleşim kayıtlı: WR düşüyor (BUY %73.6→%56.5, SELL %81.9→%64.7);
    # kâr 2-4 kat artıyor. Kullanıcı bu ödünleşimi bilerek onayladı.
    # TP bilerek SABİT: TP'yi de ATR'ye bağlamak aylık dayanıklılığı düşürüyor.
    "GDAXI.INDX:BUY": {
        "enabled": True, "tf": "5m", "period": 14,
        "tp_fixed": 67.0, "sl_mult": 2.0,
        # 5m ATR ort. 23.6p → SL ~47p; test aralığı 35-83p.
        "sl_min": 30.0, "sl_max": 120.0,
    },
    # NOT: GDAXI.INDX:SELL momentum scope'u config.ROBUST_SCOPES'ta YOK
    # (2026-06-24'te OOS'ta çöktüğü için çıkarıldı) → bu girdi şu an ÖLÜ.
    # DAX SELL ileride açılırsa hazır olsun diye bırakıldı. CHREV'in anahtarı
    # "GDAXI.INDX:SELL:CHREV" olduğu için mean-reversion kolu ETKİLENMEZ
    # (kanıt momentum sinyallerinden geldi, chrev farklı popülasyon).
    "GDAXI.INDX:SELL": {
        "enabled": True, "tf": "5m", "period": 14,
        "tp_fixed": 67.0, "sl_mult": 2.0,
        "sl_min": 30.0, "sl_max": 120.0,          # 5m ATR ort. 27.6p → SL ~55p
    },
}

_ATR_TF_MAP = {"5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
               "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1,
               "4h": mt5.TIMEFRAME_H4}


def _atr_distances(scope_key: str, mt5_symbol: str) -> tuple[float, float] | None:
    """ATR-ölçekli tp/sl mesafesi (config.ATR_GEOMETRY). Kapsam dışıysa veya
    hesaplanamıyorsa None → çağıran sabit geometriye düşer (fail-open).

    Gerekçe: research/ndx_buy_lab/RAPOR.md — sabit 80/110 (hedef 0.67 ATR)
    11 yılda −EV; momentum filtresinin kenarı ancak TP ≥ 1.5-2 ATR'de ödüyor.
    """
    spec = (getattr(config, "ATR_GEOMETRY", None) or ATR_GEOMETRY_DEFAULT).get(scope_key)
    if not spec:
        return None
    # Kapsam artık SCOPE BAZLI ("enabled"). Eskiden tek global bayrak vardı ve
    # onu açmak kullanıcının reddettiği NDX:BUY profilini de açıyordu.
    # ATR_GEOMETRY_ENABLED=False hâlâ hepsini birden kapatır (acil fren).
    if not spec.get("enabled", False):
        return None
    if getattr(config, "ATR_GEOMETRY_ENABLED", True) is False:
        return None
    try:
        tf = _ATR_TF_MAP.get(spec.get("tf", "1h"), mt5.TIMEFRAME_H1)
        period = int(spec.get("period", 14))
        rates = mt5.copy_rates_from_pos(mt5_symbol, tf, 1, period * 6)
        if rates is None or len(rates) < period + 2:
            log.warning("[ATR-GEO] %s: bar yok → sabit geometri", scope_key)
            return None
        h = [float(r["high"]) for r in rates]
        l = [float(r["low"]) for r in rates]
        c = [float(r["close"]) for r in rates]
        # Wilder ATR (indicators._atr ile aynı tanım)
        trs = [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
               for i in range(1, len(c))]
        atr = sum(trs[:period]) / period
        for x in trs[period:]:
            atr = (atr * (period - 1) + x) / period
        if not atr or atr <= 0:
            return None
        # tp_fixed verilmişse TP SABİT kalır, yalnız SL uyarlamalı olur
        # (DAX/NDX-SELL kanıtı bu biçimde ölçüldü — TP'yi de ATR'ye bağlamak
        #  aylık dayanıklılığı düşürüyordu).
        tp_fixed = spec.get("tp_fixed")
        tp_d = float(tp_fixed) if tp_fixed else atr * float(spec.get("tp_mult", 2.0))
        sl_d = atr * float(spec.get("sl_mult", 1.0))
        if not tp_fixed:
            tp_d = min(max(tp_d, float(spec.get("tp_min", 0))), float(spec.get("tp_max", 1e9)))
        sl_d = min(max(sl_d, float(spec.get("sl_min", 0))), float(spec.get("sl_max", 1e9)))
        log.info("[ATR-GEO] %s: ATR(%s,%d)=%.1f → TP %.1f%s / SL %.1f (RR %.2f)",
                 scope_key, spec.get("tf", "1h"), period, atr, tp_d,
                 " sabit" if tp_fixed else "", sl_d, tp_d / sl_d)
        return tp_d, sl_d
    except Exception as e:
        log.warning("[ATR-GEO] %s hesaplanamadı (%s) → sabit geometri", scope_key, e)
        return None


def _fixed_distances(price: float, cfg: dict, bot_signal: dict | None,
                     scope_key: str = "", mt5_symbol: str = "") -> tuple[float, float]:
    """tp/sl mesafesi. Scope ATR_GEOMETRY kapsamındaysa ATR-ölçekli, değilse
    araştırılmış sabit değerler (index: puan, USOIL: %)."""
    atr_geo = _atr_distances(scope_key, mt5_symbol) if scope_key and mt5_symbol else None
    if atr_geo is not None:
        tp_d, sl_d = atr_geo
    elif cfg["is_pct"]:
        tp_d = price * cfg["tp"] / 100.0
        sl_d = price * cfg["sl"] / 100.0
    else:
        tp_d = float(cfg["tp"])
        sl_d = float(cfg["sl"])
    # Backend'in optimize SL'i yalnız SABİT geometride devreye girer — ATR
    # geometrisi kendi stop mesafesini araştırmadan alır, ezilmemeli.
    if atr_geo is None and bot_signal and bot_signal.get("sl_price"):
        d = abs(price - float(bot_signal["sl_price"]))
        if d > 0:
            sl_d = d
    return tp_d, sl_d


def open_trade_sr(scope_key: str, forexsai_sym: str, mt5_symbol: str,
                  direction: str, cfg: dict, voters: list[str],
                  bot_signal: dict | None = None,
                  candles: list[dict] | None = None) -> None:
    """1m S/R-temelli pending-LIMIT giriş.
    BUY → en yakın DESTEK'ten, SELL → en yakın DİRENÇ'ten. TP = bir sonraki S/R.
    Uygun S/R yoksa/çok uzaksa işlem AÇILMAZ (kovalama yok)."""
    info = mt5.symbol_info(mt5_symbol)
    tick = mt5.symbol_info_tick(mt5_symbol)
    if info is None or tick is None:
        log.error("%s tick/info alınamadı", mt5_symbol); return
    digits = info.digits
    price = tick.ask if direction == "BUY" else tick.bid

    # Sahte-kırılım vetosu (4 sembol, OOS %70/%70+; fail-open — FAKEOUT_VETO=0 kapatır)
    try:
        from fakeout_veto import fakeout_check
        allow, veto_reason = fakeout_check(mt5, mt5_symbol, forexsai_sym, direction)
        if not allow:
            _log_trade("FAKEOUT_VETO", scope_key, mt5_symbol, direction, price, 0, 0,
                       voters, veto_reason)
            return
    except Exception as _fx_exc:
        log.debug("fakeout veto fail-open: %s", _fx_exc)

    fixed_tp, fixed_sl = _fixed_distances(price, cfg, bot_signal,
                                          scope_key, mt5_symbol)

    if candles is None:
        candles = candles_1m(mt5_symbol, config.ZONE_LOOKBACK)
    if candles is None or len(candles) < 30:
        log.warning("%s — 1m mum yok/az (%s), S/R hesaplanamadı, atlandı",
                    scope_key, 0 if candles is None else len(candles))
        return

    width = config.ZONE_WIDTH.get(forexsai_sym, fixed_sl)
    zones = detect_zones(candles, width=width,
                         min_touch_candles=config.ZONE_MIN_TOUCH_CANDLES,
                         lookback=config.ZONE_LOOKBACK)
    plan = plan_sr_entry(
        zones, direction, price,
        fixed_tp_dist=fixed_tp, fixed_sl_dist=fixed_sl,
        max_entry_dist=config.SR_MAX_ENTRY_DIST.get(forexsai_sym, fixed_sl * 2),
        # RR tabanı (2026-07-23): S/R TP'si en az SL mesafesinin %30'u olsun.
        # Mutlak taban (NDX 15p) tek başına yetersizdi — SL 91p iken 16p TP'ye
        # izin verdi (RR 0.18, ekran görüntüsü ticket 345898883); USOIL'de
        # RR~0.1 kırıntı-TP'ler açıldı. Yakın S/R bu tabanı geçemezse plan
        # sabit TP'ye (araştırılmış geometri) düşer.
        min_tp_dist=max(config.SR_MIN_TP_DIST.get(forexsai_sym, 0.0),
                        0.3 * fixed_sl))

    if plan is None:
        kind = "destek" if direction == "BUY" else "direnç"
        log.info("%s — uygun %s yok (%d bölge) → AÇILMADI (kovalama yok)",
                 scope_key, kind, len(zones))
        _log_trade("NO_SR", scope_key, mt5_symbol, direction, price, 0, 0,
                   voters, f"zones={len(zones)}")
        if config.SR_FALLBACK_MARKET:
            if bot_signal:
                open_trade_v2(scope_key, forexsai_sym, mt5_symbol, direction,
                              cfg, voters, bot_signal)
            else:
                open_trade(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters)
        return

    entry = round(plan.entry, digits)
    tp = round(plan.tp, digits)
    sl = round(plan.sl, digits)

    # Broker min-stop mesafesi: S/R fiyata çok yakınsa limit emir reddedilir (10016).
    min_gap = (getattr(info, "trade_stops_level", 0) or 0) * info.point
    gap = (price - entry) if direction == "BUY" else (entry - price)
    if gap < min_gap:
        log.info("%s — S/R seviyesi fiyata çok yakın (gap=%.5f < min=%.5f) → atlandı",
                 scope_key, gap, min_gap)
        _log_trade("SR_TOO_CLOSE", scope_key, mt5_symbol, direction, price, tp, sl,
                   voters, f"gap={gap:.5f}")
        return

    volume = scope_lot(scope_key)
    if bot_signal and bot_signal.get("effective_lot_multiplier"):
        volume = round(volume * float(bot_signal["effective_lot_multiplier"]), 2)
        if volume < 0.01:
            log.info("%s — lot çok düşük, atlandı", scope_key); return

    line = (f"{scope_key} | {mt5_symbol} {direction} LIMIT @ {entry} "
            f"TP={tp}[{plan.tp_source}] SL={sl} lot={volume} | fiyat={price} "
            f"({plan.entry_zone.touches} dokunuşlu bölge, toplam {len(zones)} S/R)")

    if not config.LIVE_TRADING:
        log.info("[GÖZLEM] S/R-LIMIT açardım → %s", line)
        _log_trade("OBSERVE_SR", scope_key, mt5_symbol, direction, entry, tp, sl,
                   voters, f"tp_src={plan.tp_source} zones={len(zones)}")
        return

    if pending_count(mt5_symbol, direction) >= config.MAX_OPEN_PER_SCOPE:
        log.info("%s — zaten bekleyen limit emir var, atlandı", scope_key); return
    if not check_autotrading(verbose=False):
        log.error("[CANLI] ⏸ AutoTrading KAPALI — emir gönderilmedi. %s", line); return

    order_type = (mt5.ORDER_TYPE_BUY_LIMIT if direction == "BUY"
                  else mt5.ORDER_TYPE_SELL_LIMIT)
    # MT5 expiration'ı SUNUCU saatine göre yorumlar → broker saatini (tick.time) baz
    # al, UTC (time.time()) DEĞİL; yoksa GMT+2/+3 broker'da emir anında iptal olabilir.
    server_now = int(tick.time) if getattr(tick, "time", 0) else int(time.time())
    expiration = server_now + config.PENDING_EXPIRY_MIN * 60
    request = {
        "action": mt5.TRADE_ACTION_PENDING, "symbol": mt5_symbol,
        "volume": volume, "type": order_type, "price": entry,
        "sl": sl, "tp": tp, "magic": config.MAGIC_NUMBER,
        "comment": _mk_comment("fxs-sr ", scope_key),
        "type_time": mt5.ORDER_TIME_SPECIFIED, "expiration": expiration,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    result = mt5.order_send(request)
    if result is None:
        log.error("order_send None: %s", mt5.last_error()); return
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("[CANLI] ✅ LIMIT kuruldu ticket=%s (≤%ddk) → %s",
                 result.order, config.PENDING_EXPIRY_MIN, line)
        _log_trade("LIVE_SR", scope_key, mt5_symbol, direction, entry, tp, sl,
                   voters, f"ticket={result.order} tp_src={plan.tp_source}")
        record_fingerprint(result.order, scope_key, mt5_symbol, direction,
                           entry, tp, sl, volume, "sr_limit", plan.tp_source, voters,
                           bot_signal, extra={"entry_zone_touches": plan.entry_zone.touches,
                                              "n_zones": len(zones)})
    else:
        log.error("[CANLI] ❌ LIMIT reddedildi retcode=%s → %s",
                  result.retcode, line)


def open_trade(scope_key: str, forexsai_sym: str, mt5_symbol: str,
               direction: str, cfg: dict, voters: list[str],
               magic: int | None = None) -> None:
    """Türetilmiş TP/SL ile market emri aç."""
    magic = config.MAGIC_NUMBER if magic is None else magic
    tick = mt5.symbol_info_tick(mt5_symbol)
    info = mt5.symbol_info(mt5_symbol)
    if tick is None or info is None:
        log.error("%s tick/info alınamadı", mt5_symbol); return

    # Sahte-kırılım vetosu (fail-open; FAKEOUT_VETO=0 kapatır)
    try:
        from fakeout_veto import fakeout_check
        allow, veto_reason = fakeout_check(mt5, mt5_symbol, forexsai_sym, direction)
        if not allow:
            _log_trade("FAKEOUT_VETO", scope_key, mt5_symbol, direction,
                       tick.ask if direction == "BUY" else tick.bid, 0, 0,
                       voters, veto_reason)
            return
    except Exception as _fx_exc:
        log.debug("fakeout veto fail-open: %s", _fx_exc)

    price = tick.ask if direction == "BUY" else tick.bid
    # Türetilmiş TP/SL mesafesi — ATR_GEOMETRY kapsamındaysa ATR-ölçekli,
    # değilse araştırılmış sabit (index: puan, USOIL: yüzde).
    tp_dist, sl_dist = _fixed_distances(price, cfg, None, scope_key, mt5_symbol)

    if direction == "BUY":
        tp, sl = price + tp_dist, price - sl_dist
        order_type = mt5.ORDER_TYPE_BUY
    else:
        tp, sl = price - tp_dist, price + sl_dist
        order_type = mt5.ORDER_TYPE_SELL

    digits = info.digits
    tp, sl, price = round(tp, digits), round(sl, digits), round(price, digits)
    volume = scope_lot(scope_key)

    line = (f"{scope_key} | {mt5_symbol} {direction} @ {price} "
            f"TP={tp} SL={sl} lot={volume} (oy: {','.join(voters)})")

    if not config.LIVE_TRADING:
        log.info("[GÖZLEM] Açardım → %s", line)
        _log_trade("OBSERVE", scope_key, mt5_symbol, direction, price, tp, sl, voters, "")
        return

    # AutoTrading kapalıysa emri hiç gönderme — kriptik 10027 yerine net mesaj.
    if not check_autotrading(verbose=False):
        log.error("[CANLI] ⏸ AutoTrading KAPALI — emir gönderilmedi. %s", line)
        log.error("        → bağlı terminalde 'Algo Trading' düğmesini yeşil yap.")
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": mt5_symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": config.DEVIATION_POINTS,
        "magic": magic,
        "comment": _mk_comment("fxs ", scope_key),
        "type_time": mt5.ORDER_TIME_GTC,
    }
    result = _send_market_order(request, mt5_symbol)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("[CANLI] ✅ Açıldı ticket=%s → %s", result.order, line)
        _log_trade("LIVE", scope_key, mt5_symbol, direction, price, tp, sl,
                   voters, f"ticket={result.order}")
    else:
        rc = result.retcode if result else "?"
        log.error("[CANLI] ❌ Emir reddedildi retcode=%s → %s", rc, line)


def open_trade_v2(scope_key: str, forexsai_sym: str, mt5_symbol: str,
                   direction: str, cfg: dict, voters: list[str],
                   bot_signal: dict) -> None:
    """Backend'in optimized SL/TP + lot multiplier ile market emri aç.
    Stage 4 sizing + Entry Optimizer kararları uygulanır."""
    info = mt5.symbol_info(mt5_symbol)
    if info is None:
        log.error("%s info alınamadı", mt5_symbol); return
    digits = info.digits

    # Sahte-kırılım vetosu (fail-open; FAKEOUT_VETO=0 kapatır)
    try:
        from fakeout_veto import fakeout_check
        allow, veto_reason = fakeout_check(mt5, mt5_symbol, forexsai_sym, direction)
        if not allow:
            _log_trade("FAKEOUT_VETO", scope_key, mt5_symbol, direction, 0, 0, 0,
                       voters, veto_reason)
            return
    except Exception as _fx_exc:
        log.debug("fakeout veto fail-open: %s", _fx_exc)

    tick = mt5.symbol_info_tick(mt5_symbol)
    if tick is None:
        log.error("%s tick alınamadı", mt5_symbol); return
    price = tick.ask if direction == "BUY" else tick.bid

    sl = float(bot_signal.get("sl_price") or price)
    tp = float(bot_signal.get("tp_price") or price)
    price, sl, tp = round(price, digits), round(sl, digits), round(tp, digits)

    # Geometri sanity (2026-07-23): backend planı LIMIT bölgesine göre hesaplanır;
    # fiyat kaçtıysa TP/SL market fiyatının YANLIŞ tarafında kalır → broker 10016
    # ("invalid stops") reddi (USOIL'de 15+ ret) ya da daha kötüsü RR~0 emir
    # açılır (ticket 345913572: TP +0.14 / SL −2.05). Yanlış taraf veya
    # TP < 0.3×SL mesafesi → araştırılmış sabit geometriye düş.
    sign = 1 if direction == "BUY" else -1
    tp_d, sl_d = sign * (tp - price), sign * (price - sl)
    if tp_d <= 0 or sl_d <= 0 or tp_d < 0.3 * sl_d:
        f_tp, f_sl = _fixed_distances(price, cfg, None, scope_key, mt5_symbol)
        log.warning("%s — backend TP/SL bayat/bozuk (tp_d=%.3f sl_d=%.3f, "
                    "fiyat plandan kaçmış) → sabit mesafe (tp=%.3f sl=%.3f)",
                    scope_key, tp_d, sl_d, f_tp, f_sl)
        tp = round(price + sign * f_tp, digits)
        sl = round(price - sign * f_sl, digits)

    lot_mult = float(bot_signal.get("effective_lot_multiplier") or 1.0)
    volume = round(scope_lot(scope_key) * lot_mult, 2)
    if volume < 0.01:
        log.info("%s — lot çok düşük (×%.2f), atlanıyor", scope_key, lot_mult)
        return

    action = bot_signal.get("action") or "FALLBACK_MARKET"
    line = (f"{scope_key} | {mt5_symbol} {direction} @ {price} "
            f"TP={tp} SL={sl} lot={volume} (×{lot_mult:.2f}) "
            f"action={action} (oy: {','.join(voters)})")

    if not config.LIVE_TRADING:
        log.info("[GÖZLEM] %s", line)
        _log_trade("OBSERVE", scope_key, mt5_symbol, direction, price, tp, sl,
                   voters, f"action={action} lot_mult={lot_mult}")
        return

    if not check_autotrading(verbose=False):
        log.error("[CANLI] ⏸ AutoTrading KAPALI. %s", line); return

    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": mt5_symbol,
        "volume": volume, "type": order_type, "price": price,
        "sl": sl, "tp": tp, "deviation": config.DEVIATION_POINTS,
        "magic": config.MAGIC_NUMBER,
        "comment": _mk_comment("fxs-v2 ", action),
        "type_time": mt5.ORDER_TIME_GTC,
    }
    result = _send_market_order(request, mt5_symbol)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("[CANLI] ✅ Açıldı ticket=%s → %s", result.order, line)
        _log_trade("LIVE", scope_key, mt5_symbol, direction, price, tp, sl,
                   voters,
                   f"ticket={result.order} action={action} lot×{lot_mult:.2f}")
        record_fingerprint(result.order, scope_key, mt5_symbol, direction,
                           price, tp, sl, volume, "market", "backend", voters,
                           bot_signal, extra={"action": action})
    else:
        rc = result.retcode if result else "?"
        log.error("[CANLI] ❌ Emir reddedildi retcode=%s → %s", rc, line)


GATE_SKIP_JSONL = "gate_skipped.jsonl"


def log_gate_skip(scope_key: str, mt5_symbol: str, forexsai_sym: str,
                  direction: str, price: float, reason: str,
                  tp_dist: float | None = None, sl_dist: float | None = None,
                  extra: dict | None = None) -> None:
    """Bir KAPININ eledigi giris niyetini kaydet — 'filtre hakli miydi?' sorusu
    ancak boyle olculebilir (elenen sinyalin sonucu bilinmezse gevsetme karari
    tahmine dayanir). Sizintisiz: karar anindaki fiyat ve geometri yazilir,
    sonuc SONRADAN 1m barlarla replay edilir (research/gate_audit.py).
    Fail-open: yazma hatasi girisi etkilemez."""
    try:
        rec = {"ts": datetime.now(timezone.utc).isoformat(), "scope": scope_key,
               "mt5_symbol": mt5_symbol, "symbol": forexsai_sym,
               "direction": direction, "price": round(float(price), 5),
               "reason": reason, "tp_dist": tp_dist, "sl_dist": sl_dist}
        if extra:
            rec.update(extra)
        with open(GATE_SKIP_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        log.debug("gate_skip log yazilamadi: %s", exc)


def _log_trade(mode, scope, sym, direction, price, tp, sl, voters, note):
    """İşlemi CSV'ye yaz."""
    new = False
    try:
        open(TRADE_CSV).close()
    except FileNotFoundError:
        new = True
    with open(TRADE_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc", "mode", "scope", "symbol", "direction",
                        "price", "tp", "sl", "voters", "note"])
        w.writerow([datetime.now(timezone.utc).isoformat(), mode, scope, sym,
                    direction, price, tp, sl, "|".join(voters), note])


def record_fingerprint(ticket: int, scope_key: str, mt5_symbol: str, direction: str,
                       entry: float, tp: float, sl: float, lot: float,
                       entry_type: str, tp_source: str, voters: list[str],
                       bot_signal: dict | None, extra: dict | None = None) -> None:
    """Gerçek girişin 'parmak izi'ni JSONL'e yaz — SL forensiği bunu MT5 geçmişiyle
    (position_id=ticket) eşleştirip her SL'in NEDEN olduğunu analiz eder."""
    bs = bot_signal or {}
    risk = abs(entry - sl)
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ticket": int(ticket), "scope": scope_key,
        "symbol": scope_key.split(":")[0], "mt5_symbol": mt5_symbol,
        "direction": direction, "entry": entry, "tp": tp, "sl": sl, "lot": lot,
        "rr": round(abs(tp - entry) / risk, 2) if risk else None,
        "entry_type": entry_type, "tp_source": tp_source, "voters": voters,
        "mom_stretch": _ENTRY_CTX.get("mom"), "mom_threshold": _ENTRY_CTX.get("thr"),
        "session": _ENTRY_CTX.get("session"),
        "backend_action": bs.get("action"),
        "backend_conf": bs.get("adjusted_confidence") or bs.get("confidence"),
        "lot_mult": bs.get("effective_lot_multiplier"),
        "priority": bs.get("priority_score"),
    }
    if extra:
        rec.update(extra)
    try:
        with open(FINGERPRINT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("parmak izi yazılamadı: %s", e)


# ─── Giriş yönlendirici (HİBRİT) ─────────────────────────────────────────────

def _session_factor(forexsai_sym: str, now=None) -> tuple[float, str]:
    """Sembolün borsa YEREL saatine göre momentum-eşik çarpanı (+etiket, DST otomatik).
    Frankfurt açılışı / NY açılışı / EIA (petrol Çar 10:30 ET) yüksek-momentum →
    eşik düşür; gece → yükselt. tzdata yoksa UTC'ye düşer. (now: test için enjekte)."""
    tzname = config.SESSION_TZ.get(forexsai_sym, "UTC")
    tag = tzname.split("/")[-1]
    if now is None:
        try:
            now = datetime.now(ZoneInfo(tzname))
        except Exception:                   # Windows'ta tzdata yoksa
            now = datetime.now(timezone.utc); tag = "UTC?"
    h = now.hour + now.minute / 60.0

    # EIA (petrol): Çarşamba 10:30 ET penceresinde en agresif continuation
    if forexsai_sym == config.EIA_SYMBOL and now.weekday() == config.EIA_WEEKDAY:
        a, b = config.EIA_WINDOW_ET
        if a <= h < b:
            return config.SESSION_MOM_FACTOR["eia"], f"EIA/{tag}"

    for a, b in config.HIGH_MOM_WINDOWS.get(forexsai_sym, []):
        if a <= h < b:
            return config.SESSION_MOM_FACTOR["high"], f"high/{tag}"

    qa, qb = config.QUIET_LOCAL
    quiet = (h >= qa or h < qb) if qa > qb else (qa <= h < qb)
    if quiet:
        return config.SESSION_MOM_FACTOR["quiet"], f"quiet/{tag}"
    return config.SESSION_MOM_FACTOR["normal"], f"normal/{tag}"


def trend_alignment(mt5_symbol: str, direction: str) -> tuple[bool, float | None]:
    """1h EMA50 trend hizası — giriş anında botun KENDİ MT5 barlarıyla.

    Kanıt (2026-07-24, research/trend_gate, 30g × 332 canlı bot işlemi,
    hindsight testi 0/1/2/4/8h lag'de dayandı):
      trend-yönü  n=210 WR %63.3 +9.710$
      karşı-trend n=122 WR %43.4 −13.161$
    En sert ayrışma USOIL SELL'de: EMA50 üstü SELL n=29 WR %31 −3.110$.
    Kavramsal olarak da zorunlu: "momentum-continuation" trend yönünde olmalı;
    EMA50'nin ters tarafında açılan momentum girişi tanım gereği çelişki.
    Fail-open: veri yoksa (True, None) → giriş engellenmez.
    """
    bars = candles_tf(mt5_symbol, mt5.TIMEFRAME_H1, 60)
    if not bars or len(bars) < 55:
        return True, None
    closes = np.asarray([b["close"] for b in bars], dtype=float)
    k = 2.0 / 51.0
    e = float(closes[-50])
    for v in closes[-49:]:
        e = float(v) * k + e * (1 - k)
    px = float(closes[-1])
    above = px > e
    aligned = above if direction == "BUY" else (not above)
    return aligned, px - e


POS_LOOKBACK_M5 = 48                 # 48×5dk = son 4 saatlik dalga penceresi
POS_SELL_MIN = 0.40                  # SELL: dalganın üst %60'ı (kanıt aşağıda)
POS_BUY_MAX = 0.60                   # BUY : dalganın alt %60'ı


def entry_position(mt5_symbol: str, price: float | None = None
                   ) -> tuple[float | None, float, float]:
    """Fiyatın son 4 saatlik dalga içindeki KONUMU: 0.0=dip, 1.0=tepe.

    KANIT (2026-07-28, 175 canlı NDX VIXREG SELL + 50 USOIL, 1m sızıntısız
    konum ölçümü — giriş anı öncesi pencere, hindsight yok):
      NDX VIXREG SELL — dip bölge (0-0.33): n=88 WR %53.4  −3.738$
                        tepe bölge (0.66+): n=38 WR %65.8  +2.860$
        konum ≥0.40 kapısı: n=76 WR %67.1 → +6.487$ (filtresiz +500$)
      USOIL mom BUY   — konum ≤0.60 kapısı: n=16 WR %93.8 (filtresiz %80)
    Yani SELL'i dalganın DİBİNDEN açmak sistematik zarar; tepeden açmak kâr.
    Kullanıcı gözlemiyle birebir örtüşüyor (2026-07-27 ekran görüntüsü:
    27862'den — dibin dibinden — açılan SELL, 27958'de SL).

    Dönüş: (konum, dalga_dibi, dalga_tepesi). Veri yoksa (None, 0, 0) → fail-open.
    """
    bars = candles_tf(mt5_symbol, mt5.TIMEFRAME_M5, POS_LOOKBACK_M5)
    if not bars or len(bars) < 20:
        return None, 0.0, 0.0
    hi = max(float(b["high"]) for b in bars)
    lo = min(float(b["low"]) for b in bars)
    if hi <= lo:
        return None, lo, hi
    if price is None:
        tick = mt5.symbol_info_tick(mt5_symbol)
        if tick is None:
            return None, lo, hi
        price = (tick.bid + tick.ask) / 2.0
    return (float(price) - lo) / (hi - lo), lo, hi


def _position_gate_blocks(scope_key: str, mt5_symbol: str, direction: str,
                          flag: str = "POSITION_GATE_ENABLED") -> bool:
    """True → giriş bloklanmalı: SELL dalganın dibinde / BUY tepesinde.

    'Kırılım teyidi olmadan dipten satma' kuralının ölçülebilir hali. Fiyat
    kapının yanlış tarafındaysa bot BEKLER — dalga tepeye döndüğünde sinyal
    hâlâ geçerliyse oradan girer (kovalama yok, sadece konum disiplini)."""
    if not getattr(config, flag, True):
        return False
    pos, lo, hi = entry_position(mt5_symbol)
    if pos is None:
        return False                                   # veri yok → fail-open
    sell_min = float(getattr(config, "POS_SELL_MIN", POS_SELL_MIN))
    buy_max = float(getattr(config, "POS_BUY_MAX", POS_BUY_MAX))
    bad = (direction == "SELL" and pos < sell_min) or \
          (direction == "BUY" and pos > buy_max)
    if not bad:
        return False
    nerede = "DİBİNDE" if direction == "SELL" else "TEPESİNDE"
    log.info("%s — KONUM KAPISI: fiyat 4s dalganın %s (konum %.2f, dalga "
             "%.1f–%.1f) → %s açılmadı; dalga dönünce yeniden bakılacak "
             "(kanıt: dipten SELL WR %%53 −3.7k$ / tepeden %%66 +2.9k$)",
             scope_key, nerede, pos, lo, hi, direction)
    tick = mt5.symbol_info_tick(mt5_symbol)
    if tick:
        log_gate_skip(scope_key, mt5_symbol, scope_key.split(":")[0], direction,
                      tick.ask if direction == "BUY" else tick.bid,
                      "position_gate",
                      extra={"pos": round(pos, 3), "wave_lo": round(lo, 2),
                             "wave_hi": round(hi, 2)})
    return True


def check_shadow_scopes() -> None:
    """KANIT BİRİKTİRME: canlıya alınmamış scope'ları değerlendirir, kapıdan
    geçen sinyalleri KAYDEDER ama İŞLEM AÇMAZ.

    Neden (2026-07-28): timelapse deneyi XAUUSD'yi trend+konum kapılarıyla en
    kârlı sembol gösterdi (B varyantı: BUY +55.3R/6-9 hafta, SELL +103.7R/8-9;
    spread 0.30'da bile +44/+51R; ~11 işlem/gün). AMA XAU 2026-06'da canlıda
    para kaybettiği için icra dışı bırakılmıştı ve hafızadaki iki bağımsız
    araştırma "XAU intraday edge yok / dar stop öldürür" diyor. Simülasyon ile
    canlı geçmiş ÇELİŞİYOR → simülasyonun modellemediği bir şey var (icra,
    slippage, seans). Bu yüzden XAU canlıya AÇILMIYOR; kapıdan geçen sinyaller
    gölgede kaydedilip 2 hafta sonra gerçek fiyatla karşılaştırılacak
    (research/gate_audit.py --reason shadow_signal).
    """
    scopes = getattr(config, "SHADOW_SCOPES", {"XAUUSD:BUY": {}, "XAUUSD:SELL": {}})
    for scope_key in scopes:
        try:
            forexsai_sym, direction = scope_key.split(":")[:2]
            mt5_symbol = resolve_symbol(forexsai_sym)
            if not mt5_symbol:
                continue
            models = getattr(config, "SHADOW_SCOPE_MODELS", ["pulse1", "pulse2", "pulse3"])
            voters = [m for m in models
                      if signal_direction(m, fetch_pulse(m, forexsai_sym))[0] == direction]
            if not voters:
                continue
            log.info("[GÖLGE] %s — %d oy geldi, kapılar değerlendiriliyor",
                     scope_key, len(voters))
            aligned, _ = trend_alignment(mt5_symbol, direction)
            if not aligned:
                continue
            pos, lo, hi = entry_position(mt5_symbol)
            if pos is not None:
                if (direction == "SELL" and pos < float(getattr(config, "POS_SELL_MIN", 0.40))) \
                   or (direction == "BUY" and pos > float(getattr(config, "POS_BUY_MAX", 0.60))):
                    continue
            tick = mt5.symbol_info_tick(mt5_symbol)
            if tick is None:
                continue
            px = tick.ask if direction == "BUY" else tick.bid
            log.info("[GÖLGE] %s — kapıları geçti (konum %.2f, oy %s) → KAYDEDİLDİ, "
                     "işlem AÇILMADI", scope_key, pos if pos is not None else -1,
                     ",".join(voters))
            log_gate_skip(scope_key, mt5_symbol, forexsai_sym, direction, px,
                          "shadow_signal",
                          extra={"pos": round(pos, 3) if pos is not None else None,
                                 "voters": voters})
        except Exception as exc:                 # gölge asla canlıyı etkilemez
            # WARNING (debug değil): 2026-07-28'de gölge hiç tetiklenmedi ve
            # sebebi debug seviyesinde yutulduğu için görünmedi. Sessiz
            # başarısızlık, kanıt biriktirmeyi durdurur.
            log.warning("gölge scope hata %s: %s", scope_key, exc)


def backend_veto_advice(scope_key: str, forexsai_sym: str, mt5_symbol: str,
                        direction: str, voters: list[str],
                        block_flag: str) -> bool:
    """Backend Precision Veto DANIŞMASI — VIXREG/CHREV için (2026-07-28).

    NEDEN: Bu iki scope `fetch_bot_trade_signal` çağırmıyordu, yani Precision
    Veto'nun likidite/MTF/wick/macro-bias katmanları ve Stage-4 meta modeli
    bu girişlerde HİÇ çalışmıyordu. Yalnız ROBUST_SCOPES backend'e soruyordu.

    NEDEN GEOMETRİ ALINMIYOR: backend'in entry_optimizer'ı SL/TP'yi kendi
    hesabıyla döndürür; VIXREG'in +2.071$/30g performansı ise ARAŞTIRILMIŞ
    80/110 geometrisiyle ölçüldü. Geometriyi değiştirmek o kanıtı geçersiz
    kılar (ayrıca 2026-07-24'te bayat backend planı RR 0.07'lik emir açtırdı).
    Bu yüzden buradan YALNIZ "aç/açma" bilgisi alınır; tp/sl/lot'a dokunulmaz.

    NEDEN VARSAYILAN GÖLGE: Precision Veto'nun bu scope'lardaki etkisi HİÇ
    ölçülmedi. Gölgede kararı loglar (gate_skipped.jsonl → gate_audit.py),
    2 hafta sonra "veto etseydi ne olurdu" veriyle görülür; ancak o zaman
    <block_flag>=1 ile gerçek blok açılır.

    True → giriş bloklanmalı (yalnız block_flag açıksa). Fail-open.
    """
    if not getattr(config, "BACKEND_ADVICE_ENABLED", True):
        return False
    try:
        bs = fetch_bot_trade_signal(forexsai_sym, direction,
                                    confidence=70.0 + len(voters) * 5,
                                    model_type=",".join(voters) or "vixreg")
    except Exception as exc:
        log.debug("%s — backend danışması hata (fail-open): %s", scope_key, exc)
        return False
    if bs is None or bs.get("should_trade"):
        return False
    reason = bs.get("veto_reason") or "?"
    blocking = bool(getattr(config, block_flag, False))     # default GÖLGE
    log.info("%s — BACKEND VETO%s: %s", scope_key,
             "" if blocking else " (GÖLGE — engellemedi)", reason)
    tick = mt5.symbol_info_tick(mt5_symbol)
    if tick:
        log_gate_skip(scope_key, mt5_symbol, forexsai_sym, direction,
                      tick.ask if direction == "BUY" else tick.bid,
                      "backend_veto" if blocking else "backend_veto_shadow",
                      extra={"veto_reason": reason,
                             "zone_pos": (bs.get("notes") or {}).get("zone_position")})
    return blocking


# ─── Zaman-kalitesi (TQ) kapısı — 2026-08-01 gün/saat denetimi ───────────────
# Kanıt (385 gerçek işlem, broker→UTC −3s düzeltmeli):
#   * Cuma bot-geneli: WR %46 / −3.933$ (diğer günler %57-60) → Cuma yalnız
#     "çok emin" girişler (momentum: +1 fazla oy; vixreg: ≥TQ_COOL_MIN_VOTERS oy;
#     chrev: açılmaz).
#   * VIXREG 15-17 UTC: %44 / −5.483$ (12-14 %67 +4.095$, 18-20 %75 +2.594$)
#     → çukurda vixreg yalnız çok-emin; 18-20 penceresi AKTİF kalır.
#   * CHREV 15-17 UTC: %38 / −1.820$ → çukurda chrev açılmaz.
#   * Momentum'a SAAT freni YOK: 15-17 momentum'un EN İYİ dilimi (%62 +1.330$)
#     — yalnız Cuma kuralı uygulanır.
# Hepsi config ile kapatılır: TQ_ENABLED=False → katman tamamen devre dışı.

def _tq_cool(family: str) -> tuple[bool, str]:
    """(çukurda_mı, sebep). family: 'momentum' | 'vixreg' | 'chrev'. Fail-open."""
    if not getattr(config, "TQ_ENABLED", True):
        return False, ""
    try:
        now = datetime.now(timezone.utc)
        if now.isoweekday() == 5 and getattr(config, "TQ_FRIDAY_COOL", True):
            return True, "Cuma (bot 385 işlem: WR %46 / −3.9k$)"
        cool_hours = set(getattr(config, "TQ_COOL_HOURS_UTC", (15, 16, 17)))
        cool_fams = set(getattr(config, "TQ_COOL_FAMILIES", ("vixreg", "chrev")))
        if now.hour in cool_hours and family in cool_fams:
            return True, f"{now.hour:02d} UTC çukuru ({family})"
    except Exception:
        return False, ""
    return False, ""


def _tq_decider_approval(forexsai_sym: str, direction: str) -> tuple[bool, str]:
    """ÇUKUR penceresinde Claude Decider onayı köprüsü (2026-08-01).

    Aynı kutudaki decider'ın journal'ında (claude_decider/memory/journal.jsonl)
    bu sembol için EN TAZE karar ≤TQ_DECIDER_FRESH_MIN dk önce, action=OPEN,
    aynı yönde ve size_factor ≥ TQ_DECIDER_MIN_SIZE ise → "çok emin" sayılır,
    çukur kuralı aşılır. Kanıt: botun çukurlarında decider NEGATİF DEĞİL —
    Cuma tüm semboller WR %57-67 (bot %46/−3.9k$), 15-17 UTC NDX %65 (n=31),
    DAX %62 (n=13); decider genel %60.7 (n=845).
    Fail-closed: journal yok/okunamaz/bayat → onay YOK (çukur kuralı uygulanır).
    """
    if not getattr(config, "TQ_DECIDER_APPROVAL", True):
        return False, ""
    try:
        from pathlib import Path
        jp = (Path(__file__).resolve().parent.parent
              / "claude_decider" / "memory" / "journal.jsonl")
        if not jp.exists():
            return False, ""
        with open(jp, "rb") as f:                    # dev dosya: yalnız kuyruk
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 262144))
            tail = f.read().decode("utf-8", "ignore")
        fresh_min = float(getattr(config, "TQ_DECIDER_FRESH_MIN", 45))
        min_size = float(getattr(config, "TQ_DECIDER_MIN_SIZE", 0.3))
        now = datetime.now(timezone.utc)
        for line in reversed(tail.splitlines()):
            try:
                r = json.loads(line)
            except Exception:
                continue                              # kuyruğun kırpık ilk satırı vb.
            if r.get("symbol") != forexsai_sym:
                continue
            # Bu sembolün EN TAZE kararı — ne derse o geçerli, gerisine bakılmaz.
            ts = datetime.fromisoformat(str(r.get("ts")))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age_min = (now - ts).total_seconds() / 60
            d = r.get("decision") or {}
            if (age_min <= fresh_min
                    and str(d.get("action", "")).upper() == "OPEN"
                    and d.get("direction") == direction
                    and float(d.get("size_factor") or 0) >= min_size):
                return True, (f"decider onayı: {age_min:.0f}dk önce OPEN "
                              f"{direction} size={d.get('size_factor')}")
            return False, ""
    except Exception as exc:
        log.debug("tq decider onay okunamadı (fail-closed): %s", exc)
    return False, ""


def _trend_gate_blocks(scope_key: str, mt5_symbol: str, direction: str,
                       flag: str = "TREND_GATE_ENABLED") -> bool:
    """True → giriş bloklanmalı. Log + config bayrağı ile kapatılabilir."""
    if not getattr(config, flag, True):
        return False
    aligned, dist = trend_alignment(mt5_symbol, direction)
    if aligned:
        return False
    log.info("%s — TREND KAPISI: fiyat 1h EMA50'nin ters tarafında "
             "(mesafe %.2f) → karşı-trend %s açılmadı (30g kanıt: WR %%43 / −13k$)",
             scope_key, dist if dist is not None else 0.0, direction)
    tick = mt5.symbol_info_tick(mt5_symbol)
    if tick:
        fxs = scope_key.split(":")[0]
        log_gate_skip(scope_key, mt5_symbol, fxs, direction,
                      tick.ask if direction == "BUY" else tick.bid,
                      "trend_gate", extra={"ema50_dist": round(dist, 3) if dist else None})
    return True


def _market_open(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters, bot_signal):
    """Eski market girişi (momentum-continuation)."""
    if bot_signal:
        open_trade_v2(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters, bot_signal)
    else:
        open_trade(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters)


def _route_open(scope_key: str, forexsai_sym: str, mt5_symbol: str,
                direction: str, cfg: dict, voters: list[str],
                bot_signal: dict | None) -> None:
    """HİBRİT giriş kararı:
      - USE_SR_ENTRY kapalı            → eski market girişi.
      - AŞIRI momentum (M15 stretch>eşik, seansa ölçekli) → market continuation.
      - Aksi (normal momentum)         → S/R pullback (pending limit).
    """
    _ENTRY_CTX.clear()                                       # parmak izi bağlamı (taze)

    if not config.USE_SR_ENTRY:
        _market_open(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters, bot_signal)
        return

    candles = candles_1m(mt5_symbol, config.ZONE_LOOKBACK)   # S/R için (bir kez)

    if config.HYBRID_ENTRY:
        m15 = candles_tf(mt5_symbol, mt5.TIMEFRAME_M15, config.MOMENTUM_MTF_BARS)
        mom = momentum_stretch(m15, direction) if m15 else 0.0
        factor, sess = _session_factor(forexsai_sym)
        thr = config.MOMENTUM_EXCESS_ATR * factor
        _ENTRY_CTX.update({"mom": round(mom, 2), "thr": round(thr, 2), "session": sess})
        if mom > thr:
            log.info("%s — AŞIRI momentum (M15 stretch=%.2f > eşik=%.2f, seans=%s) "
                     "→ MARKET continuation", scope_key, mom, thr, sess)
            _market_open(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters, bot_signal)
            return
        log.info("%s — normal momentum (M15 stretch=%.2f ≤ eşik=%.2f, seans=%s) "
                 "→ S/R pullback", scope_key, mom, thr, sess)

    open_trade_sr(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters,
                  bot_signal, candles=candles)


# ─── Ana döngü ───────────────────────────────────────────────────────────────

def check_scope(scope_key: str, cfg: dict) -> None:
    forexsai_sym, direction = scope_key.split(":")
    if (forexsai_sym, direction) in getattr(config, "BLOCKED_SYMBOL_DIRECTIONS", set()):
        return                                          # kalıcı yasak (ör. XAUUSD SELL)
    mt5_symbol = resolve_symbol(forexsai_sym)
    if not mt5_symbol:
        return

    held = open_count(mt5_symbol, direction)
    pend = pending_count(mt5_symbol, direction) if config.USE_SR_ENTRY else 0
    if held + pend >= config.MAX_OPEN_PER_SCOPE:
        log.info("%s — zaten açık pozisyon/bekleyen emir var (%d+%d), atlanıyor",
                 scope_key, held, pend)
        return

    voters = []
    for model in cfg["models"]:
        payload = fetch_pulse(model, forexsai_sym)
        d, stype = signal_direction(model, payload)
        if d == direction:
            if config.ONLY_CONFIRM_SIGNALS and stype != "CONFIRM":
                log.info("  %s %s = %s ama SCOUT (CONFIRM bekleniyor) — sayılmadı",
                         model, forexsai_sym, d)
                continue
            voters.append(model)

    if len(voters) < config.MIN_MODEL_VOTES:
        log.info("%s — yeterli sinyal yok (%d/%d)",
                 scope_key, len(voters), config.MIN_MODEL_VOTES)
        return

    # ── TQ kapısı: çukur pencerede (momentum için yalnız Cuma) çıta yükselir —
    #    normal oy eşiğinin ÜSTÜNE TQ_FRIDAY_EXTRA_VOTES kadar ek oy istenir.
    _cool, _why = _tq_cool("momentum")
    if _cool:
        _need = config.MIN_MODEL_VOTES + int(getattr(config, "TQ_FRIDAY_EXTRA_VOTES", 1))
        if len(voters) < _need:
            _ok, _dnote = _tq_decider_approval(forexsai_sym, direction)
            if _ok:
                log.info("%s — TQ ÇUKUR (%s): oy %d/%d ama %s → çok-emin sayıldı, devam",
                         scope_key, _why, len(voters), _need, _dnote)
            else:
                log.info("%s — TQ ÇUKUR (%s): %d oy var, çok-emin eşiği %d ve "
                         "decider onayı yok → açılmadı",
                         scope_key, _why, len(voters), _need)
                _log_trade("TQ_COOL", scope_key, mt5_symbol, direction, 0, 0, 0,
                           voters, _why)
                return
        else:
            log.info("%s — TQ ÇUKUR (%s) ama %d oy ≥ %d (çok-emin) → devam",
                     scope_key, _why, len(voters), _need)

    # ── Trend hizası kapısı (2026-07-24 kanıtı; momentum-continuation'ın
    #    tanımı gereği) — backend çağrısından ÖNCE, boş token harcamasın.
    if _trend_gate_blocks(scope_key, mt5_symbol, direction):
        _log_trade("TREND_GATE", scope_key, mt5_symbol, direction, 0, 0, 0,
                   voters, "karsi-trend (1h EMA50)")
        return
    # ── Konum kapısı (2026-07-28 kanıtı): SELL dalganın dibinden, BUY
    #    tepesinden açılmaz — kırılım/teyit gelmeden ters uçtan girme.
    if _position_gate_blocks(scope_key, mt5_symbol, direction):
        _log_trade("POSITION_GATE", scope_key, mt5_symbol, direction, 0, 0, 0,
                   voters, "dalga ters ucu")
        return

    # ── Backend'den birleşik trade plan al ───────────────────────────────
    bot_signal = fetch_bot_trade_signal(
        forexsai_sym, direction,
        confidence=70.0 + len(voters) * 5,
        model_type=",".join(voters))

    if bot_signal is None:
        # OOS-doğrulanmış momentum filtresi olan scope'lar backend'siz açılamaz:
        # filtre göstergeleri yalnızca backend'de hesaplanıyor; doğrulanmamış
        # girişte bu scope'lar ≈breakeven/−EV. Backend gelene kadar ATLA.
        if scope_key in config.MOMENTUM_FILTERED_SCOPES:
            log.warning("%s — backend yok; momentum-filtreli scope, "
                        "doğrulanamadığı için ATLANDI", scope_key)
            _log_trade("SKIP_NO_BACKEND", scope_key, mt5_symbol, direction,
                       0, 0, 0, voters, "momentum filtre dogrulanamadi")
            return
        log.warning("%s — backend yok, fallback giriş", scope_key)
        _route_open(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters, None)
        return

    if not bot_signal.get("should_trade"):
        log.info("%s — backend BLOKLADI: %s",
                 scope_key, bot_signal.get("veto_reason"))
        _log_trade("VETO", scope_key, mt5_symbol, direction, 0, 0, 0, voters,
                   f"reason={bot_signal.get('veto_reason')}")
        return

    log.info("%s — %d voter + backend OK (action=%s prio=%s lot×%.2f)",
             scope_key, len(voters), bot_signal.get("action"),
             bot_signal.get("priority_score"),
             bot_signal.get("effective_lot_multiplier", 1.0))
    _route_open(scope_key, forexsai_sym, mt5_symbol, direction, cfg, voters, bot_signal)


_CR_TF = {"5m": "TIMEFRAME_M5", "15m": "TIMEFRAME_M15",
          "30m": "TIMEFRAME_M30", "1h": "TIMEFRAME_H1"}


_chrev_tracked: dict[int, tuple[str, str]] = {}       # ticket → (sym, yön)
_chrev_last_loss: dict[tuple[str, str], float] = {}   # (sym, yön) → duvar-saati ts
CHREV_LOSS_COOLDOWN_SEC = 3600


def _chrev_update_cooldown(mt5_symbol: str, forexsai_sym: str) -> None:
    """CHREV pozisyonlarını izle; ZARARLA kapananı yakala → cooldown başlat.

    2026-07-23 kanaması: GER40 CHREV BUY güçlü düşüş gününde SL yedi ve
    0-1 dk içinde yeniden girdi (15:33 SL → 15:33 re-BUY → 16:05 SL →
    16:06 re-BUY), gün sonu 1W/3L −1657$. Mean-rev z'si trendde ekstrem
    kalmaya devam ediyor → SL sonrası 60dk bekleme döngüyü kırar.
    history_deals_get(position=) broker saat-dilimi penceresi istemez."""
    magic = config.CHANNEL_REVERSION_MAGIC
    try:
        live = {p.ticket: p for p in (mt5.positions_get(symbol=mt5_symbol) or [])
                if p.magic == magic}
        for t, p in live.items():
            d = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
            _chrev_tracked[t] = (forexsai_sym, d)
        gone = [t for t, (s, _d) in list(_chrev_tracked.items())
                if s == forexsai_sym and t not in live]
        for t in gone:
            s, d = _chrev_tracked.pop(t)
            deals = mt5.history_deals_get(position=t) or []
            pnl = sum(x.profit for x in deals if x.entry == mt5.DEAL_ENTRY_OUT)
            if pnl < 0:
                _chrev_last_loss[(s, d)] = time.time()
                log.info("%s:%s:CHREV — zararla kapandı (%.2f) → %ddk cooldown",
                         s, d, pnl, CHREV_LOSS_COOLDOWN_SEC // 60)
    except Exception as exc:                            # fail-open
        log.debug("chrev cooldown izleme hata: %s", exc)


def check_channel_reversion(forexsai_sym: str, cfg: dict) -> None:
    """MEAN-REVERSION scope (momentum'dan AYRI): pulse3 sinyali + fiyat 30m linreg
    trend-çizgisinden ≥2.5σ ötede (kanal-rejection) → market giriş, sabit tp/sl.
    Araştırma: WR %44 → %82-88 OOS. Yalnız doğrulanmış sembol+yönlerde (config)."""
    mt5_symbol = resolve_symbol(forexsai_sym)
    if not mt5_symbol:
        return
    _chrev_update_cooldown(mt5_symbol, forexsai_sym)
    model = config.CHANNEL_REVERSION_MODEL
    payload = fetch_pulse(model, forexsai_sym)
    direction, stype = signal_direction(model, payload)
    if direction not in cfg["dirs"]:
        return
    if (forexsai_sym, direction) in getattr(config, "BLOCKED_SYMBOL_DIRECTIONS", set()):
        return                                          # kalıcı yasak (ör. XAUUSD SELL)
    if config.ONLY_CONFIRM_SIGNALS and stype != "CONFIRM":
        return
    cr_magic = config.CHANNEL_REVERSION_MAGIC                    # AYRI magic → momentum'u bloklamaz
    if open_count(mt5_symbol, direction, cr_magic) + pending_count(mt5_symbol, direction, cr_magic) >= config.MAX_OPEN_PER_SCOPE:
        return
    last_loss = _chrev_last_loss.get((forexsai_sym, direction))
    if last_loss and time.time() - last_loss < CHREV_LOSS_COOLDOWN_SEC:
        left = int((CHREV_LOSS_COOLDOWN_SEC - (time.time() - last_loss)) // 60)
        log.info("%s:%s:CHREV — SL sonrası cooldown (%ddk kaldı) → açılmadı",
                 forexsai_sym, direction, left)
        return
    tf_const = getattr(mt5, _CR_TF.get(config.CHANNEL_REVERSION_MT5_TF, "TIMEFRAME_M30"))
    bars = candles_tf(mt5_symbol, tf_const, 60)
    if not bars or len(bars) < 55:
        return
    ok, source, z = is_mean_reversion(bars, direction)     # kanal z≥2.0 VEYA vwap z≥1.5
    scope_key = f"{forexsai_sym}:{direction}:CHREV"
    if not ok:
        log.info("%s — mean-reversion YOK (z=%.2f) → açılmadı", scope_key, z)
        return
    # ── ADX rejim kapısı (2026-08-05 GDAXI olayı): mean-reversion 'range'
    #    varsayar; ADX yüksekken (trend rejimi) z-ekstremi gürültü değil,
    #    kırılımın kendisi olabilir. Kanal eğimi (aşağıdaki 'gated' kontrolü)
    #    25 saatlik pencerede yavaş tepki verir — ADX aynı barda tepki verir.
    if getattr(config, "CHREV_ADX_GATE_ENABLED", True):
        adx = adx_from_bars(bars)
        adx_max = float(getattr(config, "CHREV_ADX_MAX", 25.0))
        if adx is not None and adx >= adx_max:
            log.info("%s — ADX KAPISI: ADX(30m)=%.1f ≥ %.1f (trend rejimi, "
                     "mean-reversion güvenilmez, z=%.2f) → %s",
                     scope_key, adx, adx_max, z,
                     "açılmadı" if getattr(config, "CHREV_ADX_GATE_BLOCK", True) else "GÖLGE, devam")
            if getattr(config, "CHREV_ADX_GATE_BLOCK", True):
                tick = mt5.symbol_info_tick(mt5_symbol)
                if tick:
                    log_gate_skip(scope_key, mt5_symbol, forexsai_sym, direction,
                                  tick.ask if direction == "BUY" else tick.bid,
                                  "chrev_adx_gate", extra={"adx": round(adx, 1), "z": round(z, 2)})
                return
    # ── TQ kapısı: CHREV çukur pencerede (15-17 UTC %38 −1.820$) ve Cuma
    #    yalnız Claude Decider onayıyla açılır — tek-model scope'ta başka
    #    "çok emin" ölçütü yok; decider'ın 5m mean-rev kanıt kapısı aynı
    #    kurulumun daha sıkı hali (çukurlarda decider %57-67).
    _cool, _why = _tq_cool("chrev")
    if _cool:
        _ok, _dnote = _tq_decider_approval(forexsai_sym, direction)
        if _ok:
            log.info("%s — TQ ÇUKUR (%s) ama %s → devam", scope_key, _why, _dnote)
        else:
            log.info("%s — TQ ÇUKUR (%s), decider onayı yok → CHREV açılmadı",
                     scope_key, _why)
            tick = mt5.symbol_info_tick(mt5_symbol)
            if tick:
                log_gate_skip(scope_key, mt5_symbol, forexsai_sym, direction,
                              tick.ask if direction == "BUY" else tick.bid,
                              "tq_cool", extra={"why": _why, "z": round(z, 2)})
            return
    # ── Kanıt kapısı (2026-07-23, research/next_candidates 30g z-taraması) ──
    # GDAXI BUY: düşen kanalda WR %28.6 / vwap-kaynak WR %25 → yalnız
    #   kanal-kaynak + lehte eğim geçer (WR %73.7, be %64 üstü).
    # NDX SELL: aynı kapıyla %68.8 (be %57.9) → kapılı devam.
    # NDX BUY: WR %40 (be %57.9), kapı da kurtarmıyor (%31.8) → KAPALI.
    # USOIL SELL: WR %40.6 (be %58.9), kapı yetersiz (%50) → KAPALI.
    # 2026-07-24 ek kanıt: GDAXI SELL dün tabloda EKSİKTİ (varsayılan "open"
    # kaldı) ve 07-24'te 2 SL yedi (−1.350$). Taraması: 30g WR %73.1 (+3.7R),
    # kapılı %83.3 → "gated". 30g canlı chrev toplamı −4.985$ olduğu için
    # tüm kollar artık ya kapılı ya kapalı.
    mode = {**{("GDAXI.INDX", "BUY"): "gated", ("GDAXI.INDX", "SELL"): "gated",
               ("NDX.INDX", "SELL"): "gated",
               ("NDX.INDX", "BUY"): "off", ("USOIL.FOREX", "SELL"): "off"},
            **getattr(config, "CHREV_MODE_OVERRIDE", {})
            }.get((forexsai_sym, direction), "open")
    if mode == "off":
        log.info("%s — kanıt denetimi KAPALI dedi (30g WR başabaş altı) → açılmadı",
                 scope_key)
        return
    if mode == "gated":
        from channel_filter import channel_slope_atr
        slope = channel_slope_atr(bars)
        sign = 1 if direction == "BUY" else -1
        slope_ok = slope is not None and sign * slope >= 0
        if source != "channel" or not slope_ok:
            log.info("%s — rejim kapısı: kaynak=%s eğim=%s → açılmadı "
                     "(kanal-kaynak + lehte eğim şart)", scope_key, source,
                     f"{slope:.3f}" if slope is not None else "?")
            return
    # Backend danışması (CHREV de backend'e hiç sormuyordu) — GÖLGE varsayılan.
    # NOT: CHREV mean-reversion olduğu için konum kapısı UYGULANMAZ — bu scope
    # zaten tanımı gereği dipten alır / tepeden satar (kanal ekstremi).
    if backend_veto_advice(scope_key, forexsai_sym, mt5_symbol, direction,
                           [model], "CHREV_BACKEND_VETO"):
        return
    log.info("%s — MEAN-REVERSION [%s] z=%.2f ✓ → market giriş", scope_key, source, z)
    open_trade(scope_key, forexsai_sym, mt5_symbol, direction, cfg, [model], magic=cr_magic)


_vix_cache = {"t": 0.0, "v": None}


def get_vix() -> float | None:
    """Canlı VIX (backend /api/macro-gauges, günlük). 10dk cache."""
    now = time.time()
    if _vix_cache["v"] is not None and now - _vix_cache["t"] < config.VIX_CACHE_SEC:
        return _vix_cache["v"]
    try:
        r = requests.get(config.FOREXSAI_API.rstrip("/") + "/api/macro-gauges", timeout=15)
        if r.status_code == 200:
            for g in r.json().get("gauges", []):
                if g.get("key") == "vix" and g.get("value") is not None:
                    _vix_cache["t"] = now; _vix_cache["v"] = float(g["value"])
                    return _vix_cache["v"]
    except Exception as e:
        log.warning("VIX alınamadı: %s", e)
    return _vix_cache["v"]



# ─── DAYCOMBO: gün-yönü (gece pozitif) + 15m trend + yeşil 5m mum (2026-07-28) ───
# Kanıt: research/ndx_buy_lab/daygate_combo.py — 160 kombodan üç kronolojik
# dilimde de pozitif kalan TEK kombo. n=165 / 57 gün, WR %63.0 (çıta %58.6),
# EV +0.077R; düşen test döneminde bile +0.060R. Geometri sabit 80/110 —
# trade_manager _RULES bu magic'i İÇERMEZ → BE/trail dokunmaz (ölçüm sabit
# TP/SL ile yapıldı, öyle kalmalı).
# Kural: (1) gün 00:00→13:25 UTC getirisi > 0  (2) son KAPALI 15m: kapanış
# EMA20 üstünde VE EMA20 3-bar eğimi yukarı  (3) son KAPALI 5m: yeşil ve
# gövde/aralık > 0.5  (4) pencere 14:00–19:30 UTC  → sonraki mumda market BUY.
# ⚠️ MT5 bar saatleri BROKER saatindedir (research/ndx_buy_lab RAPOR §1) —
# UTC pencereler ölçülen offset ile çevrilir.
DAYCOMBO_MAGIC = config.MAGIC_NUMBER + 4
_daycombo_state = {"offset": None, "offset_t": 0.0, "last_bar": None}


def _daycombo_offset(mt5_symbol: str) -> int:
    """Broker sunucu saati − gerçek UTC (saniye; 15dk'ya yuvarlı, 1s cache)."""
    now = time.time()
    st = _daycombo_state
    if st["offset"] is not None and now - st["offset_t"] < 3600:
        return st["offset"]
    off = 0
    try:
        tick = mt5.symbol_info_tick(mt5_symbol)
        if tick and tick.time:
            off = int(round((tick.time - now) / 900.0) * 900)
    except Exception:
        pass
    st["offset"], st["offset_t"] = off, now
    return off


def check_daycombo() -> None:
    if not getattr(config, "DAYCOMBO_ENABLED", True):
        return
    forexsai_sym = "NDX.INDX"
    mt5_symbol = resolve_symbol(forexsai_sym)
    if not mt5_symbol:
        return
    scope_key = f"{forexsai_sym}:BUY:DAYCOMBO"
    if open_count(mt5_symbol, "BUY", DAYCOMBO_MAGIC) >= 1:
        return
    off = _daycombo_offset(mt5_symbol)
    now_utc = datetime.now(timezone.utc)
    hm = now_utc.hour * 60 + now_utc.minute
    if not (14 * 60 <= hm <= 19 * 60 + 30):          # giriş penceresi (UTC)
        return

    # ── son KAPALI 5m bar (pozisyon 1 = oluşan barı atla) ──
    r5 = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M5, 1, 300)
    if r5 is None or len(r5) < 60:
        return
    last5 = r5[-1]
    bar_utc = int(last5["time"]) - off
    if _daycombo_state["last_bar"] == bar_utc:
        return                                        # bu 5m bar zaten işlendi
    if time.time() - bar_utc > 360:
        return                                        # bayat bar (>6dk) — atla
    _daycombo_state["last_bar"] = bar_utc

    # (3) gövdeli yeşil 5m mum
    o5, h5, l5, c5 = (float(last5[k]) for k in ("open", "high", "low", "close"))
    rng = h5 - l5
    if not (c5 > o5 and rng > 0 and (c5 - o5) / rng > 0.5):
        return

    # (1) gece pozitif: bugünün 00:00 UTC açılışı → 13:25 UTC fiyatı
    day_utc = datetime.fromtimestamp(bar_utc, tz=timezone.utc).date()
    gece_acilis = premkt = None
    for r in r5:
        t_utc = datetime.fromtimestamp(int(r["time"]) - off, tz=timezone.utc)
        if t_utc.date() != day_utc:
            continue
        if gece_acilis is None:
            if t_utc.hour == 0 and t_utc.minute < 10:
                gece_acilis = float(r["open"])
            else:
                break                                 # günün başı pencerede yok
        if t_utc.hour * 60 + t_utc.minute <= 13 * 60 + 20:
            premkt = float(r["close"])
    if gece_acilis is None or premkt is None or premkt <= gece_acilis:
        return

    # (2) 15m trend: kapanış > EMA20 ve EMA20 3-bar eğimi yukarı
    r15 = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M15, 1, 80)
    if r15 is None or len(r15) < 30:
        return
    closes = [float(x["close"]) for x in r15]
    ema, k = closes[0], 2.0 / 21.0
    hist = []
    for cx in closes:
        ema = cx * k + ema * (1 - k)
        hist.append(ema)
    if not (closes[-1] > hist[-1] and hist[-1] > hist[-4]):
        return

    log.info("%s — gece +%.2f%% & 15m trend↑ & gövdeli yeşil 5m → market BUY",
             scope_key, (premkt / gece_acilis - 1) * 100)
    cfg = {"tp": float(getattr(config, "DAYCOMBO_TP", 80.0)),
           "sl": float(getattr(config, "DAYCOMBO_SL", 110.0)), "is_pct": False}
    open_trade(scope_key, forexsai_sym, mt5_symbol, "BUY", cfg,
               ["daycombo"], magic=DAYCOMBO_MAGIC)


# ── USOIL BREAKOUT-DEVAM scope (2026-08-06 arastirmasi, AYRI magic+5) ────────
# Kanit: 150 gun / 29.415 adet 5m bar, 1260 Donchian-kanal kirilim olayi,
# kronolojik train(%70)/test(%30) + placebo. Donchian N (48-288 bar) ve
# tek/coklu-bar teyidi denendi — N ve teyit sayisindan BAGIMSIZ olarak BUY
# devam orani ~%58-60 OOS'ta sabit kaldi (N=48 confirm=1: train %60.0/test
# %58.8). Tek/coklu-esik gosterge filtreleri (ADX/DI/RSI/MACD/vol/ATR/range,
# hem tek-tek hem LightGBM ile) placebo'yu gecse bile OOS'ta iyilesme
# VERMEDI (bazan baseline'in altina dustu) — capraz-dogrulanmis DEGIL, koda
# ALINMADI. TEK saglam, OOS-kararli ayrim: 5m EMA200 trend hizasi.
#   BUY, fiyat EMA200 UZERINDEYKEN (trend-hizali): TEST %62.7 (n=185)
#   BUY, fiyat EMA200 ALTINDAYKEN (trend-tersi):   TEST %21.1 (n=19) — COKUYOR
# SELL yonunde HICBIR konfigurasyonda placebo'yu asan/OOS-kararli bir ayrim
# bulunamadi (en iyi TRAIN bulgu bile TEST'te dagildi) — SELL kapsam DISI.
# TP=SL=1.0xATR14(5m) (RR 1:1); %62.7 WR ile beklenti +0.25R/islem, n=185
# uzerinden test doneminde toplam +47R. Detay: macro_ndx_test/ (arastirma
# scriptleri panel repo'sunda, backend/research'e tasinmasi backlog'da).
_usoil_bo_state: dict = {"last_bar": None}


def check_usoil_breakout() -> None:
    if not getattr(config, "USOIL_BREAKOUT_ENABLED", True):
        return
    forexsai_sym = "USOIL.FOREX"
    mt5_symbol = resolve_symbol(forexsai_sym)
    if not mt5_symbol:
        return
    magic = int(getattr(config, "USOIL_BREAKOUT_MAGIC", config.MAGIC_NUMBER + 5))
    scope_key = f"{forexsai_sym}:BUY:BREAKOUT"
    if open_count(mt5_symbol, "BUY", magic) + pending_count(mt5_symbol, "BUY", magic) >= 1:
        return

    n_don = int(getattr(config, "USOIL_BREAKOUT_DONCHIAN_N", 48))
    n_ema = int(getattr(config, "USOIL_BREAKOUT_EMA_TREND", 200))
    need = max(n_don, n_ema) + 5
    rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M5, 1, need)  # pos=1: olusan barı atla
    if rates is None or len(rates) < need:
        return
    bar_time = int(rates[-1]["time"])
    if _usoil_bo_state["last_bar"] == bar_time:
        return                                            # bu 5m bar zaten islendi
    _usoil_bo_state["last_bar"] = bar_time

    closes = np.array([float(r["close"]) for r in rates])
    highs = np.array([float(r["high"]) for r in rates])

    # EMA200 (trend hizasi)
    k = 2.0 / (n_ema + 1)
    ema_t = closes[0]
    for x in closes[1:]:
        ema_t = x * k + ema_t * (1 - k)

    # Donchian: SON kapali bardan ONCEKI n_don barin en yuksegi (bakma-onyargisi yok)
    donch_high_now = highs[-1 - n_don:-1].max()
    donch_high_prev = highs[-2 - n_don:-2].max()

    fresh_break = closes[-1] > donch_high_now and closes[-2] <= donch_high_prev
    trend_aligned = closes[-1] > ema_t
    if not (fresh_break and trend_aligned):
        return

    atr = atr_5m(mt5_symbol)
    if not atr or atr <= 0:
        log.warning("%s — ATR alınamadı, atlandı", scope_key)
        return
    tp = round(float(getattr(config, "USOIL_BREAKOUT_TP_ATR", 1.0)) * atr, 5)
    sl = round(float(getattr(config, "USOIL_BREAKOUT_SL_ATR", 1.0)) * atr, 5)
    log.info("%s — Donchian(%d) kırılımı (seviye=%.3f) + EMA200 trend-hizalı "
             "(fiyat=%.3f > ema200=%.3f) → market BUY (TP/SL=%.3f/ATR×1.0)",
             scope_key, n_don, donch_high_now, closes[-1], ema_t, atr)
    cfg = {"tp": tp, "sl": sl, "is_pct": False}
    open_trade(scope_key, forexsai_sym, mt5_symbol, "BUY", cfg,
               ["breakout_donchian_ema200"], magic=magic)


def check_vix_regime() -> None:
    """VIX-rejim NDX yön scope'u: VIX<eşik→SELL favored, ≥eşik→BUY favored; model
    favored yönde sinyal verirse market giriş. Momentum/channel'dan AYRI magic."""
    forexsai_sym = config.VIX_REGIME_SYMBOL
    mt5_symbol = resolve_symbol(forexsai_sym)
    if not mt5_symbol:
        return
    vix = get_vix()
    if vix is None:
        log.warning("vix-regime — VIX yok, atlandı"); return
    favored = "BUY" if vix >= config.VIX_REGIME_THRESHOLD else "SELL"
    if (forexsai_sym, favored) in getattr(config, "BLOCKED_SYMBOL_DIRECTIONS", set()):
        return
    magic = config.VIX_REGIME_MAGIC
    if open_count(mt5_symbol, favored, magic) + pending_count(mt5_symbol, favored, magic) >= config.MAX_OPEN_PER_SCOPE:
        return
    voters = []
    for model in config.VIX_REGIME_MODELS:
        d, stype = signal_direction(model, fetch_pulse(model, forexsai_sym))
        if d == favored and (not config.ONLY_CONFIRM_SIGNALS or stype == "CONFIRM"):
            voters.append(model)
    scope_key = f"{forexsai_sym}:{favored}:VIXREG"
    # ── TQ kapısı: 15-17 UTC çukuru (−5.483$) + Cuma → yalnız çok-emin
    #    (≥TQ_COOL_MIN_VOTERS model oyu). 12-14 ve 18-20 pencereleri AKTİF.
    if voters:
        _cool, _why = _tq_cool("vixreg")
        _need = int(getattr(config, "TQ_COOL_MIN_VOTERS", 2))
        if _cool and len(voters) < _need:
            _ok, _dnote = _tq_decider_approval(forexsai_sym, favored)
            if _ok:
                log.info("%s — TQ ÇUKUR (%s): oy %d/%d ama %s → çok-emin sayıldı, devam",
                         scope_key, _why, len(voters), _need, _dnote)
            else:
                log.info("%s — TQ ÇUKUR (%s): %d oy < çok-emin eşiği %d ve "
                         "decider onayı yok → açılmadı",
                         scope_key, _why, len(voters), _need)
                tick = mt5.symbol_info_tick(mt5_symbol)
                if tick:
                    log_gate_skip(scope_key, mt5_symbol, forexsai_sym, favored,
                                  tick.ask if favored == "BUY" else tick.bid,
                                  "tq_cool", extra={"why": _why, "voters": voters})
                return
    # Trend hizası: vixreg'de de net ayrışıyor (NDX SELL trend n=123 %63
    # +5.5k$ / karşı n=51 %51 −3.5k$). Ayrı bayrak — VIXREG_TREND_GATE=0
    # ile kapatılabilir (VIX rejimi kendi başına yön kanıtı taşıyor).
    if voters and _trend_gate_blocks(scope_key, mt5_symbol, favored,
                                     flag="VIXREG_TREND_GATE"):
        return
    # Konum kapısı — VIXREG'in EN KRİTİK eksiğiydi: bu scope backend'e hiç
    # sormadığı için Precision Veto'nun discount_zone_sell koruması da
    # uygulanmıyordu ve SELL'ler dalganın dibinden açılıyordu (n=88, WR %53,
    # −3.738$). 2026-07-27 kullanıcı ekran görüntüsündeki SL tam bu vaka.
    if voters and _position_gate_blocks(scope_key, mt5_symbol, favored,
                                        flag="VIXREG_POSITION_GATE"):
        return
    # Backend Precision Veto danışması — geometri ALINMAZ, yalnız aç/açma.
    # Varsayılan GÖLGE: VIXREG_BACKEND_VETO=1 olana kadar sadece loglar.
    if voters and backend_veto_advice(scope_key, forexsai_sym, mt5_symbol,
                                      favored, voters, "VIXREG_BACKEND_VETO"):
        return
    if not voters:
        log.info("%s — VIX=%.1f favored=%s ama model sinyali yok → açılmadı",
                 scope_key, vix, favored)
        return
    log.info("%s — VIX=%.1f favored=%s, %d model onaylıyor → market giriş",
             scope_key, vix, favored, len(voters))
    # TP sabit (80p — araştırmada ATR'ye bağlamak ek fayda vermedi, aylık
    # dayanıklılığı düşürdü), SL uyarlamalı (2.0×ATR — 6/6 ay pozitif).
    cfg = {"tp": config.VIX_REGIME_TP,
           "sl": adaptive_sl(mt5_symbol, scope_key, float(config.VIX_REGIME_SL)),
           "is_pct": False}
    # SELL sabır kapısı (kanıt: Δ+39.3R — hızlı ölen SELL'ler ilk 10dk'da
    # kendini ele veriyor; research/trade_mgmt_ndx). BUY'a UYGULANMAZ.
    # SABIR KAPISI — 2026-07-28'de VARSAYILAN KAPATILDI.
    # Kanıt dengesi kapatma yönünde döndü:
    #   * timelapse OUT-of-sample (research/sim_bot): 3/3 SELL scope'ta ZARARLI
    #     (NDX trend+konum +10.27R → sabırla +5.18R; GDAXI +4.32→+0.63)
    #   * haftalık dilim testi: en iyi varyant B = trend+konum, SABIRSIZ
    #   * canlı 2026-07-27: 8 kuyruktan geçen tek işlem SL
    # Karşı kanıt (bot_trades replay +39.3R) farklı popülasyondu (VIXREG alt
    # kümesi) ve çürütülmedi — bu yüzden kod SİLİNMEDİ, yalnız varsayılan
    # kapatıldı. VIXREG_SELL_PATIENCE=True ile geri açılır.
    if favored == "SELL" and getattr(config, "VIXREG_SELL_PATIENCE", False):
        tick = mt5.symbol_info_tick(mt5_symbol)
        if tick:
            import trade_manager
            trade_manager.queue_sell(
                log, scope_key, tick.bid,
                float(config.VIX_REGIME_TP), float(config.VIX_REGIME_SL),
                opener=lambda: open_trade(scope_key, forexsai_sym, mt5_symbol,
                                          "SELL", cfg, voters, magic=magic))
        return
    open_trade(scope_key, forexsai_sym, mt5_symbol, favored, cfg, voters, magic=magic)


def main():
    mode = "CANLI İŞLEM" if config.LIVE_TRADING else "GÖZLEM (emir açmaz)"
    log.info("=" * 64)
    log.info("ForexSAI Demo Deney Botu başlıyor — MOD: %s", mode)
    log.info("Robust scope'lar: %s", ", ".join(config.ROBUST_SCOPES.keys()))
    # Aktif kapı/ayar dökümü — bayrakların çoğu config.py'de TANIMLI DEĞİL ve
    # getattr varsayılanıyla çalışıyor (config.py gitignore'da olduğu için
    # push edilemiyor). Bu satır "hangi ayar nereden geliyor" sorusunu logdan
    # cevaplanabilir kılar; (config) = dosyadan, (varsayılan) = koddan.
    def _src(name: str, default):
        return (getattr(config, name), "config") if hasattr(config, name) \
            else (default, "varsayılan")
    for _n, _d in (("TRADE_MGMT_ENABLED", True), ("MGMT_BE_MINUTES", 30),
                   ("MGMT_TRAIL_R", 0.6), ("MGMT_RUNNER_MIN_TP_SL_RATIO", 0.4),
                   ("MGMT_INCLUDE_CHREV", True),
                   ("TQ_ENABLED", True), ("TQ_FRIDAY_COOL", True),
                   ("TQ_COOL_HOURS_UTC", (15, 16, 17)),
                   ("TQ_COOL_FAMILIES", ("vixreg", "chrev")),
                   ("TQ_COOL_MIN_VOTERS", 2), ("TQ_FRIDAY_EXTRA_VOTES", 1),
                   ("TQ_DECIDER_APPROVAL", True), ("TQ_DECIDER_FRESH_MIN", 45),
                   ("TQ_DECIDER_MIN_SIZE", 0.3),
                   ("TREND_GATE_ENABLED", True), ("VIXREG_TREND_GATE", True),
                   ("VIXREG_SELL_PATIENCE", False), ("VIXREG_SELL_PATIENCE_MIN", 10),
                   ("CHREV_MODE_OVERRIDE", {}),
                   ("POSITION_GATE_ENABLED", True), ("VIXREG_POSITION_GATE", True),
                   ("POS_SELL_MIN", 0.40), ("POS_BUY_MAX", 0.60),
                   ("BACKEND_ADVICE_ENABLED", True), ("SHADOW_SCOPES_ENABLED", True),
                   ("VIXREG_SL_ATR_ENABLED", True), ("VIXREG_SL_ATR_MULT", 2.0),
                   ("VIXREG_SL_MIN", 60.0), ("VIXREG_SL_MAX", 200.0),
                   ("VIXREG_BACKEND_VETO", False), ("CHREV_BACKEND_VETO", False),
                   ("DAYCOMBO_ENABLED", True), ("DAYCOMBO_TP", 80.0),
                   ("DAYCOMBO_SL", 110.0),
                   ("USOIL_BREAKOUT_ENABLED", True), ("USOIL_BREAKOUT_DONCHIAN_N", 48),
                   ("USOIL_BREAKOUT_EMA_TREND", 200), ("USOIL_BREAKOUT_TP_ATR", 1.0),
                   ("USOIL_BREAKOUT_SL_ATR", 1.0),
                   ("MGMT_INCLUDE_USOIL_BREAKOUT", True), ("MGMT_USOIL_TRAIL_R", 1.0),
                   ("LIVE_TRADING", False)):
        _v, _from = _src(_n, _d)
        log.info("  ayar %-30s = %-8s (%s)", _n, _v, _from)
    log.info("=" * 64)

    if not connect_mt5():
        sys.exit(1)

    # AutoTrading / terminal teşhisi — retcode 10027 buradan görülür.
    at_ok = check_autotrading(verbose=True)
    if config.LIVE_TRADING and not at_ok:
        log.warning("CANLI mod açık ama AutoTrading kapalı — düzeltene kadar "
                    "emirler gönderilmeyecek. Bot taramaya devam ediyor.")

    # Başlangıçta broker'daki ENDEKS/EMTIA sembollerini göster (hisse hariç)
    # ki kullanıcı SYMBOL_MAP'i doğru adlarla eşleştirebilsin.
    all_syms = [s.name for s in (mt5.symbols_get() or [])]
    index_like = sorted(s for s in all_syms if not _looks_like_stock(s)
                        and any(k in s.upper() for k in
                        ("US", "NAS", "TEC", "GER", "DE", "DAX", "XTI",
                         "OIL", "WTI", "SPX", "30", "40", "100", "500")))
    log.info("Broker'da %d sembol var. Endeks/emtia adayları (hisse hariç):",
             len(all_syms))
    log.info("  %s", index_like[:40])
    log.info("→ NDX/GDAXI/USOIL karşılıkları bu listede DEĞİLSE config.py "
             "SYMBOL_MAP'i düzelt.")

    try:
        while True:
            log.info("─── tarama @ %s ───", datetime.now(timezone.utc).strftime("%H:%M:%S"))

            # ── Global risk geçidi (günlük zarar freni) ──
            if config.DAILY_MAX_LOSS and config.DAILY_MAX_LOSS > 0:
                try:
                    pnl = today_realized_pnl()
                except Exception as e:
                    pnl = 0.0; log.warning("günlük P/L okunamadı: %s", e)
                if pnl <= -config.DAILY_MAX_LOSS:
                    log.warning("⛔ GÜNLÜK ZARAR LİMİTİ (%.0f ≤ -%.0f) — yeni giriş YOK "
                                "(yarına kadar)", pnl, config.DAILY_MAX_LOSS)
                    time.sleep(config.POLL_SECONDS)
                    continue

            for scope_key, cfg in config.ROBUST_SCOPES.items():
                # ── Global pozisyon tavanı ──
                if total_open_positions() >= config.MAX_TOTAL_POSITIONS:
                    log.info("Global tavan dolu (%d) — kalan scope'lar atlandı",
                             config.MAX_TOTAL_POSITIONS)
                    break
                try:
                    check_scope(scope_key, cfg)
                except Exception as e:
                    log.exception("%s kontrolü hata: %s", scope_key, e)

            # ── CHANNEL_REVERSION scope'ları (mean-reversion, momentum'dan AYRI) ──
            if getattr(config, "CHANNEL_REVERSION_ENABLED", False):
                for cr_sym, cr_cfg in config.CHANNEL_REVERSION.items():
                    if total_open_positions() >= config.MAX_TOTAL_POSITIONS:
                        break
                    try:
                        check_channel_reversion(cr_sym, cr_cfg)
                    except Exception as e:
                        log.exception("ch-rev %s hata: %s", cr_sym, e)

            # ── VIX-REJİM NDX yön scope'u (makro→NDX, AYRI magic) ──
            if getattr(config, "VIX_REGIME_ENABLED", False) and \
                    total_open_positions() < config.MAX_TOTAL_POSITIONS:
                try:
                    check_vix_regime()
                except Exception as e:
                    log.exception("vix-regime hata: %s", e)

            # ── DAYCOMBO: gece-pozitif + 15m trend + yeşil 5m (AYRI magic+4, düşük lot) ──
            if getattr(config, "DAYCOMBO_ENABLED", True) and \
                    total_open_positions() < config.MAX_TOTAL_POSITIONS:
                try:
                    check_daycombo()
                except Exception as e:
                    log.exception("daycombo hata: %s", e)

            # ── USOIL BREAKOUT-DEVAM: Donchian(48×5m) kırılımı + EMA200 trend
            #    hizası (AYRI magic+5; 2026-08-06 araştırması, TEST %62.7 n=185) ──
            if getattr(config, "USOIL_BREAKOUT_ENABLED", True) and \
                    total_open_positions() < config.MAX_TOTAL_POSITIONS:
                try:
                    check_usoil_breakout()
                except Exception as e:
                    log.exception("usoil-breakout hata: %s", e)

            # ── REFLEX ENGINE (NDX momentum-continuation + 15dk time-stop, AYRI magic+3) ──
            #    Backend /api/reflex/live sinyallerini uygular. SHADOW varsayılan
            #    (REFLEX_LIVE=1 ile canlı). Kendi time-stop'unu yönetir.
            if getattr(config, "REFLEX_ENABLED", True):
                try:
                    reflex_exec.poll_reflex(log)
                except Exception as e:
                    log.exception("reflex hata: %s", e)

            # ── İŞLEM-SONRASI YÖNETİM: BE@30dk (NDX BUY) + kazananı-koştur
            #    (NDX+DAX BUY) + vixreg SELL sabır kuyruğu (kanıt:
            #    research/trade_mgmt_ndx/REPORT.md) ──
            # ── GÖLGE scope'lar (XAU): kanıt biriktir, işlem açma ──
            if getattr(config, "SHADOW_SCOPES_ENABLED", True):
                try:
                    check_shadow_scopes()
                except Exception as e:
                    log.warning("gölge scope döngü hatası: %s", e)

            if getattr(config, "TRADE_MGMT_ENABLED", True):
                try:
                    import trade_manager
                    trade_manager.manage_positions(mt5, log, resolve_symbol)
                    ndx_mt5 = resolve_symbol("NDX.INDX")
                    if ndx_mt5:
                        trade_manager.process_pending(mt5, log, ndx_mt5)
                except Exception as e:
                    log.exception("trade_manager hata: %s", e)
            time.sleep(config.POLL_SECONDS)
    except KeyboardInterrupt:
        log.info("Durduruldu (Ctrl+C).")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
