"""box_export_trades_30d.py — MT5 kutusunda çalışır: son N günün işlem geçmişi.

Amaç: botun kapanmış pozisyonlarını (giriş/çıkış zamanı+fiyatı, SL/TP seviyeleri,
çıkış sebebi) TEK bir CSV'ye çıkarıp gzip+base64 olarak stdout'a basmak; panel
tarafı bunu çözüp 1m mumlarla grafiğe basar.

Canlı süreçlere DOKUNMAZ — yalnız `history_*` okur.

Zaman ekseni: MT5'in `time` alanı BROKER saatidir (UTC+2/+3). Tick ile ölçülen
offset çıkarılıp gerçek UTC'ye çevrilir (bkz. CLAUDE.md §MT5 zaman ekseni).

Çalıştırma (kutuda):
    python backend/research/box_export_trades_30d.py --days 32
"""
from __future__ import annotations

import argparse
import base64
import csv
import gzip
import io
import sys
import time as _time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda çalışır.")

try:
    import config  # type: ignore
except Exception:  # pragma: no cover
    config = None  # type: ignore

_OFFSET_SEC = 0


def connect() -> bool:
    if config is not None and getattr(config, "MT5_ACCOUNT", None):
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
        path = getattr(config, "MT5_TERMINAL_PATH", "")
        ok = mt5.initialize(path, **kw) if path else mt5.initialize(**kw)
    else:
        ok = mt5.initialize()
    if not ok:
        print("mt5.initialize basarisiz:", mt5.last_error())
    return bool(ok)


# Broker offset'i makul aralik: hicbir broker UTC'den ±5 saatten fazla sapmaz
# (Pepperstone = UTC+2/+3). Bunun disindaki her olcum BAYAT TICK demektir.
OFFSET_MIN_SEC, OFFSET_MAX_SEC = -5 * 3600, 5 * 3600


def detect_offset() -> int:
    """Broker sunucu saati − gerçek UTC (saniye).

    ⚠️ 2026-08-30 KRİTİK DÜZELTME: eski sürüm İLK tick veren sembolü kullanıyordu.
    O sembol kapalı/likit değilse tick BAYAT olur ve offset saatlerce yanlış çıkar
    (canlı vaka: −63.000 sn ölçüldü, doğrusu +10.800 sn → tüm zaman damgaları
    +1230 dk kaydı; `nasdaq_tam_veri_2026-08-29` paketi bu yüzden kayıktı).
    Yeni sürüm: BİRDEN FAZLA sembolden ölçer, makul aralık dışını ELER ve
    MEDYAN alır; hiçbiri geçerli değilse hata verip durur (sessizce 0 dönmez)."""
    syms = list((getattr(config, "RECORDER_SYMBOLS", None) or {}).values()) if config else []
    syms += [s.name for s in (mt5.symbols_get() or [])[:20]]
    now = _time.time()
    olcumler = []
    for sym in syms:
        try:
            if not mt5.symbol_select(sym, True):
                continue
            tk = mt5.symbol_info_tick(sym)
            if not tk or not tk.time:
                continue
            # tick'in kendisi bayat mi? (>15 dk once) → bu sembolu atla
            if abs(tk.time - now) > 5 * 3600 + 900:
                continue
            cand = int(round((tk.time - now) / 900.0) * 900)
            if OFFSET_MIN_SEC <= cand <= OFFSET_MAX_SEC:
                olcumler.append(cand)
        except Exception:
            continue
        if len(olcumler) >= 5:
            break
    if not olcumler:
        sys.exit("HATA: broker offset ölçülemedi (tüm tick'ler bayat). "
                 "Piyasa kapalıyken çalıştırıyorsan bekle — sessiz yanlış "
                 "zaman damgası yazmaktansa durmak daha iyi.")
    olcumler.sort()
    off = olcumler[len(olcumler) // 2]          # medyan: tek bayat tick bozamaz
    if len(set(olcumler)) > 1:
        print(f"UYARI: semboller farklı offset verdi {olcumler} → medyan {off} kullanıldı")
    return off


def to_utc(epoch: int) -> str:
    return datetime.fromtimestamp(int(epoch) - _OFFSET_SEC, tz=timezone.utc).isoformat()


def classify_exit(close_comment: str, deal_reason: int) -> str:
    """Kapanış sebebi: tp | sl | manual/bot | so (stop-out)."""
    c = (close_comment or "").lower()
    if "[tp" in c or c.strip().startswith("tp"):
        return "tp"
    if "[sl" in c or c.strip().startswith("sl"):
        return "sl"
    if "so:" in c or "stop out" in c:
        return "stopout"
    # DEAL_REASON: 0 client,1 mobile,2 web,3 expert,4 sl,5 tp,6 so
    return {4: "sl", 5: "tp", 6: "stopout", 3: "bot_close"}.get(int(deal_reason or -1), "manual")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=32)
    args = ap.parse_args()

    if not connect():
        sys.exit(1)
    global _OFFSET_SEC
    _OFFSET_SEC = detect_offset()

    info = mt5.account_info()
    print(f"hesap={getattr(info,'login',0)} broker={getattr(info,'company','')} "
          f"bakiye={getattr(info,'balance',0)} para={getattr(info,'currency','')}")
    print(f"broker_offset_dk={_OFFSET_SEC/60:+.0f}")

    # Pencereyi broker saatinde ver (history API broker saatiyle çalışır).
    now_b = datetime.now(timezone.utc) + timedelta(seconds=_OFFSET_SEC)
    frm = now_b - timedelta(days=args.days)
    to = now_b + timedelta(days=1)

    deals = mt5.history_deals_get(frm, to)
    if deals is None:
        sys.exit(f"history_deals_get None: {mt5.last_error()}")
    orders = mt5.history_orders_get(frm, to) or []
    print(f"deal={len(deals)} order={len(orders)}")

    # position_id -> ilk emrin SL/TP'si (girişte konan seviyeler)
    sltp: dict[int, tuple[float, float]] = {}
    for o in sorted(orders, key=lambda x: x.time_setup):
        pid = int(getattr(o, "position_id", 0) or 0)
        if pid and pid not in sltp and (o.sl or o.tp):
            sltp[pid] = (float(o.sl or 0), float(o.tp or 0))

    ins: dict[int, list] = {}
    outs: dict[int, list] = {}
    for d in deals:
        if d.entry == mt5.DEAL_ENTRY_IN:
            ins.setdefault(d.position_id, []).append(d)
        elif d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY):
            outs.setdefault(d.position_id, []).append(d)

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["position_id", "symbol", "direction", "magic", "volume",
                "open_time_utc", "open_price", "close_time_utc", "close_price",
                "sl_price", "tp_price", "exit_reason", "profit", "commission",
                "swap", "comment_in", "comment_out"])
    n = 0
    for pid, il in sorted(ins.items(), key=lambda kv: kv[1][0].time):
        i0 = il[0]
        ol = sorted(outs.get(pid) or [], key=lambda d: d.time)
        if not ol:
            continue  # hâlâ açık
        last = ol[-1]
        sl, tp = sltp.get(pid, (0.0, 0.0))
        w.writerow([
            pid, i0.symbol, "BUY" if i0.type == mt5.DEAL_TYPE_BUY else "SELL",
            int(getattr(i0, "magic", 0) or 0), float(i0.volume),
            to_utc(i0.time), float(i0.price),
            to_utc(last.time), float(last.price),
            sl, tp,
            classify_exit(str(last.comment or ""), getattr(last, "reason", -1)),
            round(sum(x.profit for x in ol), 2),
            round(sum(x.commission for x in ol) + sum(x.commission for x in il), 2),
            round(sum(x.swap for x in ol), 2),
            str(i0.comment or ""), str(last.comment or ""),
        ])
        n += 1

    # Açık pozisyonlar da bilgi olarak
    open_pos = mt5.positions_get() or []
    for p in open_pos:
        w.writerow([p.ticket, p.symbol, "BUY" if p.type == 0 else "SELL",
                    int(p.magic), float(p.volume), to_utc(p.time), float(p.price_open),
                    "", "", float(p.sl or 0), float(p.tp or 0), "open",
                    round(float(p.profit), 2), 0, round(float(p.swap), 2),
                    str(p.comment or ""), ""])

    print(f"kapali_pozisyon={n} acik_pozisyon={len(open_pos)}")
    blob = base64.b64encode(gzip.compress(buf.getvalue().encode())).decode()
    print(f"TRADES_B64_LEN={len(blob)}")
    print("TRADES_B64_BEGIN")
    for i in range(0, len(blob), 4000):
        print(blob[i:i + 4000])
    print("TRADES_B64_END")
    mt5.shutdown()


if __name__ == "__main__":
    main()
