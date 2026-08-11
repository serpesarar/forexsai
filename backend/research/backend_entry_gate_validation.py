"""BACKEND giriş skoru kapısı (services/signal_gates.entry_score_gate) — sızıntısız ölçüm.

Soru: bu kapı panel sinyallerini (pulse1/2/3 + smc, NDX+USOIL) GERÇEKTEN bloklıyor;
elediği küme kârlı mıydı zararlı mıydı? (Bot tarafındaki aynı mantık 2026-08-11'de
sızıntısız ölçümde ZARARLI çıktı → aynı şüphe backend için de geçerli.)

Yöntem:
  · Sinyaller: prediction_logs (Supabase) — symbol∈{NDX,USOIL}, model∈{pulse1,2,3,smc}.
  · Skor: backend'in KENDİ compute_entry_score'u, karar anında KAPANMIŞ M5/M30
    barlarıyla (MT5). Bar kesimi _bars_upto mantığı — geleceğe bakış yok.
  · Sonuç: satırın kendi entry/tp1/sl'iyle M1 yarışı (aynı barda ikisi de → KAYIP).
    prediction_logs.status KULLANILMAZ (geçmişte iki yönlü bozuk çözümleme kanıtlandı).
  · SANSÜR: kapı 2026-07-15'te (commit f080e5d) canlıya girdi; o tarihten SONRA
    bloklanan sinyaller DB'ye hiç yazılmadı → tarafsız pencere ÖNCESİDİR.
    Sonraki dönem yalnız "kapı gerçekten çalışıyor mu + skor yeniden üretimim
    doğru mu" öz-denetimi için kullanılır (skor<7 satırı kalmamalı).

Çalıştırma (kutuda): python backend/research/backend_entry_gate_validation.py [gün]
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import MetaTrader5 as mt5  # noqa: E402

from services.signal_gates import compute_entry_score  # noqa: E402

CACHE = Path(__file__).resolve().parent / "_usoil_cache"
GATE_LIVE = datetime(2026, 7, 15, tzinfo=timezone.utc)     # commit f080e5d
SYMBOLS = {"NDX.INDX": "NAS100", "USOIL.FOREX": "SpotCrude"}
MODELS = ("pulse1", "pulse2", "pulse3", "smc")
SERVER_OFFSET_H = 3
MIN_SCORE = 7
MAX_HOLD_MIN = 24 * 60
RNG = np.random.default_rng(23)


# ── Supabase ────────────────────────────────────────────────────────────────

def _creds() -> tuple[str, str]:
    txt = (ROOT / "yeni deneme" / "config.py").read_text(encoding="utf-8", errors="replace")
    url = re.search(r'SUPABASE_URL\s*=\s*["\']([^"\']+)["\']', txt).group(1)
    key = re.search(r'SUPABASE_SERVICE_KEY\s*=\s*["\']([^"\']+)["\']', txt).group(1)
    return url, key


def fetch_signals(since: datetime) -> list[dict]:
    url, key = _creds()
    h = {"apikey": key, "Authorization": f"Bearer {key}"}
    rows, page = [], 0
    while True:
        r = requests.get(
            f"{url}/rest/v1/prediction_logs", headers=h, timeout=120,
            params={"symbol": f"in.({','.join(SYMBOLS)})",
                    "model_type": f"in.({','.join(MODELS)})",
                    "created_at": f"gte.{since.isoformat()}",
                    "select": "id,symbol,model_type,ml_direction,ml_entry_price,"
                              "ml_stop_price,targets,stop_loss_pips,status,created_at",
                    "order": "created_at.asc", "offset": page * 1000, "limit": 1000})
        r.raise_for_status()
        b = r.json()
        rows += b
        print(f"  sinyal indirildi: {len(rows)}", end="\r", flush=True)
        if len(b) < 1000:
            break
        page += 1
    print(f"  sinyal indirildi: {len(rows)}      ")
    return rows


# ── MT5 barları ─────────────────────────────────────────────────────────────

def fetch_bars(sym: str, tf_name: str, days: int) -> np.ndarray:
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{sym}_{tf_name}_{days}.npy"
    if f.exists():
        return np.load(f)
    tf = {"M5": mt5.TIMEFRAME_M5, "M1": mt5.TIMEFRAME_M1}[tf_name]
    end = datetime.now() + timedelta(days=1)
    chunks = []
    for k in range(days // 20 + 1):
        b = end - timedelta(days=20 * k)
        r = mt5.copy_rates_range(sym, tf, b - timedelta(days=20), b)
        if r is not None and len(r):
            chunks.append(np.array([(int(x["time"]), float(x["open"]), float(x["high"]),
                                     float(x["low"]), float(x["close"]),
                                     float(x["tick_volume"])) for x in r]))
    if not chunks:
        raise SystemExit(f"{sym} {tf_name} verisi yok")
    arr = np.vstack(chunks)
    arr = arr[np.argsort(arr[:, 0])]
    _, u = np.unique(arr[:, 0], return_index=True)
    arr = arr[np.sort(u)]
    np.save(f, arr)
    return arr


def to_m30(m5: np.ndarray) -> np.ndarray:
    """M5 → M30 (backend'in 30m'i de türetilmiş; aynı mantık)."""
    b = (m5[:, 0] // 1800).astype(np.int64)
    out, i = [], 0
    while i < len(b):
        j = i
        while j < len(b) and b[j] == b[i]:
            j += 1
        s = m5[i:j]
        out.append((b[i] * 1800, s[0, 1], s[:, 2].max(), s[:, 3].min(), s[-1, 4], s[:, 5].sum()))
        i = j
    return np.array(out)


def candles(arr: np.ndarray, ts: float, n: int, per_s: int) -> list[dict] | None:
    """ts (sunucu-epoch) anında KAPANMIŞ son n bar."""
    k = int(np.searchsorted(arr[:, 0], ts - per_s, side="right"))
    if k < 30:
        return None
    s = arr[max(0, k - n):k]
    return [{"high": r[2], "low": r[3], "close": r[4], "volume": r[5]} for r in s]


def wilder_atr(c: list[dict], period: int = 14) -> float | None:
    """Backend'in _wilder_atr'ıyla aynı — nötr geometri için."""
    if not c or len(c) < period + 1:
        return None
    atr, trs, pc = None, [], None
    for x in c:
        h, l, cl = x["high"], x["low"], x["close"]
        tr = h - l if pc is None else max(h - l, abs(h - pc), abs(l - pc))
        pc = cl
        if atr is None:
            trs.append(tr)
            if len(trs) == period:
                atr = sum(trs) / period
        else:
            atr = (atr * (period - 1) + tr) / period
    return atr


def resolve(m1: np.ndarray, ts: float, direction: str, entry: float,
            tp: float, sl: float) -> tuple[int, int] | None:
    """(kazandı, dakika) — aynı barda TP+SL → KAYIP (konservatif)."""
    k = int(np.searchsorted(m1[:, 0], ts))
    if k >= len(m1) - 2 or m1[k, 0] - ts > 900:
        return None
    hi, lo = m1[k:k + MAX_HOLD_MIN, 2], m1[k:k + MAX_HOLD_MIN, 3]
    if direction == "BUY":
        tp_hits, sl_hits = hi >= tp, lo <= sl
    else:
        tp_hits, sl_hits = lo <= tp, hi >= sl
    t_i = int(np.argmax(tp_hits)) if tp_hits.any() else 10 ** 9
    s_i = int(np.argmax(sl_hits)) if sl_hits.any() else 10 ** 9
    if t_i == s_i == 10 ** 9:
        return None
    return (1, t_i + 1) if t_i < s_i else (0, s_i + 1)


# ── raporlama ───────────────────────────────────────────────────────────────

def rep(name: str, sel: list[dict]) -> None:
    if not sel:
        print(f"  {name:<38} n=    0")
        return
    n = len(sel)
    w = sum(r["win"] for r in sel)
    R = sum(r["R"] for r in sel)
    b = [r for r in sel if "RB" in r]
    bt = (f" | dönem-geo: n={len(b):>5} WR={100*sum(r['winB'] for r in b)/len(b):5.1f}% "
          f"topR={sum(r['RB'] for r in b):+8.1f}") if b else ""
    print(f"  {name:<38} n={n:>5}  WR={100*w/n:5.1f}%  ortR={R/n:+.3f}  topR={R:+8.1f}{bt}")


def day_block_boot(a: list[dict], b: list[dict], n=3000) -> float:
    """Günlük blok bootstrap: P(elenen kümenin ort.R'si > geçenlerinki).
    Sinyaller gün içinde korelasyonlu → gün bloğu dürüst aralık verir."""
    days = sorted({r["gun"] for r in a + b})
    if len(days) < 10:
        return float("nan")
    by = defaultdict(lambda: ([], []))
    for r in a:
        by[r["gun"]][0].append(r["R"])
    for r in b:
        by[r["gun"]][1].append(r["R"])
    wins = 0
    for _ in range(n):
        pick = RNG.choice(days, size=len(days), replace=True)
        xa = [v for d in pick for v in by[d][0]]
        xb = [v for d in pick for v in by[d][1]]
        if xa and xb and np.mean(xb) > np.mean(xa):
            wins += 1
    return wins / n


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    if not mt5.initialize():
        raise SystemExit(f"mt5.initialize() hata: {mt5.last_error()}")
    since = datetime.now(timezone.utc) - timedelta(days=days)
    print(f"pencere: {since:%Y-%m-%d} → bugün  (kapı canlıya girişi: {GATE_LIVE:%Y-%m-%d})")
    sig = fetch_signals(since)

    bars = {}
    for fx, mt in SYMBOLS.items():
        m5 = fetch_bars(mt, "M5", days + 20)
        bars[fx] = {"m5": m5, "m30": to_m30(m5), "m1": fetch_bars(mt, "M1", days + 20)}
        print(f"  {fx}: M5={len(m5)} M30={len(bars[fx]['m30'])} M1={len(bars[fx]['m1'])}")

    rows, atlanan = [], defaultdict(int)
    for s in sig:
        dirn = s.get("ml_direction")
        if dirn not in ("BUY", "SELL"):
            atlanan["yon_yok"] += 1; continue
        try:
            entry = float(s["ml_entry_price"])
        except (TypeError, ValueError):
            atlanan["giris_yok"] += 1; continue
        if entry <= 0:
            atlanan["giris_bozuk"] += 1; continue
        created = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
        ts = created.timestamp() + SERVER_OFFSET_H * 3600         # sunucu ekseni
        d = bars[s["symbol"]]
        c5 = candles(d["m5"], ts, 260, 300)
        c30 = candles(d["m30"], ts, 60, 1800)
        if c5 is None or c30 is None:
            atlanan["bar_yok"] += 1; continue
        score, fails = compute_entry_score(s["symbol"], dirn, c5, c30, now=created)

        # A) NÖTR geometri: TP=SL=1×ATR(5m) → saf yön kalitesi (dönem geometrisinden
        #    bağımsız; pulse geometrisi bu dönemde bilinen şekilde bozuktu).
        atr5 = wilder_atr(c5)
        rec = None
        if atr5 and atr5 > 0:
            tp_a = entry + atr5 if dirn == "BUY" else entry - atr5
            sl_a = entry - atr5 if dirn == "BUY" else entry + atr5
            res_a = resolve(d["m1"], ts, dirn, entry, tp_a, sl_a)
            if res_a:
                rec = dict(sym=s["symbol"], model=s["model_type"], dirn=dirn,
                           created=created, gun=created.date().isoformat(),
                           score=score, fails=fails,
                           win=res_a[0], mins=res_a[1],
                           R=1.0 if res_a[0] else -1.0, rr=1.0,
                           once=created < GATE_LIVE)
        if rec is None:
            atlanan["cozulmedi_notr"] += 1; continue

        # B) DÖNEM geometrisi: TP1 = targets.TP1, SL mesafesi = stop_loss_pips
        tgt = s.get("targets") or {}
        try:
            tp_b = float(tgt.get("TP1"))
            sld = abs(float(s.get("stop_loss_pips")))
        except (TypeError, ValueError):
            tp_b, sld = None, None
        if tp_b and sld and sld > 0:
            sl_b = entry - sld if dirn == "BUY" else entry + sld
            res_b = resolve(d["m1"], ts, dirn, entry, tp_b, sl_b)
            if res_b:
                rr_b = abs(tp_b - entry) / sld
                rec["winB"] = res_b[0]
                rec["RB"] = rr_b if res_b[0] else -1.0
        rows.append(rec)
    print(f"\nçözülen sinyal: {len(rows)}   atlanan: {dict(atlanan)}\n")

    onc = [r for r in rows if r["once"]]
    son = [r for r in rows if not r["once"]]

    print("=" * 78)
    print(f"[A] SANSÜRSÜZ PENCERE (kapı canlıya girmeden önce, {GATE_LIVE:%Y-%m-%d} öncesi)")
    print("=" * 78)
    rep("TÜMÜ (kapı yokken gerçekleşen)", onc)
    gec = [r for r in onc if r["score"] >= MIN_SCORE]
    blk = [r for r in onc if r["score"] < MIN_SCORE]
    rep(f"kapıdan GEÇECEK (skor≥{MIN_SCORE})", gec)
    rep(f"kapının ELEYECEĞİ (skor<{MIN_SCORE})", blk)
    if gec and blk:
        p = day_block_boot(gec, blk)
        print(f"\n  → kapı haklı mı? elenen kümenin ort.R'si geçenlerden DÜŞÜK olmalı.")
        print(f"     elenen {np.mean([r['R'] for r in blk]):+.3f} vs geçen "
              f"{np.mean([r['R'] for r in gec]):+.3f}   "
              f"P(elenen > geçen | gün-bloklu bootstrap) = %{100*p:.1f}")

    print("\n  eşik duyarlılığı (sansürsüz pencere):")
    for thr in (5, 6, 7, 8):
        k = [r for r in onc if r["score"] >= thr]
        d_ = [r for r in onc if r["score"] < thr]
        print(f"    eşik≥{thr}: kalan n={len(k):>5} ortR={np.mean([r['R'] for r in k]) if k else 0:+.3f}"
              f" topR={sum(r['R'] for r in k):+8.1f} | elenen n={len(d_):>5} "
              f"topR={sum(r['R'] for r in d_):+8.1f}")

    print("\n  sembol × model kırılımı (elenen küme):")
    for sym in SYMBOLS:
        for m in MODELS:
            sel = [r for r in onc if r["sym"] == sym and r["model"] == m]
            if len(sel) < 20:
                continue
            b_ = [r for r in sel if r["score"] < MIN_SCORE]
            print(f"    {sym:<12}{m:<8} tümü n={len(sel):>4} ortR="
                  f"{np.mean([r['R'] for r in sel]):+.3f} | elenen n={len(b_):>4} "
                  f"ortR={np.mean([r['R'] for r in b_]) if b_ else 0:+.3f}")

    print("\n  en sık ihlal (elenenler):")
    cnt = defaultdict(int)
    for r in blk:
        for f in r["fails"]:
            cnt[f] += 1
    for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
        print(f"    {k:<20} {v}")

    print("\n" + "=" * 78)
    print("[B] ÖZ-DENETİM — kapı canlıya girdikten sonra (sansürlü; skor<7 KALMAMALI)")
    print("=" * 78)
    rep("TÜMÜ", son)
    rep(f"skor≥{MIN_SCORE}", [r for r in son if r["score"] >= MIN_SCORE])
    rep(f"skor<{MIN_SCORE} (sızmış olanlar)", [r for r in son if r["score"] < MIN_SCORE])
    if son:
        pay = 100 * sum(1 for r in son if r["score"] < MIN_SCORE) / len(son)
        onc_pay = 100 * len(blk) / len(onc) if onc else 0
        print(f"\n  skor<{MIN_SCORE} oranı: kapı öncesi %{onc_pay:.1f} → kapı sonrası %{pay:.1f}")
        print("  (belirgin düşüş = kapı gerçekten çalışıyor VE skor yeniden üretimim doğru)")
        print("\n  sızma kırılımı (kapı sonrası skor<7 satırları — kapı neden yakalamadı?):")
        for m in MODELS:
            sel = [r for r in son if r["model"] == m]
            if not sel:
                continue
            s7 = [r for r in sel if r["score"] < MIN_SCORE]
            print(f"    {m:<8} n={len(sel):>5}  skor<7: {len(s7):>4} (%{100*len(s7)/len(sel):.1f})")
        for sym in SYMBOLS:
            sel = [r for r in son if r["sym"] == sym]
            if not sel:
                continue
            s7 = [r for r in sel if r["score"] < MIN_SCORE]
            print(f"    {sym:<12} n={len(sel):>5}  skor<7: {len(s7):>4} (%{100*len(s7)/len(sel):.1f})")
        cnt2 = defaultdict(int)
        for r in son:
            if r["score"] < MIN_SCORE:
                for f in r["fails"]:
                    cnt2[f] += 1
        print("    sızanların ihlalleri:", dict(sorted(cnt2.items(), key=lambda x: -x[1])))
    print("\nBITTI")


if __name__ == "__main__":
    main()
