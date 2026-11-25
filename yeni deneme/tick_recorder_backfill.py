"""tick_recorder_backfill.py — tick_recorder'ın durduğu dönemi brokerın tick geçmişinden gün gün doldurur (TEK SEFERLİK).

Broker (Pepperstone) tick geçmişini ~3 ay tutar (2026-11-25 ölçümü: XAUUSD ≥ 2026-09-01); daha eskisi boş gelir.
tick_recorder ÇALIŞMIYORKEN koşturulmalı (aynı state.json). tick_recorder'ın kendi append_rows/save_state'i ve satır biçimi kullanılır;
her sembolde state'teki son msc'den sonrası yazılır → tekrar koşmak mükerrer üretmez.
Kullanım (kutuda): python tick_recorder_backfill.py
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import tick_recorder as T


def main() -> None:
    if not T.connect_mt5():
        raise SystemExit(1)
    st = T.load_state()
    now = datetime.now(timezone.utc)
    for fx, m in T.config.RECORDER_SYMBOLS.items():
        T.mt5.symbol_select(m, True)
        last = int(st.get(fx, 0))
        gun = (datetime.fromtimestamp(last / 1000, tz=timezone.utc) if last else now - timedelta(days=1)).replace(hour=0, minute=0, second=0,
                                                                                                                  microsecond=0)
        toplam, dolu = 0, 0
        while gun < now:
            r = T.mt5.copy_ticks_range(m, gun, gun + timedelta(days=1), T.mt5.COPY_TICKS_INFO)
            satir: dict[str, list] = {}
            mx = last
            for t in (r if r is not None else []):
                msc = int(t["time_msc"])
                if msc <= last:
                    continue
                mx = max(mx, msc)
                d = datetime.fromtimestamp(msc / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                satir.setdefault(d, []).append(f"{msc},{float(t['bid']):.5f},{float(t['ask']):.5f},{float(t['last']):.5f},{int(t['volume'])}\n")
            n = sum(len(v) for v in satir.values())
            if n:
                T.append_rows(fx, satir)
                st[fx] = mx
                last = mx
                T.save_state(st)
                toplam += n
                dolu += 1
            gun += timedelta(days=1)
            time.sleep(0.2)
        print(f"SONUC {fx} ({m}): {dolu} gün, {toplam} tick, son {datetime.fromtimestamp(last / 1000, tz=timezone.utc)}", flush=True)
    T.mt5.shutdown()


if __name__ == "__main__":
    main()
