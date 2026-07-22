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

import requests

try:
    import MetaTrader5 as mt5
except ImportError:
    print("HATA: MetaTrader5 paketi yok. Kur:  pip install -r requirements.txt")
    sys.exit(1)

import config
import reflex_exec
from sr_zones import detect_zones, plan_sr_entry, momentum_stretch
from channel_filter import is_channel_rejection, is_mean_reversion

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


def _fixed_distances(price: float, cfg: dict, bot_signal: dict | None) -> tuple[float, float]:
    """Araştırılmış sabit tp/sl mesafesi (index: puan, USOIL: %). Backend
    optimized SL varsa SL mesafesini ondan al."""
    if cfg["is_pct"]:
        tp_d = price * cfg["tp"] / 100.0
        sl_d = price * cfg["sl"] / 100.0
    else:
        tp_d = float(cfg["tp"])
        sl_d = float(cfg["sl"])
    if bot_signal and bot_signal.get("sl_price"):
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

    fixed_tp, fixed_sl = _fixed_distances(price, cfg, bot_signal)

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
        min_tp_dist=config.SR_MIN_TP_DIST.get(forexsai_sym, 0.0))

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

    volume = float(config.LOT_SIZE)
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
    # Türetilmiş TP/SL mesafesi — index: puan, USOIL: yüzde.
    if cfg["is_pct"]:
        tp_dist = price * cfg["tp"] / 100.0
        sl_dist = price * cfg["sl"] / 100.0
    else:
        tp_dist = float(cfg["tp"])
        sl_dist = float(cfg["sl"])

    if direction == "BUY":
        tp, sl = price + tp_dist, price - sl_dist
        order_type = mt5.ORDER_TYPE_BUY
    else:
        tp, sl = price - tp_dist, price + sl_dist
        order_type = mt5.ORDER_TYPE_SELL

    digits = info.digits
    tp, sl, price = round(tp, digits), round(sl, digits), round(price, digits)

    line = (f"{scope_key} | {mt5_symbol} {direction} @ {price} "
            f"TP={tp} SL={sl} lot={config.LOT_SIZE} (oy: {','.join(voters)})")

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
        "volume": float(config.LOT_SIZE),
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

    lot_mult = float(bot_signal.get("effective_lot_multiplier") or 1.0)
    volume = round(float(config.LOT_SIZE) * lot_mult, 2)
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


def check_channel_reversion(forexsai_sym: str, cfg: dict) -> None:
    """MEAN-REVERSION scope (momentum'dan AYRI): pulse3 sinyali + fiyat 30m linreg
    trend-çizgisinden ≥2.5σ ötede (kanal-rejection) → market giriş, sabit tp/sl.
    Araştırma: WR %44 → %82-88 OOS. Yalnız doğrulanmış sembol+yönlerde (config)."""
    mt5_symbol = resolve_symbol(forexsai_sym)
    if not mt5_symbol:
        return
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
    tf_const = getattr(mt5, _CR_TF.get(config.CHANNEL_REVERSION_MT5_TF, "TIMEFRAME_M30"))
    bars = candles_tf(mt5_symbol, tf_const, 60)
    if not bars or len(bars) < 55:
        return
    ok, source, z = is_mean_reversion(bars, direction)     # kanal z≥2.5 VEYA vwap z≥2.0
    scope_key = f"{forexsai_sym}:{direction}:CHREV"
    if not ok:
        log.info("%s — mean-reversion YOK (z=%.2f) → açılmadı", scope_key, z)
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
    if not voters:
        log.info("%s — VIX=%.1f favored=%s ama model sinyali yok → açılmadı",
                 scope_key, vix, favored)
        return
    log.info("%s — VIX=%.1f favored=%s, %d model onaylıyor → market giriş",
             scope_key, vix, favored, len(voters))
    cfg = {"tp": config.VIX_REGIME_TP, "sl": config.VIX_REGIME_SL, "is_pct": False}
    # SELL sabır kapısı (kanıt: Δ+39.3R — hızlı ölen SELL'ler ilk 10dk'da
    # kendini ele veriyor; research/trade_mgmt_ndx). BUY'a UYGULANMAZ.
    if favored == "SELL" and getattr(config, "VIXREG_SELL_PATIENCE", True):
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
