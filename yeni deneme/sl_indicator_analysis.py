"""
sl_indicator_analysis.py — SL'leri indicator_snapshots'a JOIN + WIN/LOSS ayrımı.
====================================================================================
Soru: işlemlerim (özellikle SL'ler) HANGİ gösterge koşullarında oluyor? Hangi tek
gösterge filtresi WR'ı artırır? (gelişim / edge keşfi)

Akış:
  1. MT5 geçmiş deal'leri → position_id ile aç/kapa eşle → trade (giriş zamanı=FILL,
     yön, sonuç tp/sl, kâr).
  2. Supabase indicator_snapshots → her sembol×TF için pencere yüklenir.
  3. Her trade'in FILL zamanına ≤ en yakın snapshot bulunur (TF başına), göstergeler
     tf-önekiyle birleştirilir (ör. '5m_rsi14').
  4. discrimination.discriminate + best_filter → AUC sıralı rapor + filtre önerileri.

MT5 kutusunda çalıştır:  python sl_indicator_analysis.py [--days 14]
Önkoşul: data_recorder.py bir süredir çalışıp indicator_snapshots'ı doldurmuş olmalı.
"""
from __future__ import annotations
import argparse, sys, bisect
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import config
from discrimination import discriminate, best_filter, print_report
from combo_filter import combo_report

try:
    import MetaTrader5 as mt5
except ImportError:
    print("MetaTrader5 yok — MT5 kutusunda çalıştır."); sys.exit(1)
try:
    from supabase import create_client
except ImportError:
    print("pip install supabase"); sys.exit(1)

ANALYSIS_TFS = ["1m", "5m", "15m"]          # giriş-zamanlama göstergeleri
MT5_TO_FX = {m: fx for fx, m in config.RECORDER_SYMBOLS.items()}


def connect() -> bool:
    """LOGIN modu (MT5_ACCOUNT dolu) veya ATTACH modu (0/boş → açık terminal).
    2026-07-26: attach kurulumunda login=0 → '(-2, Invalid params)' (haftalık
    iş fail sebebi). Bot'taki connect_mt5 ile aynı mantık."""
    if config.MT5_ACCOUNT:
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH, **kw)
              if config.MT5_TERMINAL_PATH else mt5.initialize(**kw))
    else:
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH)
              if config.MT5_TERMINAL_PATH else mt5.initialize())
    if not ok:
        print(f"mt5.initialize: {mt5.last_error()}"); return False
    return True


def supa():
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        print("config.SUPABASE_URL / SUPABASE_SERVICE_KEY boş."); sys.exit(1)
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def _reason(comment: str) -> str:
    c = (comment or "").lower()
    return "tp" if "tp" in c else ("sl" if "sl" in c else "other")


def pair_trades(days: int) -> list[dict]:
    """MT5 deal'lerini position_id ile aç/kapa eşle → trade listesi."""
    to = datetime.now(timezone.utc); frm = to - timedelta(days=days)
    deals = mt5.history_deals_get(frm, to) or []
    opens, closes = {}, {}
    for d in deals:
        if d.magic != config.MAGIC_NUMBER:
            continue
        if d.entry == mt5.DEAL_ENTRY_IN:
            opens[d.position_id] = d
        elif d.entry == mt5.DEAL_ENTRY_OUT:
            closes[d.position_id] = d
    trades = []
    for pid, od in opens.items():
        cd = closes.get(pid)
        if not cd:
            continue
        reason = _reason(cd.comment)
        if reason not in ("tp", "sl"):
            continue
        trades.append({
            "pid": pid, "mt5_symbol": od.symbol,
            "symbol": MT5_TO_FX.get(od.symbol, od.symbol),
            "direction": "BUY" if od.type == mt5.DEAL_TYPE_BUY else "SELL",
            "entry_epoch": int(od.time), "win": reason == "tp",
            "reason": reason, "profit": cd.profit,
        })
    return trades


def load_snapshots(client, symbols, tfs, frm_iso):
    """indicator_snapshots → {(symbol,tf): [(epoch, ind_dict), ...]} sıralı."""
    store = {}
    for sym in symbols:
        for tf in tfs:
            rows, off = [], 0
            while True:
                r = (client.table("indicator_snapshots")
                     .select("candle_time,ind").eq("symbol", sym).eq("timeframe", tf)
                     .gte("candle_time", frm_iso).order("candle_time")
                     .range(off, off + 999).execute().data)
                rows += r
                if len(r) < 1000:
                    break
                off += 1000
            arr = [(int(datetime.fromisoformat(x["candle_time"]).timestamp()), x["ind"]) for x in rows]
            arr.sort()
            store[(sym, tf)] = arr
    return store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()
    if not connect():
        sys.exit(1)
    try:
        trades = pair_trades(args.days)
        print(f"{len(trades)} kapalı tp/sl işlem (son {args.days} gün).")
        if not trades:
            print("İşlem yok — bot canlıda biraz çalışınca tekrar koş."); return
        client = supa()
        symbols = sorted({t["symbol"] for t in trades})
        frm_iso = (datetime.now(timezone.utc) - timedelta(days=args.days + 1)).isoformat()
        store = load_snapshots(client, symbols, ANALYSIS_TFS, frm_iso)

        rows = []
        for t in trades:
            ind = {}
            for tf in ANALYSIS_TFS:
                arr = store.get((t["symbol"], tf), [])
                if not arr:
                    continue
                i = bisect.bisect_right([a[0] for a in arr], t["entry_epoch"]) - 1
                if i >= 0:
                    for k, v in arr[i][1].items():
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            ind[f"{tf}_{k}"] = v
            if ind:
                rows.append({"win": t["win"], "ind": ind, "symbol": t["symbol"],
                             "direction": t["direction"]})

        matched = len(rows)
        print(f"{matched} işlem indicator_snapshots ile eşleşti.\n")
        if matched < 20:
            print("Az eşleşme — data_recorder.py daha uzun çalışmalı (snapshot birikmeli)."); return

        print_report(rows, "TÜM İŞLEMLER — gösterge ayrımı")
        for sym in symbols:
            sub = [r for r in rows if r["symbol"] == sym]
            if len(sub) >= 40:
                print()
                print_report(sub, f"{sym} — gösterge ayrımı")

        # çok-göstergeli kombinasyon keşfi (overfit korumalı: nested-CV + placebo)
        # İki mod: serbest (en iyi) + zorunlu cross-TF (multi-TF gerçekten yardım ediyor mu?)
        print()
        combo_report(rows, "TÜM İŞLEMLER — serbest", min_tfs=1)
        print()
        combo_report(rows, "TÜM İŞLEMLER — zorunlu cross-TF", min_tfs=2)
        for scope in sorted({f"{r['symbol']}:{r['direction']}" for r in rows}):
            sub = [r for r in rows if f"{r['symbol']}:{r['direction']}" == scope]
            if len(sub) >= 60:
                print()
                combo_report(sub, f"{scope} — serbest", min_tfs=1)
                print()
                combo_report(sub, f"{scope} — zorunlu cross-TF", min_tfs=2)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
