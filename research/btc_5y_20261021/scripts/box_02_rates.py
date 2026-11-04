# Kutuda (MT5) çalışır — SALT OKUMA. Emir yok, dosya yazma yok.
# BTCUSD görünmüyorsa GEÇİCİ seçilir, sonda gizlenir (önceki durum).
# ARGS = {"mode": "stats"} → M1 spread/gap özeti (60 gün)
# ARGS = {"mode": "dump", "d0": 14, "d1": 10} → [şimdi-d0, şimdi-d1] gün aralığı
#   M1 barları lzma+base64 sıkıştırılmış int dizileri olarak yazdırılır.
import time, collections, base64, lzma, datetime as dt
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
    print("TICK_server", tk.time, "utc_now", int(time.time()))
    srv_now = dt.datetime.fromtimestamp(tk.time, dt.timezone.utc)

    def get(d0, d1):
        a = srv_now - dt.timedelta(days=d0)
        b = srv_now - dt.timedelta(days=d1)
        r = None
        for i in range(8):
            r = mt5.copy_rates_range(SYM, mt5.TIMEFRAME_M1, a, b)
            if r is not None and len(r):
                break
            time.sleep(3)
        print("RANGE", a, b, None if r is None else len(r), mt5.last_error())
        return r

    if ARGS.get("mode") == "stats":
        r = get(ARGS.get("days", 60), 0)
        if r is None or not len(r):
            for n in (90000, 60000, 30000, 10000):
                r = mt5.copy_rates_from_pos(SYM, mt5.TIMEFRAME_M1, 0, n)
                print("FROMPOS", n, None if r is None else len(r), mt5.last_error())
                if r is not None and len(r):
                    break
        t = r["time"].astype(np.int64)
        print("M1_RANGE_server", time.strftime("%Y-%m-%d %H:%M %a", time.gmtime(int(t[0]))),
              time.strftime("%Y-%m-%d %H:%M %a", time.gmtime(int(t[-1]))), "n", len(t))
        d = np.diff(t) // 60
        big = [(time.strftime("%a %Y-%m-%d %H:%M", time.gmtime(int(t[i]))), int(d[i]))
               for i in np.where(d > 5)[0]]
        print("GAPS_gt1min", int((d > 1).sum()), "missing_min", int((d[d > 1] - 1).sum()), "n_gt5", len(big))
        print("BIGGAPS", big[:100])
        sp = r["spread"].astype(float) * si.point
        rel = sp / r["close"] * 100
        hrs = (t // 3600) % 24
        dow = (t // 86400 + 3) % 7  # 0=Pzt
        def s(m):
            return (int(m.sum()), round(float(np.median(sp[m])), 2), round(float(np.quantile(sp[m], .9)), 2),
                    round(float(sp[m].max()), 2), round(float(np.median(rel[m])), 5),
                    round(float(np.quantile(rel[m], .9)), 5), round(float(np.mean(sp[m])), 2))
        allm = np.ones(len(t), bool)
        print("SPREAD_ALL n,med$,p90$,max$,med%,p90%,mean$", s(allm))
        print("SPREAD_WEEKDAY", s(dow < 5)); print("SPREAD_WEEKEND", s(dow >= 5))
        for h in range(24):
            m = hrs == h
            if m.any(): print("SPREAD_H_server", h, s(m))
        for k in range(7):
            m = dow == k
            if m.any(): print("SPREAD_DOW_server", k, s(m))
        tv = r["tick_volume"]
        print("TICKVOL med,p10,zero", float(np.median(tv)), float(np.quantile(tv, .1)), int((tv == 0).sum()))
        print("ZEROSPREAD_bars", int((r["spread"] == 0).sum()))
        # hafta sonu bar sayısı ve gün başına bar
        days = collections.Counter(time.strftime("%Y-%m-%d %a", time.gmtime(int(x))) for x in t)
        print("BARS_PER_DAY", sorted(days.items())[-21:])
    else:
        r = get(ARGS["d0"], ARGS["d1"])
        t = r["time"].astype(np.int64)
        cols = [np.diff(t, prepend=0)]
        for c in ("open", "high", "low", "close"):
            v = np.round(r[c] * 100).astype(np.int64)
            cols.append(np.diff(v, prepend=0))
        cols += [r["spread"].astype(np.int64), r["tick_volume"].astype(np.int64)]
        raw = np.stack(cols).astype(np.int64).tobytes()
        blob = base64.b64encode(lzma.compress(raw, preset=9)).decode()
        print("DUMP_N", len(t), "B64LEN", len(blob))
        print("DUMP_BEGIN")
        for i in range(0, len(blob), 4000):
            print(blob[i:i + 4000])
        print("DUMP_END")
finally:
    if not was_visible:
        print("RESTORE_HIDE", mt5.symbol_select(SYM, False))
    mt5.shutdown()
