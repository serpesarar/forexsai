"""NOM Faz 0 — Dukascopy USATECHIDXUSD 1m BID+ASK seri, nazik, devam ettirilebilir indirme.

Kalıp: research/ndx_seans_tasima_20261103/denetim/duka_slow.py (paralel istek 503 verir).
Kullanım: python src/duka_fetch.py 2026-01-01:2026-02-07,2018-01-01:2021-10-31 [BID,ASK]
Çıktı: data/duka_m1/YYYYMMDD_<SIDE>.bi5 (404 → boş dosya = veri yok günü)
"""
import sys, time, urllib.request, urllib.error, datetime as D
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'data' / 'duka_m1'
URL = 'https://datafeed.dukascopy.com/datafeed/USATECHIDXUSD/{y}/{m:02d}/{d:02d}/{side}_candles_min_1.bi5'
PACE_S = 1.5
MAX_BLOCK_S = 7200


def days(s: str, e: str):
    a, b = D.date.fromisoformat(s), D.date.fromisoformat(e)
    while a <= b:
        if a.weekday() != 5:          # Cumartesi işlem yok
            yield a
        a += D.timedelta(1)


def main() -> None:
    # argv: 'S1:E1,S2:E2,...' [SIDES] — aralıklar verilen SIRAYLA çekilir (öncelik)
    ranges = [r.split(':') for r in sys.argv[1].split(',')]
    sides = (sys.argv[2] if len(sys.argv) > 2 else 'BID').split(',')
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [(x, sd) for s, e in ranges for x in days(s, e) for sd in sides
            if not (OUT / f'{x:%Y%m%d}_{sd}.bi5').exists()]
    print('todo', len(todo), flush=True)
    done, blocked, wait = 0, 0, 60
    for x, sd in todo:
        u = URL.format(y=x.year, m=x.month - 1, d=x.day, side=sd)
        while True:
            try:
                b = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}),
                                           timeout=60).read()
                (OUT / f'{x:%Y%m%d}_{sd}.bi5').write_bytes(b)
                wait, blocked = 60, 0
                break
            except urllib.error.HTTPError as ex:
                if ex.code == 404:
                    (OUT / f'{x:%Y%m%d}_{sd}.bi5').write_bytes(b'')
                    break
                code = ex.code
            except Exception as ex:  # noqa: BLE001
                code = type(ex).__name__
            print(time.strftime('%H:%M:%S'), 'blocked', code, x, sd, 'wait', wait, flush=True)
            time.sleep(wait)
            blocked += wait
            wait = min(wait * 2, 600)
            if blocked >= MAX_BLOCK_S:
                print('GAVE UP after', blocked, 'done', done, flush=True)
                sys.exit(2)
        done += 1
        if done % 50 == 0:
            print(time.strftime('%H:%M:%S'), 'done', done, '/', len(todo), x, sd, flush=True)
        time.sleep(PACE_S)
    print('ALL DONE', done, flush=True)


if __name__ == '__main__':
    main()
