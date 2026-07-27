"""gate_audit.py — "Filtre çok mu sıkı?" sorusunu VERİYLE cevaplar.

Bot her kapı-elemesini `yeni deneme/gate_skipped.jsonl`'e yazar (karar anındaki
fiyat + geometri). Bu script o kayıtları 1m barlarla SIZINTISIZ replay eder:
elenen sinyal açılsaydı TP mi SL mi olurdu?

Karar kuralı (ön-kayıtlı):
  * Elenenler −EV → kapı HAKLI, dokunma.
  * Elenenler +EV ve n≥20 → kapı fazla sıkı, gevşetme adayı.
  * n<20 → "veri birikiyor", karar YOK (küçük örnekle gevşetme yapılmaz).

Kullanım:
  python3 research/gate_audit.py                 # tüm kapılar
  python3 research/gate_audit.py --reason trend_gate
  python3 research/gate_audit.py --days 14
"""
from __future__ import annotations

import argparse
import bisect
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

SKIP_FILES = [ROOT / "yeni deneme" / "gate_skipped.jsonl"]
# Sembol bazlı varsayılan geometri (kayıtta tp/sl yoksa — bot sabitleri)
DEFAULT_GEOM = {
    "NDX.INDX": (80.0, 110.0), "GDAXI.INDX": (67.0, 119.0),
    "USOIL.FOREX": (None, None),          # yüzde bazlı, fiyattan hesaplanır
    "XAUUSD": (8.0, 6.0),
}
PCT_GEOM = {"USOIL.FOREX": (1.04, 1.49)}
MIN_N_FOR_DECISION = 20


def parse_ts(t: str) -> datetime:
    t = t.replace("Z", "+00:00")
    dt = datetime.fromisoformat(t)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_skips(days: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for path in SKIP_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if parse_ts(rec["ts"]) >= since:
                    out.append(rec)
            except Exception:
                continue
    return out


def fetch_bars(symbol: str, since: datetime) -> list[dict]:
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase erişilemedi")
    bars, cursor = [], since.isoformat()
    while True:
        res = (client.table("candle_cache").select("candle_time,high,low,close")
               .eq("symbol", symbol).eq("timeframe", "1m")
               .gte("candle_time", cursor).order("candle_time").limit(1000).execute())
        if res.get("error"):
            raise RuntimeError(res["error"])
        chunk = res.get("data") or []
        if not chunk:
            break
        for r in chunk:
            dt = parse_ts(r["candle_time"])
            if dt.second != 0:                 # tick-kirlilik koruması
                continue
            bars.append({"ts": int(dt.timestamp()), "h": float(r["high"]),
                         "l": float(r["low"]), "c": float(r["close"])})
        cursor = (parse_ts(chunk[-1]["candle_time"]) + timedelta(seconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    return bars


def geometry(rec: dict) -> tuple[float, float] | None:
    tp, sl = rec.get("tp_dist"), rec.get("sl_dist")
    if tp and sl:
        return float(tp), float(sl)
    sym, px = rec["symbol"], float(rec["price"])
    if sym in PCT_GEOM:
        t, s = PCT_GEOM[sym]
        return px * t / 100.0, px * s / 100.0
    t, s = DEFAULT_GEOM.get(sym, (None, None))
    return (t, s) if t and s else None


def make_runner(bars: list[dict]):
    keys = [b["ts"] for b in bars]
    bymap = {b["ts"]: b for b in bars}

    def run(rec: dict, max_bars: int = 2880):
        geom = geometry(rec)
        if not geom:
            return None
        tp_d, sl_d = geom
        px = float(rec["price"])
        sign = 1 if rec["direction"] == "BUY" else -1
        tp, sl = px + sign * tp_d, px - sign * sl_d
        t0 = int(parse_ts(rec["ts"]).timestamp())
        i = bisect.bisect_right(keys, (t0 // 60) * 60)
        for k in keys[i:i + max_bars]:
            b = bymap[k]
            hit_sl = (b["l"] <= sl) if sign > 0 else (b["h"] >= sl)
            hit_tp = (b["h"] >= tp) if sign > 0 else (b["l"] <= tp)
            if hit_sl:                       # aynı barda ikisi de → konservatif SL
                return -1.0
            if hit_tp:
                return tp_d / sl_d
        return 0.0                           # çözülmedi
    return run


def summarize(rs: list[float]) -> str:
    res = [r for r in rs if r != 0.0]
    w = sum(1 for r in res if r > 0)
    l = len(res) - w
    if not res:
        return f"n={len(rs)} (hiçbiri çözülmedi)"
    return (f"n={len(rs)} çözülen={len(res)} W={w} L={l} "
            f"WR=%{100 * w / len(res):.1f} totR={sum(res):+.2f} "
            f"avgR={statistics.mean(res):+.3f}")


def verdict(rs: list[float]) -> str:
    res = [r for r in rs if r != 0.0]
    if len(res) < MIN_N_FOR_DECISION:
        return f"⏳ VERİ BİRİKİYOR (n={len(res)} < {MIN_N_FOR_DECISION}) — karar yok"
    tot = sum(res)
    if tot < 0:
        return "✅ KAPI HAKLI — elenenler zarardaydı, dokunma"
    return "⚠️ KAPI FAZLA SIKI — elenenler kârdaydı, gevşetme adayı"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--reason", default=None)
    a = ap.parse_args()

    skips = load_skips(a.days)
    if a.reason:
        skips = [s for s in skips if s.get("reason") == a.reason]
    if not skips:
        print(f"gate_skipped.jsonl'de {a.days} günlük kayıt yok.\n"
              f"(Bot yeni kodla çalışmaya başladıktan sonra birikir — "
              f"kapılar tetiklendikçe yazılır.)")
        return

    print(f"{len(skips)} eleme kaydı ({a.days} gün)\n")
    by_symbol = defaultdict(list)
    for s in skips:
        by_symbol[s["symbol"]].append(s)

    all_by_reason: dict[str, list[float]] = defaultdict(list)
    for symbol, recs in sorted(by_symbol.items()):
        since = min(parse_ts(r["ts"]) for r in recs) - timedelta(minutes=5)
        try:
            bars = fetch_bars(symbol, since)
        except Exception as exc:
            print(f"{symbol}: bar çekilemedi ({exc})")
            continue
        if not bars:
            print(f"{symbol}: 1m bar yok")
            continue
        run = make_runner(bars)
        by_reason: dict[str, list[float]] = defaultdict(list)
        for r in recs:
            val = run(r)
            if val is not None:
                by_reason[r.get("reason", "?")].append(val)
                all_by_reason[r.get("reason", "?")].append(val)
        print(f"── {symbol} ──")
        for reason, rs in sorted(by_reason.items()):
            print(f"  {reason:<22} {summarize(rs)}")
            print(f"  {'':<22} {verdict(rs)}")

    if len(by_symbol) > 1:
        print("\n── TÜM SEMBOLLER (kapı bazında) ──")
        for reason, rs in sorted(all_by_reason.items()):
            print(f"  {reason:<22} {summarize(rs)}")
            print(f"  {'':<22} {verdict(rs)}")


if __name__ == "__main__":
    main()
