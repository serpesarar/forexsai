"""
data_recorder.py — SÜREKLI OHLC + indicator kaydedici  (MT5 kutusunda, botla paralel)
====================================================================================
NEDEN: MT5 bridge 1m yayınlamıyor ve diğer TF'ler de ~periyodik donuyor. Bu script
MT5'ten DOĞRUDAN çekip Supabase'e yazar → veri donması KALICI biter, üstüne her
mum için TÜM indicator değerleri kaydedilir (gelişim/forensik analiz için).

Yazılan tablolar:
  • candle_cache         (OHLC, mevcut tablo — bot/paneller bunu okur)
  • indicator_snapshots  (her kapalı mum için tam indicator seti, ind JSONB)

Zaman: MT5 Python API time'ı UTC kabul edilir (offset 0 — backend/candle_cache
konvansiyonuyla birebir aynı).

Çalıştırma:  python data_recorder.py
Ayar:        config.py  (RECORDER_SYMBOLS / RECORDER_TIMEFRAMES / SUPABASE_*)
"""
from __future__ import annotations
import sys
import time
import logging
from datetime import datetime, timezone

import config
from indicators import compute_all

try:
    import MetaTrader5 as mt5
except ImportError:
    print("HATA: MetaTrader5 yok. Bu script MT5 kutusunda çalışır."); sys.exit(1)
try:
    from supabase import create_client
except ImportError:
    print("HATA: pip install supabase"); sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler("data_recorder.log", encoding="utf-8")])
log = logging.getLogger("recorder")

TF_MAP = {"1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
          "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1}
HIST_BARS = 320           # steady-state pencere (ema200 + pay)
CC_CHUNK = 1000           # candle_cache upsert batch boyutu


def connect_mt5() -> bool:
    # LOGIN modu / ATTACH modu (MT5_ACCOUNT boş → açık terminale bağlan).
    # 2026-07-26: attach kurulumunda login=0 → '(-2, Invalid params)'.
    if config.MT5_ACCOUNT:
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH, **kw)
              if config.MT5_TERMINAL_PATH else mt5.initialize(**kw))
    else:
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH)
              if config.MT5_TERMINAL_PATH else mt5.initialize())
    if not ok:
        log.error("mt5.initialize başarısız: %s", mt5.last_error()); return False
    info = mt5.account_info()
    log.info("MT5 bağlı | hesap=%s broker=%s", getattr(info, "login", "?"),
             getattr(info, "company", "?"))
    return True


def supa():
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        log.error("config.SUPABASE_URL / SUPABASE_SERVICE_KEY boş — doldur."); sys.exit(1)
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


# ── MT5 SUNUCU SAATİ → GERÇEK UTC (2026-07-28 düzeltmesi) ───────────────────
# MT5'in copy_rates/tick `time` alanı epoch GİBİ görünür ama BROKER SUNUCU
# saatindedir (IC Markets: kış UTC+2, ABD-yaz UTC+3). Bunu doğrudan
# `fromtimestamp(..., tz=utc)` ile yazmak barları 2-3 saat İLERİ etiketler.
#
# Bulunan hasar (research/ndx_buy_lab/RAPOR.md §1): candle_cache'e 3 saat kaymış
# damgalar yazılıyordu → (a) sinyal↔mum eşleşmesi bozuk, (b) bayatlık kontrolleri
# "gelecekten gelen bar" gördüğü için hep taze sanıyor, (c) backend'in Redis
# köprüsü DOĞRU UTC yazdığı için bu script periyodik toplu yazımda doğru
# satırların ÜZERİNE kaymış veri basıyordu.
#
# Çözüm: offset'i çalışma anında ÖLÇ (sunucu tick zamanı − gerçek UTC), 15 dk'ya
# yuvarla. Böylece DST geçişleri ve broker değişiklikleri kendiliğinden çözülür.
_SERVER_OFFSET_SEC = 0
_OFFSET_KNOWN = False        # ilk başarılı ölçüm yapıldı mı (0 = "bilinmiyor" ile karışmasın)

# ── OFFSET ÖLÇÜM SAĞLAMLIĞI (2026-07-31 düzeltmesi) ─────────────────────────
# Eski sürüm 15 dk'ya yuvarlıyor ve TEK sembolün tick'ine güveniyordu. İki kaza:
#   1. Bayat tick (piyasa kapalı/sembol donmuş) → delta saatlerce sapar, 900'e
#      yuvarlanınca "makul" görünür. 2026-07-30 17:45'te ölçüm +135 dk çıktı
#      (doğrusu +180) → 68 dakika boyunca barlar 45 dk kaymış damgayla yazıldı.
#   2. 15 dk'lık yuvarlama 30m/1h ızgarasını BOZAR: 45 dk kayma :15/:45
#      damgaları üretir, upsert anahtarı farklı olduğu için doğru satırı EZMEZ →
#      hayalet bar kalıcı olarak birikir (temizlik öncesi 1h'te 18.006 satır).
# Çözüm: (a) TAM SAATE yuvarla — gerçek broker offset'leri tam saattir
# (Pepperstone UTC+2/+3); (b) her sembolün ölçümü toleranstan geçsin;
# (c) semboller arası ÇOĞUNLUK uzlaşması ara; (d) ölçülemezse 0'a düşme,
# bilinen son offset'i KORU.
OFFSET_SNAP_SEC = 3600       # tam saate yuvarla (30m/1h ızgarası korunur)
OFFSET_TOLERANCE_SEC = 240   # ham ölçüm, yuvarlanmış değerden en fazla bu kadar sapabilir
OFFSET_MAX_ABS_SEC = 14 * 3600   # |offset| bu değeri aşarsa ölçüm saçmadır


def detect_server_offset() -> int | None:
    """MT5 sunucu saati − gerçek UTC farkı (saniye).

    Dönüş: uzlaşılan offset, ya da güvenilir ölçüm yoksa None (çağıran mevcut
    offset'i korur — asla sessizce 0'a düşmez).
    """
    import time as _time
    from collections import Counter

    votes: list[int] = []
    detail: list[str] = []
    for sym in list(config.RECORDER_SYMBOLS.values()):
        try:
            if not mt5.symbol_select(sym, True):
                continue
            tick = mt5.symbol_info_tick(sym)
            if not tick or not tick.time:
                continue
            delta = tick.time - _time.time()
            snapped = int(round(delta / OFFSET_SNAP_SEC) * OFFSET_SNAP_SEC)
            if abs(delta - snapped) > OFFSET_TOLERANCE_SEC:
                # bayat tick / donmuş sembol: tam saate oturmuyor → OYU SAYMA
                detail.append(f"{sym}=RED({delta/60:+.1f}dk)")
                continue
            if abs(snapped) > OFFSET_MAX_ABS_SEC:
                detail.append(f"{sym}=RED(sınır dışı {snapped/3600:+.1f}s)")
                continue
            votes.append(snapped)
            detail.append(f"{sym}={snapped/60:+.0f}dk")
        except Exception:
            continue

    if not votes:
        log.warning("sunucu saat offset'i ölçülemedi (%s) — mevcut offset korunuyor: %+.0f dk",
                    ", ".join(detail) or "tick yok", _SERVER_OFFSET_SEC / 60.0)
        return None

    winner, n = Counter(votes).most_common(1)[0]
    if n * 2 <= len(votes) and len(votes) > 1:
        # net çoğunluk yok (ör. 2'ye 2) — belirsiz ölçümle damga kaydırma
        log.warning("offset uzlaşması yok (%s) — mevcut offset korunuyor: %+.0f dk",
                    ", ".join(detail), _SERVER_OFFSET_SEC / 60.0)
        return None

    log.info("MT5 sunucu saat offset'i: %+.1f dk (%d/%d sembol uzlaştı: %s)",
             winner / 60.0, n, len(votes), ", ".join(detail))
    return int(winner)


def _iso(epoch: int) -> str:
    """Broker sunucu epoch'unu GERÇEK UTC ISO damgasına çevir."""
    return datetime.fromtimestamp(epoch - _SERVER_OFFSET_SEC, tz=timezone.utc).isoformat()


def record(client, fx_symbol: str, mt5_symbol: str, tf_name: str, tf_const,
           last_seen: dict) -> None:
    key = (fx_symbol, tf_name)
    count = (config.RECORDER_BACKFILL_BARS.get(tf_name, HIST_BARS)  # ilk koşu: derin backfill
             if key not in last_seen else HIST_BARS)                # sonra: küçük pencere
    rates = mt5.copy_rates_from_pos(mt5_symbol, tf_const, 1, count)  # 1 = forming'i atla
    if rates is None or len(rates) < 30:
        return
    o = [float(r["open"]) for r in rates]; h = [float(r["high"]) for r in rates]
    l = [float(r["low"]) for r in rates];  c = [float(r["close"]) for r in rates]
    v = [float(r["tick_volume"]) for r in rates]
    t = [int(r["time"]) for r in rates]
    prev = last_seen.get(key, 0)
    new_idx = [i for i in range(len(t)) if t[i] > prev]
    if not new_idx:
        return

    now = datetime.now(timezone.utc).isoformat()
    # 1) candle_cache — tüm yeni kapalı barlar (chunk'lı: backfill binlerce satır olabilir)
    cc_rows = [{"symbol": fx_symbol, "timeframe": tf_name, "candle_time": _iso(t[i]),
                "open": o[i], "high": h[i], "low": l[i], "close": c[i],
                "volume": v[i], "fetched_at": now} for i in new_idx]
    for j in range(0, len(cc_rows), CC_CHUNK):
        try:
            client.table("candle_cache").upsert(
                cc_rows[j:j + CC_CHUNK], on_conflict="symbol,timeframe,candle_time").execute()
        except Exception as e:
            log.warning("%s %s candle_cache upsert hata: %s", fx_symbol, tf_name, e)

    # 2) indicator_snapshots — yeni barlar (poll başına tavan; gap OHLC olarak dolar,
    #    indicator istenirse candle_cache'ten sonradan yeniden hesaplanabilir)
    ind_rows = []
    for i in new_idx[-config.RECORDER_MAX_IND_PER_POLL:]:
        if i < 30:
            continue
        ind = compute_all(o[:i + 1], h[:i + 1], l[:i + 1], c[:i + 1], v[:i + 1])
        ind_rows.append({"symbol": fx_symbol, "timeframe": tf_name, "candle_time": _iso(t[i]),
                         "open": o[i], "high": h[i], "low": l[i], "close": c[i],
                         "volume": v[i], "ind": ind})
    # indicator satırları 29 anahtarlı JSONB taşır; 120'lik tek upsert Supabase
    # statement timeout'una (57014) düşüyordu ve hata YUTULUP tekrar denenmiyordu
    # → o barın göstergeleri kalıcı olarak kayboluyordu (denetimde XAUUSD 1h
    # kapsamı %54'e inmişti). Küçük parça + azalan boyutla yeniden deneme.
    _upsert_indicators(client, fx_symbol, tf_name, ind_rows)

    last_seen[key] = t[-1]
    log.info("  %-12s %-3s: +%d bar (son %s)", fx_symbol, tf_name, len(new_idx),
             _iso(t[-1])[11:16])


IND_CHUNK = 25            # JSONB ağır → küçük parça
IND_RETRY_CHUNKS = (25, 10, 1)


def _upsert_indicators(client, fx_symbol: str, tf_name: str, ind_rows: list) -> None:
    """indicator_snapshots upsert — parçalı ve zaman aşımına dayanıklı."""
    if not ind_rows:
        return
    failed = 0
    for j in range(0, len(ind_rows), IND_CHUNK):
        batch = ind_rows[j:j + IND_CHUNK]
        for size in IND_RETRY_CHUNKS:      # aynı batch'i giderek küçülterek dene
            ok = True
            for k in range(0, len(batch), size):
                try:
                    client.table("indicator_snapshots").upsert(
                        batch[k:k + size],
                        on_conflict="symbol,timeframe,candle_time").execute()
                except Exception as e:
                    ok = False
                    if size == IND_RETRY_CHUNKS[-1]:   # tek satır bile geçmedi
                        failed += 1
                        log.warning("%s %s indicator upsert BAŞARISIZ (%d satır): %s",
                                    fx_symbol, tf_name, len(batch[k:k + size]), e)
                    break
            if ok:
                break
    if failed:
        log.warning("%s %s: %d indicator parçası yazılamadı — kapsama boşluğu oluştu",
                    fx_symbol, tf_name, failed)


def resolve(mt5_symbol: str) -> str | None:
    if mt5.symbol_info(mt5_symbol) is not None:
        mt5.symbol_select(mt5_symbol, True)
        return mt5_symbol
    log.warning("%s MT5'te bulunamadı — atlandı", mt5_symbol)
    return None


def main():
    log.info("=" * 60)
    log.info("data_recorder başlıyor — semboller=%s TF=%s",
             list(config.RECORDER_SYMBOLS), config.RECORDER_TIMEFRAMES)
    log.info("=" * 60)
    if not connect_mt5():
        sys.exit(1)
    client = supa()
    last_seen: dict = {}
    resolved = {fx: resolve(m) for fx, m in config.RECORDER_SYMBOLS.items()}

    # Açılışta güvenilir offset ŞART — bilinen önceki değer yok, yanlış damga
    # tüm backfill'i zehirler. Ölçülemezse yaz(ma)dan çık (fail-closed).
    global _SERVER_OFFSET_SEC, _OFFSET_KNOWN
    for attempt in range(1, 6):
        off = detect_server_offset()
        if off is not None:
            _SERVER_OFFSET_SEC, _OFFSET_KNOWN = off, True
            break
        log.warning("açılış offset ölçümü %d/5 başarısız — 10 sn sonra tekrar", attempt)
        time.sleep(10)
    if not _OFFSET_KNOWN:
        log.error("sunucu saat offset'i açılışta ölçülemedi — YAZMADAN ÇIKILIYOR "
                  "(yanlış damgalı bar yazmaktansa hiç yazma). MT5 bağlantısını/"
                  "Market Watch sembollerini kontrol et.")
        mt5.shutdown()
        sys.exit(2)

    try:
        loops = 0
        while True:
            log.info("─── kayıt @ %s ───", datetime.now(timezone.utc).strftime("%H:%M:%S"))
            # DST geçişi / broker değişikliği: offset'i saatte bir tazele
            loops += 1
            if loops % max(1, int(3600 / max(config.RECORDER_POLL, 1))) == 0:
                new_off = detect_server_offset()
                # None = güvenilir ölçüm yok → mevcut offset'i KORU (eski sürüm
                # burada 0'a düşüp tüm barları broker saatinde yazıyordu)
                if new_off is not None and new_off != _SERVER_OFFSET_SEC:
                    log.warning("sunucu offset'i değişti: %+d dk → %+d dk (DST/broker)",
                                _SERVER_OFFSET_SEC // 60, new_off // 60)
                    _SERVER_OFFSET_SEC = new_off
                    # SADECE SON PENCEREYİ yeniden yaz — last_seen.clear() DEĞİL.
                    # clear() `key not in last_seen` yaptığı için DERİN BACKFILL
                    # tetikliyordu ve aylarca geçmişi YENİ offset'le yeniden
                    # damgalıyordu. Oysa MT5 tarihsel barları kendi döneminin
                    # sunucu saatinde tutar: DST geçişinde tüm geçmişi 1 saat
                    # kaydırıp piyasanın KAPALI olduğu saate hayalet bar basıyordu
                    # (NDX 21:00 UTC'de 946 satır, MT5'te o saatte 0 bar).
                    # 0'a çekmek pencereyi HIST_BARS ile sınırlar: yakın geçmiş
                    # düzeltilir, eski geçmişe dokunulmaz.
                    for k in last_seen:
                        last_seen[k] = 0
            for fx, mt5_symbol in config.RECORDER_SYMBOLS.items():
                rs = resolved.get(fx)
                if not rs:
                    continue
                for tf_name in config.RECORDER_TIMEFRAMES:
                    tf_const = TF_MAP.get(tf_name)
                    if tf_const is None:
                        continue
                    try:
                        record(client, fx, rs, tf_name, tf_const, last_seen)
                    except Exception as e:
                        log.exception("%s %s kayıt hata: %s", fx, tf_name, e)
            time.sleep(config.RECORDER_POLL)
    except KeyboardInterrupt:
        log.info("Durduruldu (Ctrl+C).")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
