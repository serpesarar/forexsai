"""repair_candle_cache.py — candle_cache saat kaymasını onar (MT5 kutusunda koşar).

SORUN: candle_cache'e yıllardır BROKER sunucu saatiyle (UTC+2/+3) damgalanmış barlar
yazılmış (bkz. RAPOR.md §1). Doğru yazan kaynaklarla karışmış durumda.

YÖNTEM — cerrahi, MT5 otorite:
  1. MT5'ten barları GERÇEK UTC damgayla çek (offset çalışma anında ölçülür).
  2. Bunları upsert et → doğru damgadaki satırlar düzelir/oluşur.
  3. MT5'in kapsadığı aralıkta, DB'de olup MT5'te OLMAYAN damgaları bul = HAYALET.
     Bunlar kaymış yazımların artıklarıdır.
  4. --apply verilmişse hayaletleri sil; verilmemişse yalnız SAY (kuru koşu).

GÜVENLİK:
  • Silme YALNIZ MT5'in kapsadığı zaman aralığında yapılır — MT5'in görmediği
    eski geçmişe DOKUNULMAZ.
  • Silinecek damgalar önce CSV'ye yazılır (kutuda `repair_backup/`), geri alınabilir.
  • Kuru koşu varsayılan.
"""
from __future__ import annotations

import csv
import sys
import time as _time
from datetime import datetime, timezone
from pathlib import Path

# Repo kökünü bul: "yeni deneme" klasörünü içeren ilk üst dizin (script repo
# kökünden de, research/ndx_buy_lab/ içinden de çalıştırılabilsin).
ROOT = Path.cwd()
for cand in [Path.cwd(), *Path(__file__).resolve().parents]:
    if (cand / "yeni deneme").is_dir():
        ROOT = cand
        break
sys.path.insert(0, str(ROOT / "yeni deneme"))

import MetaTrader5 as mt5  # noqa: E402
import config  # noqa: E402
from supabase import create_client  # noqa: E402

TF_MAP = {"1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
          "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1, "1d": mt5.TIMEFRAME_D1}
WANT = {"1m": 80000, "5m": 80000, "15m": 80000, "30m": 60000, "1h": 60000, "1d": 6000}
PAGE = 1000
_OFFSET = 0
STAMP = datetime.now(timezone.utc).isoformat()


def detect_offset(syms) -> int:
    for s in syms:
        try:
            if not mt5.symbol_select(s, True):
                continue
            tk = mt5.symbol_info_tick(s)
            if tk and tk.time:
                return int(round((tk.time - _time.time()) / 900.0) * 900)
        except Exception:
            continue
    return 0


def iso(epoch: int) -> str:
    return datetime.fromtimestamp(int(epoch) - _OFFSET, tz=timezone.utc).isoformat()


def db_timestamps(cl, symbol: str, tf: str, lo: str, hi: str) -> set[str]:
    out, off = set(), 0
    while True:
        r = (cl.table("candle_cache").select("candle_time")
             .eq("symbol", symbol).eq("timeframe", tf)
             .gte("candle_time", lo).lte("candle_time", hi)
             .order("candle_time").range(off, off + PAGE - 1).execute())
        rows = r.data or []
        for x in rows:
            out.add(datetime.fromisoformat(x["candle_time"].replace("Z", "+00:00"))
                    .astimezone(timezone.utc).isoformat())
        if len(rows) < PAGE:
            break
        off += PAGE
    return out


def main(apply: bool, upsert_only: bool = False, only_sym: str | None = None) -> None:
    global _OFFSET
    ok = (mt5.initialize(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                         server=config.MT5_SERVER) if config.MT5_ACCOUNT else mt5.initialize())
    if not ok:
        print("mt5 init fail", mt5.last_error()); sys.exit(1)
    syms = dict(config.RECORDER_SYMBOLS)
    if only_sym:
        syms = {k: v for k, v in syms.items() if k == only_sym}
    _OFFSET = detect_offset(list(syms.values()))
    print(f"MT5 sunucu offset: {_OFFSET/60:+.0f} dk  |  mod={'UYGULA' if apply else 'KURU KOŞU'}")
    cl = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    bdir = ROOT / "repair_backup"
    bdir.mkdir(exist_ok=True)

    grand = 0
    for fx, brk in syms.items():
        real = brk if mt5.symbol_info(brk) else None
        if real is None:
            for c in mt5.symbols_get() or []:
                if c.name.upper() == brk.upper():
                    real = c.name
                    break
        if not real:
            print(f"  ! {fx}: sembol yok"); continue
        mt5.symbol_select(real, True)
        for tf, want in WANT.items():
            rates = mt5.copy_rates_from_pos(real, TF_MAP[tf], 0, want)
            if rates is None or len(rates) == 0:
                print(f"  {fx} {tf}: MT5 verisi yok"); continue
            good = {}
            for r in rates:
                good[iso(r["time"])] = dict(
                    symbol=fx, timeframe=tf, candle_time=iso(r["time"]),
                    open=float(r["open"]), high=float(r["high"]),
                    low=float(r["low"]), close=float(r["close"]),
                    volume=float(r["tick_volume"]),
                    # KRİTİK: mevcut satır güncellenirken de damga tazelensin.
                    # Böylece "otoriter" satırlar (yeni VEYA güncellenmiş) eski
                    # kaymış artıklardan fetched_at ile kesin ayrılır.
                    fetched_at=STAMP)
            lo, hi = min(good), max(good)
            rows = list(good.values())
            for i in range(0, len(rows), PAGE):
                try:
                    cl.table("candle_cache").upsert(
                        rows[i:i + PAGE], on_conflict="symbol,timeframe,candle_time").execute()
                except Exception as e:
                    print(f"  ! upsert {fx} {tf} @{i}: {e}"); break
            if upsert_only:
                print(f"  {fx:12s} {tf:3s}: MT5={len(good):6d} yazıldı  {lo[:10]}→{hi[:10]}  "
                      f"(hayalet sayımı atlandı)")
                continue
            have = db_timestamps(cl, fx, tf, lo, hi)
            ghosts = sorted(have - set(good))
            grand += len(ghosts)
            print(f"  {fx:12s} {tf:3s}: MT5={len(good):6d}  DB(aralıkta)={len(have):6d}  "
                  f"HAYALET={len(ghosts):6d}   {lo[:10]}→{hi[:10]}")
            if not ghosts:
                continue
            with open(bdir / f"ghosts_{fx.replace('.','_')}_{tf}.csv", "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(["candle_time"])
                for g in ghosts:
                    w.writerow([g])
            if apply:
                for i in range(0, len(ghosts), 200):
                    try:
                        (cl.table("candle_cache").delete()
                         .eq("symbol", fx).eq("timeframe", tf)
                         .in_("candle_time", ghosts[i:i + 200]).execute())
                    except Exception as e:
                        print(f"  ! delete {fx} {tf} @{i}: {e}"); break
                print(f"      → {len(ghosts)} hayalet SİLİNDİ")
    print(f"\nTOPLAM HAYALET: {grand}  ({'silindi' if apply else 'silinmedi — kuru koşu'})")
    mt5.shutdown()


if __name__ == "__main__":
    sym = None
    for a in sys.argv[1:]:
        if a.startswith("--symbol="):
            sym = a.split("=", 1)[1]
    main("--apply" in sys.argv, "--upsert-only" in sys.argv, sym)
