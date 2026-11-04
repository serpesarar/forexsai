"""Kaba geçmiş: terminaldeki M3 barlarıyla aynı SembolKlon. Kutuda çalışır, kayıt tutmaz.

Bar içi yol varsayımı: açılış → (yükselen barda dip, düşen barda tepe) → karşı uç → kapanış.
Ask = bid + barın spread'i. Beklenti ayarı için değil, deneyin ne gösterebileceğini görmek için;
tick'le koşan deneyin yerine geçmez.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from klon_coklu import SEMBOLLER, TERMINAL, SembolKlon  # noqa: E402

BAR_N = 40_000


def main() -> None:
    import MetaTrader5 as m  # noqa: N813
    if not m.initialize(TERMINAL):
        raise SystemExit(m.last_error())
    print(f'{"sembol":10} {"var":3} {"dönem":23} {"net $":>10} {"gerç. $":>10} {"swap $":>8} {"TP":>5} {"kesici":>6} {"max sev":>7} {"en kötü yüzen":>13} {"en kötü net":>12}')
    for s in SEMBOLLER:
        i = m.symbol_info(s.ad)
        sk = SembolKlon(s, i.trade_tick_value / i.trade_tick_size,
                        {"mod": i.swap_mode, "long": i.swap_long, "short": i.swap_short, "point": i.point,
                         "uc_kat": i.swap_rollover3days})
        r = m.copy_rates_from_pos(s.ad, m.TIMEFRAME_M3, 0, BAR_N)
        pt = i.point
        for b in r:
            ms = int(b["time"]) * 1000
            sp = float(b["spread"]) * pt
            o, h, l, c = float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])
            yol = (o, l, h, c) if c >= o else (o, h, l, c)
            for n, px in enumerate(yol):
                sk.tick(ms + n * 45_000, px, px + sp)
        bas = r["time"][0]
        import time
        don = time.strftime("%Y-%m-%d", time.gmtime(bas)) + "→" + time.strftime("%Y-%m-%d", time.gmtime(r["time"][-1]))
        for v, x in sk.ozet().items():
            print(f'{s.ad:10} {v:3} {don:23} {x["net"]:10.0f} {x["gerceklesen"]:10.0f} {x["swap"]:8.0f} {x["tp"]:5d} {x["kesici"]:6d} '
                  f'{x["max_seviye"]:7d} {x["en_kotu_yuzen"]:13.0f} {x["en_kotu_net"]:12.0f}')


if __name__ == "__main__":
    main()
