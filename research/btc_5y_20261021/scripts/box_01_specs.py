# Kutuda (MT5) çalışır — SALT OKUMA. Emir göndermez, dosya yazmaz.
# Veri için sembol Market Watch'ta olmalı: görünmüyorsa GEÇİCİ seçilir ve
# sonda eski hâline (gizli) döndürülür. Açık terminale kwargs'sız attach olur.
# remote.py sh ile zlib+base64 exec olarak gönderilir (03_box_send.py).
import time, collections, statistics as st
import MetaTrader5 as mt5

if not mt5.initialize():
    print("INIT_FAIL", mt5.last_error()); raise SystemExit
ai = mt5.account_info()
print("ACCOUNT", {"company": ai.company, "server": ai.server, "currency": ai.currency,
                  "leverage": ai.leverage, "trade_mode": ai.trade_mode, "margin_mode": ai.margin_mode})
ti = mt5.terminal_info()
print("TERMINAL", {"build": mt5.version(), "maxbars": ti.maxbars, "connected": ti.connected})
syms = mt5.symbols_get("*BTC*") or ()
print("BTC_SYMBOLS", [(s.name, s.path, s.visible, s.trade_mode) for s in syms])
cands = [s for s in syms if s.name.upper().startswith("BTCUSD")] or list(syms)
for s in cands[:1]:
    d = s._asdict()
    keep = ["name", "path", "description", "currency_base", "currency_profit", "currency_margin",
            "digits", "point", "spread", "spread_float", "trade_contract_size", "trade_tick_size",
            "trade_tick_value", "volume_min", "volume_max", "volume_step", "swap_mode", "swap_long",
            "swap_short", "swap_rollover3days", "trade_stops_level", "trade_freeze_level",
            "trade_mode", "trade_calc_mode", "trade_exemode", "filling_mode", "order_mode",
            "margin_initial", "margin_maintenance", "margin_hedged", "visible", "select",
            "bid", "ask", "time", "session_deals", "volume", "volumehigh"]
    print("SYMINFO", {k: d.get(k) for k in keep})
sym = cands[0].name if cands else None
print("CHOSEN", sym)
was_visible = bool(cands[0].visible) if cands else True
if sym and not was_visible:
    print("TEMP_SELECT", mt5.symbol_select(sym, True))
    for _ in range(20):
        if mt5.symbol_info_tick(sym) is not None and mt5.symbol_info_tick(sym).time:
            break
        time.sleep(0.5)
if sym:
    tk = mt5.symbol_info_tick(sym)
    now = time.time()
    print("TICK", tk._asdict() if tk else None, "utc_now", now,
          "offset_h", round((tk.time - now) / 3600, 2) if tk else None)
    for lot in (0.01, 1.0):
        try:
            print("MARGIN", lot, mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, sym, lot, tk.ask))
        except Exception as e:
            print("MARGIN_ERR", e)
    try:
        print("PROFIT_1lot_+100usd", mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, sym, 1.0, tk.ask, tk.ask + 100))
    except Exception as e:
        print("PROFIT_ERR", e)
    r = None
    for _ in range(10):
        r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 100000)
        if r is not None and len(r) > 50000:
            break
        time.sleep(3)
    print("M1_BARS", None if r is None else len(r), mt5.last_error())
    if r is not None and len(r):
        pt = cands[0].point
        t0, t1 = int(r["time"][0]), int(r["time"][-1])
        print("M1_RANGE_server", time.strftime("%Y-%m-%d %H:%M", time.gmtime(t0)),
              time.strftime("%Y-%m-%d %H:%M", time.gmtime(t1)))
        gaps = collections.Counter()
        biggaps = []
        for a, b in zip(r["time"][:-1], r["time"][1:]):
            g = int(b - a) // 60
            if g > 1:
                gaps["gt1"] += 1
                if g > 15:
                    biggaps.append((time.strftime("%a %Y-%m-%d %H:%M", time.gmtime(int(a))), g))
        print("GAPS_gt1min", gaps["gt1"], "n_gt15", len(biggaps))
        print("BIGGAPS", biggaps[:80])
        byhour = collections.defaultdict(list); bydow = collections.defaultdict(list)
        allsp = []
        for row in r:
            tm = time.gmtime(int(row["time"]))
            sp = float(row["spread"]) * pt
            rel = sp / float(row["close"]) * 100
            byhour[tm.tm_hour].append((sp, rel)); bydow[tm.tm_wday].append((sp, rel)); allsp.append((sp, rel))
        def q(v, p):
            v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]
        def summ(lst):
            a = [x[0] for x in lst]; b = [x[1] for x in lst]
            return (len(a), round(st.median(a), 3), round(q(a, .9), 3), round(max(a), 3),
                    round(st.median(b), 5), round(q(b, .9), 5))
        print("SPREAD_ALL n,med$,p90$,max$,med%,p90%", summ(allsp))
        for h in range(24):
            if byhour[h]: print("SPREAD_H_server", h, summ(byhour[h]))
        for d in range(7):
            if bydow[d]: print("SPREAD_DOW_server", d, summ(bydow[d]))
        tv = [int(x) for x in r["tick_volume"]]
        print("TICKVOL med,p10,zero", st.median(tv), q(tv, .1), sum(1 for x in tv if x == 0))
    # Gerçek bid/ask tick spread'i (son 2 gün)
    tk2 = mt5.copy_ticks_from(sym, int(tk.time) - 2 * 86400, 2_000_000, mt5.COPY_TICKS_INFO)
    if tk2 is not None and len(tk2):
        sp = [float(a - b) for a, b in zip(tk2["ask"], tk2["bid"])]
        rel = [float((a - b) / b * 100) for a, b in zip(tk2["ask"], tk2["bid"])]
        sp.sort(); rel.sort()
        print("TICKS n", len(sp), "med$", sp[len(sp) // 2], "p90$", sp[int(.9 * len(sp))],
              "p99$", sp[int(.99 * len(sp))], "med%", round(rel[len(rel) // 2], 5),
              "p90%", round(rel[int(.9 * len(rel))], 5))
        hb = collections.defaultdict(list)
        for t, a, b in zip(tk2["time"], tk2["ask"], tk2["bid"]):
            hb[time.gmtime(int(t)).tm_hour].append(float(a - b))
        for h in sorted(hb):
            v = sorted(hb[h]); print("TICKSPREAD_H_server", h, len(v), v[len(v) // 2], v[int(.9 * len(v))])
if sym and not was_visible:
    print("RESTORE_HIDE", mt5.symbol_select(sym, False))
mt5.shutdown()
