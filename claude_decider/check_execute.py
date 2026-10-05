"""check_execute.py — emir göndermeden icra zincirini doğrula (hesap modu + sembol başına order_check)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_decider as rd  # noqa: E402
import execute_mt5 as ex  # noqa: E402
from decide import stop_mults  # noqa: E402

mt5 = rd.mt5
if not rd.connect_mt5():
    sys.exit("MT5 bağlantısı yok")
acc = mt5.account_info()
print(f"hesap={acc.login} trade_mode={acc.trade_mode} (0=DEMO) server={acc.server} bakiye={acc.balance}")
print("terminal trade_allowed:", mt5.terminal_info().trade_allowed)
for sym, ms in rd._SYM_MAP.items():
    info, tick = mt5.symbol_info(ms), mt5.symbol_info_tick(ms)
    atr = ex._atr14(mt5, ms)
    if not (info and tick and atr):
        print(f"{sym}: veri eksik"); continue
    tp_atr, sl_atr = stop_mults(sym)
    tp, sl = ex.build_levels("BUY", tick.ask, atr, tp_atr, sl_atr)
    lot = ex.normalize_lot(1.0, info.volume_min, info.volume_max, info.volume_step)
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": ms, "volume": lot, "type": mt5.ORDER_TYPE_BUY,
           "price": tick.ask, "sl": round(sl, info.digits), "tp": round(tp, info.digits),
           "deviation": ex.DEVIATION_POINTS, "magic": ex.DECIDER_MAGIC,
           "comment": ex.mk_comment(sym, "BUY"), "type_time": mt5.ORDER_TIME_GTC}
    chk = ex.check_with_fill_modes(mt5, req, info)
    print(f"{sym:12s} {ms:10s} lot={lot} atr={atr:.3f} spread/ATR={(tick.ask-tick.bid)/atr:.3f} "
          f"stops_ok={ex.stops_ok(tick.ask, req['tp'], req['sl'], info.trade_stops_level, info.point)} "
          f"order_check retcode={getattr(chk,'retcode',None)} {getattr(chk,'comment','')}")
mt5.shutdown()
