"""
sl_forensics.py — SL POST-MORTEM / gelişim analizi  (MT5 kutusunda çalıştır)
============================================================================
Her SL'in NEDEN olduğunu sınıflandırır:
  • stop_too_tight : SL'den sonra fiyat geri dönüp would-be TP'yi vurdu (whipsaw /
                     dar stop / erken giriş) — yön DOĞRUYDU, çıkış kötüydü.
  • direction_wrong: SL ötesine belirgin devam etti — yön YANLIŞTI.
  • chop          : ne TP'ye döndü ne sert devam etti — kararsız.

Girdi : entry_fingerprints.jsonl (bot canlıda yazar) + MT5 geçmiş deal'leri + MT5 1m.
Çıktı : sl_postmortem.jsonl + ekrana gelişim özeti (sembol/scope/seans/giriş-tipi).

Kullanım:
    python sl_forensics.py                 # son 7 gün, SL sonrası 240dk bak
    python sl_forensics.py --days 3 --forward-min 180
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import config

try:
    import MetaTrader5 as mt5
except ImportError:
    print("HATA: MetaTrader5 yok. Bu script MT5 kutusunda çalışır."); sys.exit(1)

FINGERPRINT_FILE = "entry_fingerprints.jsonl"
OUT = "sl_postmortem.jsonl"


def connect() -> bool:
    kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
    ok = (mt5.initialize(config.MT5_TERMINAL_PATH, **kw) if config.MT5_TERMINAL_PATH
          else mt5.initialize(**kw))
    if not ok:
        print(f"mt5.initialize başarısız: {mt5.last_error()}"); return False
    return True


def load_fingerprints() -> dict[int, dict]:
    fps: dict[int, dict] = {}
    try:
        with open(FINGERPRINT_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    fps[int(r["ticket"])] = r          # ticket = position_id
    except FileNotFoundError:
        print(f"UYARI: {FINGERPRINT_FILE} yok (bot henüz canlı parmak izi yazmamış).")
    return fps


def close_reason(comment: str) -> str:
    c = (comment or "").lower()
    if "tp" in c: return "tp"
    if "sl" in c: return "sl"
    return "other"


def classify(fp: dict, sl_price: float, direction: str, fbars: list) -> dict:
    """SL sonrası 1m yoluna bakarak sınıflandır."""
    D = 1 if direction == "BUY" else -1
    entry = fp.get("entry"); tp = fp.get("tp")
    risk = abs(entry - sl_price) if entry else None
    mfe = mae = 0.0; reached_tp = recovered = False
    for b in fbars:
        hi, lo = b["high"], b["low"]
        fav = (hi - sl_price) if D > 0 else (sl_price - lo)   # SL'den lehte gidiş
        adv = (sl_price - lo) if D > 0 else (hi - sl_price)   # SL'den aleyhte gidiş
        mfe = max(mfe, fav); mae = max(mae, adv)
        if entry and ((D > 0 and hi >= entry) or (D < 0 and lo <= entry)):
            recovered = True
        if tp and ((D > 0 and hi >= tp) or (D < 0 and lo <= tp)):
            reached_tp = True
    if reached_tp:
        cls = "stop_too_tight"
    elif risk and mae > risk:
        cls = "direction_wrong"
    else:
        cls = "chop"
    return {"class": cls, "reached_would_be_tp": reached_tp, "recovered_to_entry": recovered,
            "mfe_after_sl": round(mfe, 5), "mae_after_sl": round(mae, 5),
            "mfe_in_R": round(mfe / risk, 2) if risk else None}


def pct(n, d): return f"{n/d*100:.0f}%" if d else "—"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--forward-min", type=int, default=240)
    args = ap.parse_args()

    fps = load_fingerprints()
    if not connect():
        sys.exit(1)
    try:
        to = datetime.now(timezone.utc)
        frm = to - timedelta(days=args.days)
        deals = mt5.history_deals_get(frm, to) or []
        closes = [d for d in deals if d.magic == config.MAGIC_NUMBER
                  and d.entry == mt5.DEAL_ENTRY_OUT]
        print(f"Son {args.days} gün: {len(closes)} kapanış (magic={config.MAGIC_NUMBER}), "
              f"{len(fps)} parmak izi.\n")

        bars_cache: dict[str, list] = {}
        def forward_bars(symbol, sl_epoch):
            if symbol not in bars_cache:
                r = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 11000)
                bars_cache[symbol] = list(r) if r is not None else []
            end = sl_epoch + args.forward_min * 60
            return [{"high": float(b["high"]), "low": float(b["low"])}
                    for b in bars_cache[symbol] if sl_epoch < b["time"] <= end]

        records = []
        for d in closes:
            reason = close_reason(d.comment)
            fp = fps.get(d.position_id)
            rec = {
                "position_id": d.position_id, "mt5_symbol": d.symbol,
                "close_time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
                "close_price": d.price, "profit": d.profit, "close_reason": reason,
                "scope": (fp or {}).get("scope"), "direction": (fp or {}).get("direction"),
                "entry_type": (fp or {}).get("entry_type"), "tp_source": (fp or {}).get("tp_source"),
                "session": (fp or {}).get("session"), "mom_stretch": (fp or {}).get("mom_stretch"),
                "rr": (fp or {}).get("rr"), "matched_fp": fp is not None,
            }
            if reason == "sl" and fp:
                rec.update(classify(fp, d.price, fp["direction"], forward_bars(d.symbol, d.time)))
            records.append(rec)

        with open(OUT, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"yazıldı → {OUT}\n")
        summarize(records)
    finally:
        mt5.shutdown()


def summarize(records):
    sls = [r for r in records if r["close_reason"] == "sl"]
    tps = [r for r in records if r["close_reason"] == "tp"]
    analyzed = [r for r in sls if "class" in r]
    print("=" * 70)
    print(f"ÖZET: {len(tps)} TP · {len(sls)} SL · {len(analyzed)} SL analiz edildi "
          f"(parmak izi eşleşen)")
    print("=" * 70)
    if not analyzed:
        print("Analiz edilecek (parmak izi eşleşen) SL yok — bot canlıda biraz çalışınca tekrar koş.")
        return

    # genel sınıf dağılımı
    cl = defaultdict(int)
    for r in analyzed: cl[r["class"]] += 1
    n = len(analyzed)
    print(f"\nSL SINIFI (genel):")
    for c in ("stop_too_tight", "direction_wrong", "chop"):
        print(f"  {c:16s}: {cl[c]:3d}  {pct(cl[c], n)}")
    print(f"  → 'stop_too_tight' yüksekse: SL dar / giriş erken (TP/SL veya zamanlama düzelt)")
    print(f"  → 'direction_wrong' yüksekse: model/yön sorunu (sinyal kalitesi)")

    def breakdown(key, label):
        print(f"\nSL sınıfı × {label}:")
        grp = defaultdict(lambda: defaultdict(int))
        for r in analyzed:
            grp[r.get(key)][r["class"]] += 1
        for g in sorted(grp, key=lambda x: str(x)):
            tot = sum(grp[g].values())
            print(f"  {str(g):22s} n={tot:3d} | tight {pct(grp[g]['stop_too_tight'],tot):>4s} "
                  f"wrong {pct(grp[g]['direction_wrong'],tot):>4s} chop {pct(grp[g]['chop'],tot):>4s}")
    breakdown("scope", "scope")
    breakdown("session", "seans")
    breakdown("entry_type", "giriş tipi (S/R vs market)")

    # momentum: SL vs TP girişlerinde ortalama stretch
    import statistics as st
    sl_mom = [r["mom_stretch"] for r in sls if isinstance(r.get("mom_stretch"), (int, float))]
    tp_mom = [r["mom_stretch"] for r in tps if isinstance(r.get("mom_stretch"), (int, float))]
    if sl_mom and tp_mom:
        print(f"\nGiriş momentum (M15 stretch) — SL'ler vs TP'ler:")
        print(f"  SL ort={st.mean(sl_mom):+.2f}  TP ort={st.mean(tp_mom):+.2f}  "
              f"→ {'SL daha düşük momentumda (eşik yükselt?)' if st.mean(sl_mom)<st.mean(tp_mom) else 'fark belirsiz'}")


if __name__ == "__main__":
    main()
