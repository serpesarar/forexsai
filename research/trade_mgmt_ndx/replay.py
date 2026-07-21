"""NDX işlem-yönetimi replay motoru — 10 strateji + fenomen analizi.

DÜRÜSTLÜK SÖZLEŞMESİ:
  * Kararlar yalnız BAR KAPANIŞINDA alınır; SL/TP değişikliği SONRAKİ bardan
    itibaren geçerlidir (bar-içi geleceği görme yok).
  * Giriş dakikasının kalan kısmı bilinmediğinden değerlendirme entry
    barının BİR SONRAKİ barından başlar.
  * Aynı 1m barda hem TP hem SL menzildeyse KONSERVATİF: SL-önce sayılır
    (hem baseline hem stratejilerde aynı kural — adil karşılaştırma).
  * Zaman kuralları PİYASA dakikası sayar (1 bar = 1 dk; kapalı saatler
    akmaz) — MT5'te de piyasa kapaliyken fiyat akmaz.
  * SL'i mevcut fiyatın "yanlış" tarafına taşıyacak kural tetiklenirse
    (broker reddi durumu) MARKET ÇIKIŞ uygulanır (bar kapanışından) —
    kural askıya alınıp beklenmez (bekleme = hindsight seçilimi olur).

Sonuç metrikleri ORİJİNAL riske göre R (|entry−SL0| = 1R) + puan/lot.
"""
from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAX_BARS = 3 * 1440          # emniyet: 3 gün piyasa dakikası


def load() -> tuple[list[dict], dict[int, dict], list[int]]:
    trades = [t for t in json.load(open(HERE / "trades.json")) if t.get("geometry_ok")]
    bars: dict[int, dict] = {}
    with open(HERE / "bars_1m.csv") as f:
        for r in csv.DictReader(f):
            bars[int(r["ts"])] = {"o": float(r["open"]), "h": float(r["high"]),
                                  "l": float(r["low"]), "c": float(r["close"])}
    return trades, bars, sorted(bars)


def parse_ts(text: str) -> int:
    t = text.strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    dt = datetime.fromisoformat(t)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def trade_bars(t: dict, bars: dict[int, dict], keys: list[int]) -> list[tuple[int, dict]]:
    """Entry barından SONRAKİ barlar (kronolojik)."""
    entry_bar = (parse_ts(t["entry_time"]) // 60) * 60
    import bisect
    i = bisect.bisect_right(keys, entry_bar)
    return [(k, bars[k]) for k in keys[i:i + MAX_BARS]]


# ─── Çekirdek replay ─────────────────────────────────────────────────────────

def replay(t: dict, seq: list[tuple[int, dict]], strategy) -> dict:
    """strategy(state, bar_close_r, bar_close_f, minutes, closes_r) → aksiyonlar.

    state: dict(sl, tp) fiyat cinsinden; strategy her bar kapanışında çağrılır,
    {"sl": yeni_sl} / {"tp": yeni_tp} / {"exit": True} dönebilir (None = dokunma).
    """
    e = t["entry_px"]
    sign = 1 if t["direction"] == "BUY" else -1
    sl_d, tp_d = t["sl_dist"], t["tp_dist"]
    state = {"sl": t["sl_px"], "tp": t["tp_px"], "mem": {}}
    closes_r: list[float] = []

    for minutes, (ts, b) in enumerate(seq, start=1):
        # 1) mevcut seviyelerle çıkış kontrolü (SL-önce konservatif)
        if sign > 0:
            hit_sl = b["l"] <= state["sl"]
            hit_tp = b["h"] >= state["tp"]
        else:
            hit_sl = b["h"] >= state["sl"]
            hit_tp = b["l"] <= state["tp"]
        if hit_sl:
            px = state["sl"]
            return {"outcome": "sl", "exit_px": px, "minutes": minutes,
                    "r": sign * (px - e) / sl_d}
        if hit_tp:
            px = state["tp"]
            return {"outcome": "tp", "exit_px": px, "minutes": minutes,
                    "r": sign * (px - e) / sl_d}
        # 2) bar kapanışı → strateji kararı (bir SONRAKİ bardan geçerli)
        r = sign * (b["c"] - e) / sl_d
        f = sign * (b["c"] - e) / tp_d
        closes_r.append(r)
        act = strategy(state, r, f, minutes, closes_r) if strategy else None
        if act:
            if act.get("exit"):
                return {"outcome": "mgmt_exit", "exit_px": b["c"], "minutes": minutes,
                        "r": r}
            if "sl" in act:
                new_sl = act["sl"]
                # broker geçerliliği: SL fiyatın doğru tarafında olmalı
                if sign * (b["c"] - new_sl) <= 0:
                    return {"outcome": "mgmt_exit", "exit_px": b["c"],
                            "minutes": minutes, "r": r}
                # SL yalnız LEHTE hareket eder (gevşetme yok)
                if sign * (new_sl - state["sl"]) > 0:
                    state["sl"] = new_sl
            if "tp" in act:
                new_tp = act["tp"]
                if sign * (new_tp - b["c"]) <= 0:
                    return {"outcome": "mgmt_exit", "exit_px": b["c"],
                            "minutes": minutes, "r": r}
                # TP yalnız YAKINA çekilir (uzatma yok)
                if sign * (state["tp"] - new_tp) > 0:
                    state["tp"] = new_tp
    last_r = closes_r[-1] if closes_r else 0.0
    return {"outcome": "unresolved", "exit_px": None, "minutes": len(seq), "r": last_r}


# ─── Fenomen analizi (baseline yol istatistikleri) ───────────────────────────

def path_stats(t: dict, seq: list[tuple[int, dict]]) -> dict | None:
    """Orijinal SL/TP ile yol: MFE/MAE, SL-yarısı dwell, yaklaşıp-dönme."""
    e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
    sl_d, tp_d = t["sl_dist"], t["tp_dist"]
    sl_px, tp_px = t["sl_px"], t["tp_px"]
    max_f = 0.0          # TP mesafesinin en fazla yüzde kaçına yaklaştı (close bazlı)
    min_r = 0.0          # en derin zarar (R)
    dwell_half = 0       # SL-yarısında (r ≤ −0.5) ardışık dk — maksimum koşu
    run = 0
    dwell_before_outcome = 0
    outcome = None
    minutes = 0
    reach_time_07 = None
    for minutes, (ts, b) in enumerate(seq, start=1):
        if sign > 0:
            hit_sl, hit_tp = b["l"] <= sl_px, b["h"] >= tp_px
        else:
            hit_sl, hit_tp = b["h"] >= sl_px, b["l"] <= tp_px
        if hit_sl:                      # konservatif: SL-önce
            outcome = "sl"
            break
        if hit_tp:
            outcome = "tp"
            break
        r = sign * (b["c"] - e) / sl_d
        f = sign * (b["c"] - e) / tp_d
        max_f = max(max_f, f)
        min_r = min(min_r, r)
        if f >= 0.7 and reach_time_07 is None:
            reach_time_07 = minutes
        if r <= -0.5:
            run += 1
            dwell_half = max(dwell_half, run)
        else:
            run = 0
    if outcome is None:
        return None
    return {"outcome": outcome, "minutes": minutes, "max_f": round(max_f, 3),
            "min_r": round(min_r, 3), "dwell_half_max": dwell_half,
            "reach07_min": reach_time_07, "direction": t["direction"],
            "cohort": t["cohort"]}


# ─── 10 strateji ─────────────────────────────────────────────────────────────

def make_strategies() -> dict:
    S = {}

    def s1(state, r, f, m, closes):                 # BE @ %50 TP yolu
        if f >= 0.5 and not state["mem"].get("be"):
            state["mem"]["be"] = True
            return {"sl": state["mem"]["entry"]}
    S["S1_be_at_halfTP"] = s1

    def s2(state, r, f, m, closes):                 # BE @ 30 piyasa-dk
        if m >= 30 and not state["mem"].get("be"):
            state["mem"]["be"] = True
            return {"sl": state["mem"]["entry"]}
    S["S2_be_after_30m"] = s2

    def s3(state, r, f, m, closes):                 # SL yarıya @ 30 dk
        if m >= 30 and not state["mem"].get("hv"):
            state["mem"]["hv"] = True
            return {"sl": state["mem"]["half_sl"]}
    S["S3_halveSL_after_30m"] = s3

    def s4(state, r, f, m, closes):                 # 10dk SL-yarısı → TP=entry
        if state["mem"].get("scr"):
            return None
        if len(closes) >= 10 and all(x <= -0.5 for x in closes[-10:]):
            state["mem"]["scr"] = True
            return {"tp": state["mem"]["entry"]}
    S["S4_scratchTP_dwell10"] = s4

    def s5(state, r, f, m, closes):                 # 10dk SL-yarısı → market çık
        if len(closes) >= 10 and all(x <= -0.5 for x in closes[-10:]):
            return {"exit": True}
    S["S5_cut_dwell10"] = s5

    def s6(state, r, f, m, closes):                 # %70 TP → yarısını kilitle
        if f >= 0.7 and not state["mem"].get("lock"):
            state["mem"]["lock"] = True
            return {"sl": state["mem"]["lock_px"]}
    S["S6_lock_at_07TP"] = s6

    def s7(state, r, f, m, closes):                 # %70'e ulaştı, 15dk'da TP yok → çık
        if f >= 0.7 and "t07" not in state["mem"]:
            state["mem"]["t07"] = m
        if "t07" in state["mem"] and m - state["mem"]["t07"] >= 15:
            return {"exit": True}
    S["S7_stallExit_07TP_15m"] = s7

    def s8(state, r, f, m, closes):                 # %50 sonrası iz süren SL
        if f >= 0.5:
            state["mem"]["trail_on"] = True
        if state["mem"].get("trail_on"):
            return {"sl": state["mem"]["trail_fn"](closes[-1])}
    S["S8_trail_after_halfTP"] = s8

    def s9(state, r, f, m, closes):                 # 120 dk zaman-stopu
        if m >= 120:
            return {"exit": True}
    S["S9_timestop_120m"] = s9

    def s10(state, r, f, m, closes):                # kombo: S1 + S5 + S6
        if len(closes) >= 10 and all(x <= -0.5 for x in closes[-10:]):
            return {"exit": True}
        if f >= 0.7 and not state["mem"].get("lock"):
            state["mem"]["lock"] = True
            return {"sl": state["mem"]["lock_px"]}
        if f >= 0.5 and not state["mem"].get("be"):
            state["mem"]["be"] = True
            return {"sl": state["mem"]["entry"]}
    S["S10_combo_S1S5S6"] = s10

    return S


def bind_strategy(name: str, fn, t: dict):
    """Stratejiye işlem geometrisini enjekte et (closure)."""
    e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)

    def wrapped(state, r, f, m, closes):
        mem = state["mem"]
        if "entry" not in mem:
            mem["entry"] = e
            mem["half_sl"] = e - sign * 0.5 * t["sl_dist"]
            mem["lock_px"] = e + sign * 0.35 * t["tp_dist"]
            mem["trail_fn"] = lambda last_r: e + sign * (last_r * t["sl_dist"] - 0.6 * t["sl_dist"])
        return fn(state, r, f, m, closes)
    return wrapped


# ─── Koşum + rapor ───────────────────────────────────────────────────────────

def aggregate(results: list[dict]) -> dict:
    n = len(results)
    wins = [x for x in results if x["r"] > 0.02]
    losses = [x for x in results if x["r"] < -0.02]
    scratch = n - len(wins) - len(losses)
    rs = [x["r"] for x in results]
    return {
        "n": n, "win": len(wins), "loss": len(losses), "scratch": scratch,
        "win_rate_pct": round(100 * len(wins) / max(1, len(wins) + len(losses)), 1),
        "avg_r": round(statistics.mean(rs), 4) if rs else None,
        "total_r": round(sum(rs), 2),
        "median_min": statistics.median([x["minutes"] for x in results]) if results else None,
        "full_sl_count": sum(1 for x in results if x["r"] <= -0.98),
    }


def main() -> None:
    trades, bars, keys = load()
    seqs = {t["pid"]: trade_bars(t, bars, keys) for t in trades}
    trades = [t for t in trades if len(seqs[t["pid"]]) >= 5]
    print(f"replay edilebilir işlem: {len(trades)}")

    # 1) Kalibrasyon + fenomenler
    phen = []
    agree = 0
    baseline_results = []
    for t in trades:
        ps = path_stats(t, seqs[t["pid"]])
        base = replay(t, seqs[t["pid"]], None)
        baseline_results.append({**base, "pid": t["pid"]})
        if ps:
            phen.append(ps)
            if ps["outcome"] == t["close_reason"]:
                agree += 1
    resolved_phen = len(phen)
    print(f"kalibrasyon: replay-vs-gerçek uyum {agree}/{resolved_phen} "
          f"(%{100*agree/max(1,resolved_phen):.1f})")

    # fenomen özetleri
    sl_trades = [p for p in phen if p["outcome"] == "sl"]
    tp_trades = [p for p in phen if p["outcome"] == "tp"]
    near_then_sl = [p for p in sl_trades if p["max_f"] >= 0.7]
    half_then_sl = [p for p in sl_trades if p["max_f"] >= 0.5]
    dwell10_all = [p for p in phen if p["dwell_half_max"] >= 10]
    dwell10_tp = [p for p in dwell10_all if p["outcome"] == "tp"]
    phenomena = {
        "resolved": resolved_phen,
        "tp": len(tp_trades), "sl": len(sl_trades),
        "sl_after_reaching_70pct_tp": len(near_then_sl),
        "sl_after_reaching_50pct_tp": len(half_then_sl),
        "p_win_given_reach_70pct": round(
            100 * sum(1 for p in phen if p["max_f"] >= 0.7 and p["outcome"] == "tp")
            / max(1, sum(1 for p in phen if p["max_f"] >= 0.7)), 1),
        "p_win_given_reach_50pct": round(
            100 * sum(1 for p in phen if p["max_f"] >= 0.5 and p["outcome"] == "tp")
            / max(1, sum(1 for p in phen if p["max_f"] >= 0.5)), 1),
        "dwell10_in_sl_half_count": len(dwell10_all),
        "dwell10_recovered_to_tp": len(dwell10_tp),
        "p_win_given_dwell10": round(100 * len(dwell10_tp) / max(1, len(dwell10_all)), 1),
        "winners_that_dipped_sl_half": sum(1 for p in tp_trades if p["min_r"] <= -0.5),
        "median_minutes_tp": statistics.median([p["minutes"] for p in tp_trades]) if tp_trades else None,
        "median_minutes_sl": statistics.median([p["minutes"] for p in sl_trades]) if sl_trades else None,
    }
    print(json.dumps(phenomena, indent=1))

    # 2) Stratejiler
    out = {"baseline": aggregate(baseline_results)}
    per_trade = {"baseline": baseline_results}
    for name, fn in make_strategies().items():
        results = []
        for t in trades:
            bound = bind_strategy(name, fn, t)
            res = replay(t, seqs[t["pid"]], bound)
            results.append({**res, "pid": t["pid"], "cohort": t["cohort"],
                            "direction": t["direction"]})
        out[name] = aggregate(results)
        per_trade[name] = results
        # kohort kırılımı
        for c in ("A", "B"):
            sub = [x for x in results if x.get("cohort") == c]
            if sub:
                out[name][f"cohort_{c}"] = {"n": len(sub),
                                            "avg_r": round(statistics.mean([x["r"] for x in sub]), 4),
                                            "total_r": round(sum(x["r"] for x in sub), 2)}

    json.dump({"phenomena": phenomena, "strategies": out},
              open(HERE / "results.json", "w"), indent=1)
    json.dump(per_trade, open(HERE / "per_trade.json", "w"), indent=1)

    print(f"\n{'strateji':<28}{'n':>5}{'WR%':>7}{'avgR':>9}{'totR':>8}{'tamSL':>7}")
    for name, a in out.items():
        print(f"{name:<28}{a['n']:>5}{a['win_rate_pct']:>7}{a['avg_r']:>9}"
              f"{a['total_r']:>8}{a['full_sl_count']:>7}")


if __name__ == "__main__":
    main()
