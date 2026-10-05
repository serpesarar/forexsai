"""
execute_mt5.py — Decider kararını MT5'e GERÇEK emir olarak gönder (2026-10-05, kullanıcı kararı:
"demo'da küçük boyutla aç").
=============================================================================
Tasarım ilkeleri (hepsi kodla zorlanır, prompt'la değil):
 1. YALNIZ DEMO hesap: account_info().trade_mode != DEMO → emir YOK (ALLOW_REAL_ACCOUNT=False).
 2. Küçük boyut: lot = LIVE_BASE_LOT × min(size_factor, LIVE_SIZE_CAP), step'e yuvarlanır.
 3. Sembol başına en fazla 1 decider pozisyonu; toplam LIVE_MAX_OPEN; günlük LIVE_MAX_ORDERS_PER_DAY.
 4. TP/SL = decide.build_trade ile AYNI geometri (ATR çarpanları) — gölge grade ile birebir
    karşılaştırılabilir kalsın. Giriş = anlık tick (BUY→ask, SELL→bid), mesafeler entry'den.
 5. Ayrı magic (DECIDER_MAGIC): bot'un trade_manager'ı (BE/timestop) yalnız kendi magic'lerine
    dokunur → decider pozisyonlarını yönetmez, çakışmaz.
 6. order_check ÖNCE; ardından filling-mode döngüsü (SpotCrude/XTI 10030 dersi).
 7. Her deneme (gönderildi/reddedildi/atlandı) live_orders.jsonl'e yazılır.
 8. Kill-switch: env DECIDER_EXECUTE=0 veya HERE/EXECUTE_OFF dosyası → hiçbir emir gitmez.
Çıkış politikası: sabit TP/SL (USOIL trail_1.0 gölge-grade'de ayrı ölçülüyor, burada uygulanmaz).
"""
from __future__ import annotations
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE_ORDERS_JSONL = HERE / "live_orders.jsonl"
KILL_FILE = HERE / "EXECUTE_OFF"

# ── Sabitler (magic number yasak → adlandırılmış) ────────────────────────────
DECIDER_MAGIC = 52890989          # bot: 52890969 (+1,+2,+3,+5 kullanımda) — +20 AYRI slot
LIVE_BASE_LOT = 0.10              # size_factor=1.0'ın lot karşılığı (bot demo LOT_SIZE ile aynı)
LIVE_SIZE_CAP = 0.3               # "küçük boyut": size_factor bu tavana kırpılır → ≤0.03 lot
LIVE_MAX_OPEN = 3                 # eşzamanlı decider pozisyonu (tüm semboller)
LIVE_MAX_ORDERS_PER_DAY = 10      # UTC günü başına gönderilen emir
MAX_SPREAD_ATR = 0.15             # spread/ATR bunu aşarsa giriş sürtünmesi RR'yi yer → atla
DEVIATION_POINTS = 30             # slippage toleransı
ALLOW_REAL_ACCOUNT = False        # True yapılmadıkça gerçek (live) hesapta emir gitmez
FILLING_UNSUPPORTED = 10030       # TRADE_RETCODE_INVALID_FILL


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _log(rec: dict) -> None:
    rec = {"ts": _now().isoformat(timespec="seconds"), **rec}
    try:
        with open(LIVE_ORDERS_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except OSError as e:
        print(f"  live_orders yazılamadı: {e}")


def killed() -> bool:
    return os.getenv("DECIDER_EXECUTE", "1") == "0" or KILL_FILE.exists()


def mk_comment(symbol: str, direction: str) -> str:
    """ASCII + ≤28 karakter (≥31 → order_send reddi; 2026-06-29 dersi)."""
    c = f"CDEC {symbol.split('.')[0][:8]} {direction}".encode("ascii", "ignore").decode()
    return c[:28]


def normalize_lot(size_factor: float, vol_min: float, vol_max: float, vol_step: float) -> float:
    """size_factor → lot: taban×min(sf, cap), step'e AŞAĞI yuvarla, [min,max] içine al."""
    raw = LIVE_BASE_LOT * min(max(float(size_factor), 0.0), LIVE_SIZE_CAP)
    step = vol_step if vol_step and vol_step > 0 else 0.01
    lot = math.floor(raw / step + 1e-9) * step
    lot = max(lot, vol_min or step)
    lot = min(lot, vol_max or lot)
    return round(lot, 8)


def build_levels(direction: str, entry: float, atr: float, tp_atr: float, sl_atr: float) -> tuple[float, float]:
    buy = direction.upper() == "BUY"
    tp = entry + tp_atr * atr if buy else entry - tp_atr * atr
    sl = entry - sl_atr * atr if buy else entry + sl_atr * atr
    return tp, sl


def stops_ok(entry: float, tp: float, sl: float, stops_level: int, point: float) -> bool:
    """Broker min stop mesafesi (trade_stops_level × point) — altındaysa emir reddedilir."""
    need = (stops_level or 0) * (point or 0.0)
    return abs(tp - entry) >= need and abs(sl - entry) >= need


def _atr14(mt5, mt5_symbol: str) -> float | None:
    rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M5, 0, 40)
    if rates is None or len(rates) < 16:
        return None
    trs = []
    for i in range(1, len(rates)):
        h, l, pc = float(rates[i]["high"]), float(rates[i]["low"]), float(rates[i - 1]["close"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-14:]) / 14.0


def _today_order_count() -> int:
    if not LIVE_ORDERS_JSONL.exists():
        return 0
    day = _now().strftime("%Y-%m-%d")
    n = 0
    for ln in LIVE_ORDERS_JSONL.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if r.get("status") == "sent" and str(r.get("ts", "")).startswith(day):
            n += 1
    return n


def _send_with_fill_modes(mt5, request: dict, info):
    fm = getattr(info, "filling_mode", 0) if info else 0
    modes = []
    if fm & 2:
        modes.append(mt5.ORDER_FILLING_IOC)
    if fm & 1:
        modes.append(mt5.ORDER_FILLING_FOK)
    modes.append(mt5.ORDER_FILLING_RETURN)
    result = None
    for mode in modes:
        request["type_filling"] = mode
        result = mt5.order_send(request)
        if result is None:
            continue
        if result.retcode != FILLING_UNSUPPORTED:
            return result
    return result


def send_order(mt5, sit_symbol: str, mt5_symbol: str, dec: dict, atr: float | None,
               tp_atr: float, sl_atr: float) -> dict:
    """Kararı emre çevir. Dönüş: {status: sent|skipped|rejected, reason, ...} (her zaman loglanır)."""
    direction = str(dec.get("direction") or "").upper()
    rec = {"symbol": sit_symbol, "mt5_symbol": mt5_symbol, "direction": direction,
           "size_factor": dec.get("size_factor"), "reason": str(dec.get("reason"))[:160]}

    def done(status: str, why: str, **kw) -> dict:
        out = {**rec, "status": status, "why": why, **kw}
        _log(out)
        print(f"  [icra] {sit_symbol} {direction}: {status} — {why}")
        return out

    if killed():
        return done("skipped", "kill-switch (DECIDER_EXECUTE=0 veya EXECUTE_OFF dosyası)")
    if direction not in ("BUY", "SELL"):
        return done("skipped", "yön yok")
    acc = mt5.account_info()
    if acc is None:
        return done("skipped", "account_info yok")
    if acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO and not ALLOW_REAL_ACCOUNT:
        return done("skipped", f"DEMO DEĞİL (trade_mode={acc.trade_mode}) — gerçek hesapta emir yasak")
    term = mt5.terminal_info()
    if term is not None and not term.trade_allowed:
        return done("skipped", "terminalde algo trading kapalı")
    poss = [p for p in (mt5.positions_get() or []) if p.magic == DECIDER_MAGIC]
    if any(p.symbol == mt5_symbol for p in poss):
        return done("skipped", "bu sembolde zaten açık decider pozisyonu")
    if len(poss) >= LIVE_MAX_OPEN:
        return done("skipped", f"eşzamanlı üst sınır ({LIVE_MAX_OPEN})")
    if _today_order_count() >= LIVE_MAX_ORDERS_PER_DAY:
        return done("skipped", f"günlük emir sınırı ({LIVE_MAX_ORDERS_PER_DAY})")
    info = mt5.symbol_info(mt5_symbol)
    tick = mt5.symbol_info_tick(mt5_symbol)
    if info is None or tick is None:
        return done("skipped", "symbol_info/tick yok")
    atr = atr or _atr14(mt5, mt5_symbol)
    if not atr:
        return done("skipped", "ATR hesaplanamadı")
    buy = direction == "BUY"
    entry = tick.ask if buy else tick.bid
    spread = tick.ask - tick.bid
    if spread / atr > MAX_SPREAD_ATR:
        return done("skipped", f"spread/ATR={spread/atr:.3f} > {MAX_SPREAD_ATR}")
    tp, sl = build_levels(direction, entry, atr, tp_atr, sl_atr)
    digits = info.digits
    tp, sl = round(tp, digits), round(sl, digits)
    if not stops_ok(entry, tp, sl, info.trade_stops_level, info.point):
        return done("skipped", "TP/SL broker min stop mesafesinin altında")
    lot = normalize_lot(dec.get("size_factor") or 0.0, info.volume_min, info.volume_max, info.volume_step)
    request = {"action": mt5.TRADE_ACTION_DEAL, "symbol": mt5_symbol, "volume": lot,
               "type": mt5.ORDER_TYPE_BUY if buy else mt5.ORDER_TYPE_SELL,
               "price": entry, "sl": sl, "tp": tp, "deviation": DEVIATION_POINTS,
               "magic": DECIDER_MAGIC, "comment": mk_comment(sit_symbol, direction),
               "type_time": mt5.ORDER_TIME_GTC}
    rec.update({"lot": lot, "entry": entry, "tp": tp, "sl": sl, "atr": round(atr, 5),
                "spread": round(spread, 5)})
    # order_check: filling-mode ayrımından bağımsız, margin/stop/volume doğrulaması
    request["type_filling"] = mt5.ORDER_FILLING_RETURN
    chk = mt5.order_check(request)
    if chk is None or chk.retcode not in (0, mt5.TRADE_RETCODE_DONE):
        code = getattr(chk, "retcode", None)
        comment = getattr(chk, "comment", mt5.last_error())
        if code != FILLING_UNSUPPORTED:        # filling hatası dışındaki ret gerçek ret
            return done("rejected", f"order_check ret={code} {comment}")
    res = _send_with_fill_modes(mt5, request, info)
    if res is None:
        return done("rejected", f"order_send None: {mt5.last_error()}")
    if res.retcode != mt5.TRADE_RETCODE_DONE:
        return done("rejected", f"retcode={res.retcode} {getattr(res, 'comment', '')}")
    return done("sent", "emir dolduruldu", ticket=getattr(res, "order", None),
                fill_price=getattr(res, "price", None))
