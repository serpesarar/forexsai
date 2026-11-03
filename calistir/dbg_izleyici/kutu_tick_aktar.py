"""DBG terminalinden ilk ayrışma pencerelerinin ham tick'lerini dışa aktarır. Salt-okuma.

Terminal: C:\\Program Files\\MetaTrader 5 (botun Pepperstone terminali DEĞİL). Hesap DBG değilse durur.

Kullanım (kutuda):
    python kutu_tick_aktar.py --terminal "D:\\MT5_DBG\\terminal64.exe" --pencereler tick_pencereleri.csv --cikis ticks\\

Pencere zamanları broker SUNUCU saatidir. MT5 tick zamanları da sunucu saatidir; datetime'lar
UTC etiketli verilir (MT5 bunları sunucu saati olarak yorumlar; CLAUDE.md §9).
Çıktı: pencere başına bir CSV (time_msc, bid, ask, last, volume, flags).
"""
from __future__ import annotations

import argparse
from datetime import timezone
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--terminal", required=True)
    ap.add_argument("--pencereler", required=True)
    ap.add_argument("--cikis", required=True)
    ap.add_argument("--sembol", default="XAUUSD.GC")
    a = ap.parse_args()
    import MetaTrader5 as mt5  # noqa: N813
    if not mt5.initialize(a.terminal):
        raise SystemExit(f"initialize başarısız: {mt5.last_error()}")
    acc = mt5.account_info()
    if acc is None or "DBG" not in (acc.server or ""):
        raise SystemExit(f"Bu terminal DBG sunucusuna bağlı değil ({getattr(acc, 'server', None)}); durdu.")
    out = Path(a.cikis)
    out.mkdir(parents=True, exist_ok=True)
    w = pd.read_csv(a.pencereler, parse_dates=["bas_sunucu", "bit_sunucu"])
    for i, r in enumerate(w.itertuples()):
        t0 = r.bas_sunucu.to_pydatetime().replace(tzinfo=timezone.utc)
        t1 = r.bit_sunucu.to_pydatetime().replace(tzinfo=timezone.utc)
        ticks = mt5.copy_ticks_range(a.sembol, t0, t1, mt5.COPY_TICKS_ALL)
        df = pd.DataFrame(ticks if ticks is not None else [])
        df.to_csv(out / f"w{i:04d}_{r.bas_sunucu:%Y%m%d_%H%M}.csv", index=False)
    mt5.shutdown()
    print(len(w), "pencere yazıldı ->", out)


if __name__ == "__main__":
    main()
