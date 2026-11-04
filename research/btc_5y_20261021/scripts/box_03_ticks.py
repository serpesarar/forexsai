# Kutuda (MT5) çalışır — SALT OKUMA. Emir yok, dosya yazma yok.
# BTCUSD görünmüyorsa GEÇİCİ seçilir, sonda gizlenir.
# ARGS = {"days": 14} → son N günün tick bid/ask spread dağılımı
# (UTC saat = sunucu − ARGS["off_h"]), hafta içi/sonu, getiri-şoku anlarında spread.
import time
import numpy as np
import MetaTrader5 as mt5

SYM = "BTCUSD"
if not mt5.initialize():
    print("INIT_FAIL", mt5.last_error()); raise SystemExit
si = mt5.symbol_info(SYM)
was_visible = bool(si.visible)
if not was_visible:
    print("TEMP_SELECT", mt5.symbol_select(SYM, True))
    for _ in range(20):
        t = mt5.symbol_info_tick(SYM)
        if t is not None and t.time:
            break
        time.sleep(0.5)
try:
    tk = mt5.symbol_info_tick(SYM)
    off = int(ARGS.get("off_h", 3)) * 3600
    days = int(ARGS.get("days", 14))
    x = None
    for _ in range(6):
        x = mt5.copy_ticks_range(SYM, int(tk.time) - days * 86400, int(tk.time) + 60, mt5.COPY_TICKS_INFO)
        if x is not None and len(x) > 1000:
            break
        time.sleep(5)
    print("TICKS", None if x is None else len(x), mt5.last_error())
    ts = x["time_msc"].astype(np.int64) // 1000 - off   # UTC saniye
    sp = (x["ask"] - x["bid"]).astype(float)
    mid = (x["ask"] + x["bid"]) / 2
    rel = sp / mid * 100
    print("UTC_RANGE", time.strftime("%Y-%m-%d %H:%M %a", time.gmtime(int(ts[0]))),
          time.strftime("%Y-%m-%d %H:%M %a", time.gmtime(int(ts[-1]))))
    # zaman-ağırlıklı: her tick'in spread'i bir sonraki tick'e kadar geçerli
    dur = np.diff(ts, append=ts[-1]).clip(0, 300).astype(float)
    def q(v, w, p):
        o = np.argsort(v); cw = np.cumsum(w[o]); return float(v[o][np.searchsorted(cw, p * cw[-1])])
    def s(m):
        if not m.any(): return None
        return dict(n=int(m.sum()), tick_med=float(np.median(sp[m])), tick_p90=float(np.quantile(sp[m], .9)),
                    tick_p99=round(float(np.quantile(sp[m], .99)), 2), tw_mean=round(float(np.average(sp[m], weights=dur[m] + 1e-9)), 2),
                    tw_p90=round(q(sp[m], dur[m] + 1e-9, .9), 2), tw_p99=round(q(sp[m], dur[m] + 1e-9, .99), 2),
                    med_pct=round(float(np.median(rel[m])), 5), p90_pct=round(float(np.quantile(rel[m], .9)), 5),
                    max=round(float(sp[m].max()), 2))
    dow = (ts // 86400 + 3) % 7
    hr = (ts // 3600) % 24
    print("ALL", s(np.ones(len(ts), bool)))
    print("WEEKDAY", s(dow < 5)); print("WEEKEND", s(dow >= 5))
    for h in range(24):
        print("UTC_H", h, s(hr == h))
    # dakikalık mid getirisi büyükken spread
    mn = ts // 60
    u, idx = np.unique(mn, return_index=True)
    last_mid = mid[np.r_[idx[1:] - 1, len(mid) - 1]]
    r = np.abs(np.diff(np.log(last_mid)))
    big = u[1:][r > np.quantile(r, .99)]
    m = np.isin(mn, big)
    print("TOP1PCT_MOVE_MINUTES", s(m))
    print("SPREAD_VALUES_TOP", sorted(zip(*np.unique(np.round(sp, 2), return_counts=True)), key=lambda z: -z[1])[:12])
finally:
    if not was_visible:
        print("RESTORE_HIDE", mt5.symbol_select(SYM, False))
    mt5.shutdown()
