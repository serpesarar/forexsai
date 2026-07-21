"""Aşama 3 — genişletilmiş hipotez uzayı: giriş zamanlaması, SL-sonrası
re-entry, TP-sonrası devam, kısmi kâr, yol-şekli kuralları.

Bar verisi 2026-07-21'e genişletilir (SL/TP SONRASI ne olduğunu görmek için).
Tüm kurallar bar-kapanışı kararlı, sızıntısız; dolumlar konservatif.
Çoklu-test uyarısı: ~50 test tarandı → yalnız P(+)≥%97 + iki-kohort-tutarlı +
parametre-düz adaylar 'bulgu' sayılır.
"""
from __future__ import annotations

import bisect
import csv
import json
import random
import statistics
from datetime import timedelta
from pathlib import Path

from replay import load, trade_bars, replay, parse_ts, MAX_BARS
from analyze2 import run_strategy, bootstrap_delta, be_after

HERE = Path(__file__).resolve().parent
random.seed(11)
EXT = HERE / "bars_1m_ext.csv"


def extend_bars() -> None:
    if EXT.exists():
        return
    import sys
    sys.path.insert(0, str(HERE.parents[1] / "backend"))
    from build_dataset import load_bars_supabase
    extra = load_bars_supabase("2026-06-26T00:00:00+00:00", "2026-07-22T00:00:00+00:00")
    bars = {}
    with open(HERE / "bars_1m.csv") as f:
        for r in csv.DictReader(f):
            bars[int(r["ts"])] = r
    with open(EXT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close"])
        merged = dict(bars)
        for ts, b in extra.items():
            if ts not in merged:
                merged[ts] = {"ts": ts, "open": b["open"], "high": b["high"],
                              "low": b["low"], "close": b["close"]}
        for ts in sorted(merged):
            r = merged[ts]
            w.writerow([ts, r["open"], r["high"], r["low"], r["close"]])
    print(f"bars_1m_ext.csv: {len(merged)} bar")


def load_ext():
    trades = [t for t in json.load(open(HERE / "trades.json")) if t.get("geometry_ok")]
    bars = {}
    with open(EXT) as f:
        for r in csv.DictReader(f):
            bars[int(r["ts"])] = {"o": float(r["open"]), "h": float(r["high"]),
                                  "l": float(r["low"]), "c": float(r["close"])}
    return trades, bars, sorted(bars)


def seq_from(ts0: int, bars, keys, n=MAX_BARS):
    i = bisect.bisect_right(keys, ts0)
    return [(k, bars[k]) for k in keys[i:i + n]]


def base_path(t, seq):
    """(outcome, exit_idx, yol close-r listesi) — orijinal SL/TP, SL-önce."""
    e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
    closes = []
    for idx, (ts, b) in enumerate(seq):
        if sign > 0:
            hit_sl, hit_tp = b["l"] <= t["sl_px"], b["h"] >= t["tp_px"]
        else:
            hit_sl, hit_tp = b["h"] >= t["sl_px"], b["l"] <= t["tp_px"]
        if hit_sl:
            return "sl", idx, closes
        if hit_tp:
            return "tp", idx, closes
        closes.append(sign * (b["c"] - e) / t["sl_dist"])
    return "open", len(seq), closes


def agg(rs):
    n = len(rs)
    w = sum(1 for r in rs if r > 0.02)
    l = sum(1 for r in rs if r < -0.02)
    return {"n": n, "wr": round(100 * w / max(1, w + l), 1),
            "avg_r": round(statistics.mean(rs), 3) if rs else None,
            "tot_r": round(sum(rs), 2)}


def main():
    extend_bars()
    trades, bars, keys = load_ext()
    seqs = {t["pid"]: trade_bars(t, bars, keys) for t in trades}
    trades = [t for t in trades if len(seqs[t["pid"]]) >= 5]
    buys = [t for t in trades if t["direction"] == "BUY"]
    report = {}

    # ═══ TEŞHİSLER ═══════════════════════════════════════════════════════════
    # D1: Dip ZAMANLAMASI ayrıştırıyor mu? (erken dip vs geç dip → kazanma)
    d1 = {"dip<=10m": [0, 0], "dip11-30m": [0, 0], "dip>30m": [0, 0], "hiç": [0, 0]}
    for t in trades:
        out, idx, closes = base_path(t, seqs[t["pid"]])
        if out == "open":
            continue
        t_dip = next((i + 1 for i, r in enumerate(closes) if r <= -0.5), None)
        key = ("hiç" if t_dip is None else
               "dip<=10m" if t_dip <= 10 else
               "dip11-30m" if t_dip <= 30 else "dip>30m")
        d1[key][0 if out == "tp" else 1] += 1
    report["D1_dip_timing"] = {k: {"tp": v[0], "sl": v[1],
                                   "p_win": round(100 * v[0] / max(1, sum(v)), 1)}
                              for k, v in d1.items()}

    # D2: SL SONRASI — fiyat girişe geri dönüyor mu (stop-avı)?
    rec60 = rec240 = cont = n_sl = 0
    for t in trades:
        out, idx, _ = base_path(t, seqs[t["pid"]])
        if out != "sl":
            continue
        n_sl += 1
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        after = seqs[t["pid"]][idx + 1: idx + 1 + 240]
        t_rec = next((i + 1 for i, (ts, b) in enumerate(after)
                      if sign * (b["c"] - e) >= 0), None)
        if t_rec is not None:
            rec240 += 1
            if t_rec <= 60:
                rec60 += 1
        else:
            cont += 1
    report["D2_post_sl"] = {"n_sl": n_sl, "girise_donen_60m": rec60,
                            "girise_donen_240m": rec240, "donmeyen": cont,
                            "p_stophunt_240m": round(100 * rec240 / max(1, n_sl), 1)}

    # D3: TP SONRASI — devam ne kadar? (kazananı koşturma potansiyeli)
    ext_more = []
    for t in trades:
        out, idx, _ = base_path(t, seqs[t["pid"]])
        if out != "tp":
            continue
        sign = 1 if t["direction"] == "BUY" else -1
        after = seqs[t["pid"]][idx + 1: idx + 1 + 240]
        if not after:
            continue
        best = max((sign * (b["c"] - t["tp_px"]) for ts, b in after), default=0)
        ext_more.append(best / t["sl_dist"])
    report["D3_post_tp"] = {
        "n": len(ext_more),
        "medyan_ek_R": round(statistics.median(ext_more), 3) if ext_more else None,
        "p75_ek_R": round(sorted(ext_more)[int(0.75 * len(ext_more))], 3) if ext_more else None,
        "ek>=0.5R_oran": round(100 * sum(1 for x in ext_more if x >= 0.5) / max(1, len(ext_more)), 1)}

    # D4: HIZLI BAŞLANGIÇ — ilk 10dk'da +0.3R gören vs görmeyen
    fast = [0, 0]; slow = [0, 0]
    for t in trades:
        out, idx, closes = base_path(t, seqs[t["pid"]])
        if out == "open":
            continue
        early_max = max(closes[:10], default=(0.727 if out == "tp" and not closes else 0))
        (fast if early_max >= 0.3 else slow)[0 if out == "tp" else 1] += 1
    report["D4_fast_start"] = {
        "hizli": {"tp": fast[0], "sl": fast[1], "p_win": round(100 * fast[0] / max(1, sum(fast)), 1)},
        "yavas": {"tp": slow[0], "sl": slow[1], "p_win": round(100 * slow[0] / max(1, sum(slow)), 1)}}

    # D5: BUY BE30 iyileşmesi saat dilimine göre
    base_buy = run_strategy(buys, seqs, None)
    be30_buy = run_strategy(buys, seqs, be_after(30))
    bb = {x["pid"]: x for x in base_buy}
    hours = {}
    for t, x in zip(buys, be30_buy):
        h = parse_ts(t["entry_time"]) // 3600 % 24
        bucket = f"{(h // 6) * 6:02d}-{(h // 6) * 6 + 6:02d}utc"
        hours.setdefault(bucket, []).append(x["r"] - bb[x["pid"]]["r"])
    report["D5_be30_buy_hourly_delta"] = {k: {"n": len(v), "delta": round(sum(v), 2)}
                                          for k, v in sorted(hours.items())}

    # ═══ YENİ STRATEJİLER ════════════════════════════════════════════════════
    strat = {}

    def per_trade_new(fn):
        rs_all, rs_buy, rs_sell = [], [], []
        for t in trades:
            r = fn(t)
            if r is None:
                continue
            rs_all.append(r)
            (rs_buy if t["direction"] == "BUY" else rs_sell).append(r)
        return {"all": agg(rs_all), "BUY": agg(rs_buy), "SELL": agg(rs_sell)}

    def n1_reenter_after_sl(t):          # SL sonrası girişe dönüşte AYNI yön re-entry
        out, idx, _ = base_path(t, seqs[t["pid"]])
        if out == "tp":
            return t["tp_dist"] / t["sl_dist"]
        if out != "sl":
            return None
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        after = seqs[t["pid"]][idx + 1: idx + 1 + 240]
        for i, (ts, b) in enumerate(after):
            if sign * (b["c"] - e) >= 0:              # girişe döndü → re-enter
                e2 = b["c"]
                t2 = {**t, "entry_px": e2,
                      "tp_px": e2 + sign * t["tp_dist"], "sl_px": e2 - sign * t["sl_dist"]}
                out2, idx2, _ = base_path(t2, after[i + 1:])
                r2 = (t["tp_dist"] / t["sl_dist"] if out2 == "tp"
                      else -1.0 if out2 == "sl" else 0.0)
                return -1.0 + r2
        return -1.0
    strat["N1_reenter_sl_recovery"] = per_trade_new(n1_reenter_after_sl)

    def n2_reverse_after_sl(t):          # SL sonrası TERS yön
        out, idx, _ = base_path(t, seqs[t["pid"]])
        if out == "tp":
            return t["tp_dist"] / t["sl_dist"]
        if out != "sl":
            return None
        sign = 1 if t["direction"] == "BUY" else -1
        after = seqs[t["pid"]][idx + 1:]
        if not after:
            return -1.0
        e2 = after[0][1]["o"]
        t2 = {**t, "direction": "SELL" if sign > 0 else "BUY", "entry_px": e2,
              "tp_px": e2 - sign * t["tp_dist"], "sl_px": e2 + sign * t["sl_dist"]}
        out2, _, _ = base_path(t2, after[1:])
        r2 = (t["tp_dist"] / t["sl_dist"] if out2 == "tp"
              else -1.0 if out2 == "sl" else 0.0)
        return -1.0 + r2
    strat["N2_reverse_after_sl"] = per_trade_new(n2_reverse_after_sl)

    def n3_run_winners(t):               # TP'de çıkma; 0.6R iz süren SL ile koştur
        seq = seqs[t["pid"]]
        out, idx, _ = base_path(t, seq)
        if out == "sl":
            return -1.0
        if out != "tp":
            return None
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        sl = t["tp_px"] - sign * 0.6 * t["sl_dist"]   # başlangıç izi
        for ts, b in seq[idx + 1: idx + 1 + 480]:
            if (sign > 0 and b["l"] <= sl) or (sign < 0 and b["h"] >= sl):
                return sign * (sl - e) / t["sl_dist"]
            trail = b["c"] - sign * 0.6 * t["sl_dist"]
            if sign * (trail - sl) > 0:
                sl = trail
        return sign * (sl - e) / t["sl_dist"]         # veri bitti → izde kapat
    strat["N3_run_winners_trail06"] = per_trade_new(n3_run_winners)

    def n4_partial_half(t):              # yarısı 0.5TP'de + BE, kalan TP'de
        seq = seqs[t["pid"]]
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        half_px = e + sign * 0.5 * t["tp_dist"]
        rr = t["tp_dist"] / t["sl_dist"]
        for idx, (ts, b) in enumerate(seq):
            hit_sl = (b["l"] <= t["sl_px"]) if sign > 0 else (b["h"] >= t["sl_px"])
            hit_half = (b["h"] >= half_px) if sign > 0 else (b["l"] <= half_px)
            if hit_sl:
                return -1.0
            if hit_half:
                rest_t = {**t, "sl_px": e}            # kalan yarı BE stoplu
                out2, _, _ = base_path(rest_t, seq[idx + 1:])
                rest = rr if out2 == "tp" else 0.0
                return 0.5 * (0.5 * rr) + 0.5 * rest
        return None
    strat["N4_partial_half_be"] = per_trade_new(n4_partial_half)

    def n5_tp_decay(state, r, f, m, closes):          # 60dk sonra TP'yi yarıya çek
        if m >= 60 and not state["mem"].get("dec"):
            state["mem"]["dec"] = True
            return {"tp": state["mem"]["half_tp"]}
    def bind5(t):
        from replay import bind_strategy
        def wrapped(state, r, f, m, closes):
            if "half_tp" not in state["mem"]:
                sign = 1 if t["direction"] == "BUY" else -1
                state["mem"]["half_tp"] = t["entry_px"] + sign * 0.5 * t["tp_dist"]
                state["mem"]["entry"] = t["entry_px"]
            return n5_tp_decay(state, r, f, m, closes)
        return wrapped
    res5 = [replay(t, seqs[t["pid"]], bind5(t)) for t in trades]
    strat["N5_tp_decay_60m"] = {
        "all": agg([x["r"] for x in res5]),
        "BUY": agg([x["r"] for x, t in zip(res5, trades) if t["direction"] == "BUY"]),
        "SELL": agg([x["r"] for x, t in zip(res5, trades) if t["direction"] == "SELL"])}

    def n6_limit_entry(t, retr=0.33, window=30):      # −0.33R limit giriş
        seq = seqs[t["pid"]]
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        lim = e - sign * retr * t["sl_dist"]
        for i, (ts, b) in enumerate(seq[:window]):
            touched = (b["l"] <= lim) if sign > 0 else (b["h"] >= lim)
            if touched:
                t2 = {**t, "entry_px": lim,
                      "tp_px": lim + sign * t["tp_dist"], "sl_px": lim - sign * t["sl_dist"]}
                out2, _, _ = base_path(t2, seq[i + 1:])
                return (t["tp_dist"] / t["sl_dist"] if out2 == "tp"
                        else -1.0 if out2 == "sl" else 0.0)
        return 0.0                                    # dolmadı → sinyal atlandı
    strat["N6_limit_entry_033R"] = per_trade_new(n6_limit_entry)

    def n7_confirm_delay(t, wait=10, floor=-0.3):     # 10dk teyit gecikmesi
        seq = seqs[t["pid"]]
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        if len(seq) <= wait:
            return None
        # ilk 'wait' dakikada SL/TP vurulursa işlem zaten bizsiz bitti → atlandı
        out0, idx0, _ = base_path(t, seq[:wait])
        if out0 in ("sl", "tp"):
            return 0.0
        c = seq[wait - 1][1]["c"]
        if sign * (c - e) / t["sl_dist"] <= floor:
            return 0.0                                # teyit yok → atla
        t2 = {**t, "entry_px": c,
              "tp_px": c + sign * t["tp_dist"], "sl_px": c - sign * t["sl_dist"]}
        out2, _, _ = base_path(t2, seq[wait:])
        return (t["tp_dist"] / t["sl_dist"] if out2 == "tp"
                else -1.0 if out2 == "sl" else 0.0)
    strat["N7_confirm_delay_10m"] = per_trade_new(n7_confirm_delay)

    def n8_early_cut(state, r, f, m, closes):         # ilk 10dk'da −0.6R → çık
        if m <= 10 and r <= -0.6:
            return {"exit": True}
    from replay import bind_strategy as _bind
    res8 = [replay(t, seqs[t["pid"]], _bind("n8", n8_early_cut, t)) for t in trades]
    strat["N8_early_cut_10m"] = {
        "all": agg([x["r"] for x in res8]),
        "BUY": agg([x["r"] for x, t in zip(res8, trades) if t["direction"] == "BUY"]),
        "SELL": agg([x["r"] for x, t in zip(res8, trades) if t["direction"] == "SELL"])}

    def n9_slow_scratch(state, r, f, m, closes):      # 20dk'da +0.3R yoksa çık
        if m == 20 and max(closes, default=-9) < 0.3:
            return {"exit": True}
    res9 = [replay(t, seqs[t["pid"]], _bind("n9", n9_slow_scratch, t)) for t in trades]
    strat["N9_slow_scratch_20m"] = {
        "all": agg([x["r"] for x in res9]),
        "BUY": agg([x["r"] for x, t in zip(res9, trades) if t["direction"] == "BUY"]),
        "SELL": agg([x["r"] for x, t in zip(res9, trades) if t["direction"] == "SELL"])}

    def n10_v_recovery(state, r, f, m, closes):       # −0.5R dalışı sonrası girişte BE
        if r <= -0.5:
            state["mem"]["dipped"] = True
        if state["mem"].get("dipped") and r >= 0 and not state["mem"].get("be"):
            state["mem"]["be"] = True
            return {"sl": state["mem"]["entry"]}
    res10 = [replay(t, seqs[t["pid"]], _bind("n10", n10_v_recovery, t)) for t in trades]
    strat["N10_v_recovery_be"] = {
        "all": agg([x["r"] for x in res10]),
        "BUY": agg([x["r"] for x, t in zip(res10, trades) if t["direction"] == "BUY"]),
        "SELL": agg([x["r"] for x, t in zip(res10, trades) if t["direction"] == "SELL"])}

    # baseline referans
    base_all = run_strategy(trades, seqs, None)
    strat["baseline"] = {
        "all": agg([x["r"] for x in base_all]),
        "BUY": agg([x["r"] for x in base_all if x["direction"] == "BUY"]),
        "SELL": agg([x["r"] for x in base_all if x["direction"] == "SELL"])}

    report["strategies"] = strat
    json.dump(report, open(HERE / "results_stage3.json", "w"), indent=1)

    print("═══ TEŞHİSLER ═══")
    for k in ("D1_dip_timing", "D2_post_sl", "D3_post_tp", "D4_fast_start",
              "D5_be30_buy_hourly_delta"):
        print(k, json.dumps(report[k]))
    print("\n═══ STRATEJİLER (tot_r: all | BUY | SELL) ═══")
    for name, s in strat.items():
        print(f"{name:<26} all={s['all']['tot_r']:>8} (WR {s['all']['wr']}%)"
              f"  BUY={s['BUY']['tot_r']:>8}  SELL={s['SELL']['tot_r']:>8}")


if __name__ == "__main__":
    main()
