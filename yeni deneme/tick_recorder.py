"""
tick_recorder.py — SÜREKLİ tick kaydedici, YEREL diske  (MT5 kutusunda, botla paralel)
======================================================================================
NEDEN: MT5 bridge tick'i Redis pub/sub'a basıyor ama pub/sub uçucu — tick geçmişi
hiçbir yerde arşivlenmiyor. Scalp refleks motorunun mikro-teyit araştırması ve
karar-anı spread analizi için bid/ask tick arşivi gerekiyor. Supabase'e DEĞİL,
yerel diske yazar (hacim: gz ile ~1-2 MB/gün/sembol, yılda ~3 GB).

Yazılan dosyalar (script klasörünün altında):
  • tickdata/<SEMBOL>/<YYYY-MM-DD>.csv.gz   (UTC güne göre; kolonlar:
      time_msc,bid,ask,last,volume — spread = ask-bid buradan türetilir)
  • tickdata/state.json                     (sembol başına son kaydedilen msc;
      restart'ta kaldığı yerden devam, mükerrer yazmaz)

Not: Aynı milisaniyeye düşen ardışık tick'lerden sonrakiler nadiren atlanabilir
(msc+1'den devam) — spread/mikroyapı analizi için ihmal edilebilir.

Zaman: MT5 tick time_msc UTC kabul edilir (data_recorder konvansiyonu).

Çalıştırma:  python tick_recorder.py          (calistir/16_tick_kaydedici.bat)
Ayar:        config.py  (RECORDER_SYMBOLS / MT5_*)
"""
from __future__ import annotations

import gzip
import json
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config

try:
    import MetaTrader5 as mt5
except ImportError:
    print("HATA: MetaTrader5 yok. Bu script MT5 kutusunda çalışır."); sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler("tick_recorder.log", encoding="utf-8")])
log = logging.getLogger("tick_recorder")

POLL_S = 30                 # kaç saniyede bir yeni tick çekilir
FIRST_BACKFILL_MIN = 60     # ilk koşuda geriye dönük pencere
MAX_FETCH_H = 12            # tek seferde en fazla bu kadar geriden çek (uzun kapalılık)
DATA_DIR = Path(__file__).resolve().parent / "tickdata"
STATE_FILE = DATA_DIR / "state.json"
HEADER = "time_msc,bid,ask,last,volume\n"


def connect_mt5() -> bool:
    kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
    ok = (mt5.initialize(config.MT5_TERMINAL_PATH, **kw) if config.MT5_TERMINAL_PATH
          else mt5.initialize(**kw))
    if not ok:
        log.error("mt5.initialize başarısız: %s", mt5.last_error()); return False
    info = mt5.account_info()
    log.info("MT5 bağlı | hesap=%s broker=%s", getattr(info, "login", "?"),
             getattr(info, "company", "?"))
    return True


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    tmp.replace(STATE_FILE)


def append_rows(fx_symbol: str, rows_by_day: dict) -> None:
    """rows_by_day: 'YYYY-MM-DD' → list[str satır]. gzip'e member-append."""
    for day, lines in rows_by_day.items():
        d = DATA_DIR / fx_symbol
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{day}.csv.gz"
        new_file = not path.exists()
        with gzip.open(path, "at", encoding="utf-8") as f:
            if new_file:
                f.write(HEADER)
            f.writelines(lines)


def fetch_and_store(fx_symbol: str, mt5_symbol: str, state: dict) -> int:
    now = datetime.now(timezone.utc)
    last_msc = state.get(fx_symbol, 0)
    if last_msc <= 0:
        frm = now - timedelta(minutes=FIRST_BACKFILL_MIN)
    else:
        frm = max(datetime.fromtimestamp((last_msc + 1) / 1000, tz=timezone.utc),
                  now - timedelta(hours=MAX_FETCH_H))
    ticks = mt5.copy_ticks_range(mt5_symbol, frm, now, mt5.COPY_TICKS_INFO)
    if ticks is None or len(ticks) == 0:
        return 0
    rows_by_day: dict[str, list] = {}
    max_msc = last_msc
    for t in ticks:
        msc = int(t["time_msc"])
        if msc <= last_msc:
            continue
        max_msc = max(max_msc, msc)
        day = datetime.fromtimestamp(msc / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        rows_by_day.setdefault(day, []).append(
            f"{msc},{float(t['bid']):.5f},{float(t['ask']):.5f},"
            f"{float(t['last']):.5f},{int(t['volume'])}\n")
    n = sum(len(v) for v in rows_by_day.values())
    if n:
        append_rows(fx_symbol, rows_by_day)
        state[fx_symbol] = max_msc
    return n


def main() -> None:
    if not connect_mt5():
        sys.exit(1)
    symbols = dict(config.RECORDER_SYMBOLS)
    log.info("Tick kaydedici başladı | semboller=%s | hedef=%s",
             list(symbols), DATA_DIR)
    state = load_state()
    last_summary = time.time()
    counts = {fx: 0 for fx in symbols}
    while True:
        if mt5.account_info() is None:          # kopmuş — yeniden bağlan
            log.warning("MT5 bağlantısı yok, yeniden deneniyor...")
            mt5.shutdown()
            time.sleep(10)
            if not connect_mt5():
                time.sleep(30)
                continue
        for fx, m in symbols.items():
            try:
                counts[fx] += fetch_and_store(fx, m, state)
            except Exception as e:               # tek sembol düşürmesin
                log.error("%s tick çekme hatası: %s", fx, e)
        save_state(state)
        if time.time() - last_summary >= 600:    # 10dk'da bir özet
            log.info("10dk özeti: %s", {k: v for k, v in counts.items()})
            counts = {fx: 0 for fx in symbols}
            last_summary = time.time()
        time.sleep(POLL_S)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Durduruldu (Ctrl+C).")
        mt5.shutdown()
