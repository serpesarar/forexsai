"""Çok sembol gölge deneyinin özeti. Kullanım: python klon_coklu_ozet.py"""
from __future__ import annotations

import json

from klon_coklu import OZET_FILE


def main() -> None:
    d = json.loads(OZET_FILE.read_text(encoding="utf-8"))
    print("son güncelleme:", d["ts_utc"], "| kural:", d["kural"], "| tutarlar USD, sanal")
    print(f'{"sembol":10} {"var":3} {"net":>10} {"gerçekleşen":>12} {"swap":>8} {"yüzen":>10} {"TP":>5} {"kesici":>6} {"max sev":>7} {"en kötü net":>12}  açık seviye')
    for ad, o in d["semboller"].items():
        for v, x in o.items():
            print(f'{ad:10} {v:3} {x["net"]:10.2f} {x["gerceklesen"]:12.2f} {x["swap"]:8.2f} {x["yuzen"]:10.2f} {x["tp"]:5d} '
                  f'{x["kesici"]:6d} {x["max_seviye"]:7d} {x["en_kotu_net"]:12.2f}  B{x["seviye"]["BUY"]}/S{x["seviye"]["SELL"]}')
    print("üç sembol toplamının dakikalık dibi:", d["portfoy_dip"])


if __name__ == "__main__":
    main()
