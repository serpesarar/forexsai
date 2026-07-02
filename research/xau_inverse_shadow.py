"""
xau_inverse_shadow.py — XAU en-kötü-model TERS shadow sistemi (1m HONEST, veri-kaçağı-sız).
=============================================================================
Amaç: XAU'nun en başarısız modeli (pulse2 SELL, backend %2.9) sinyallerini TERS çevirip
(BUY) çeşitli TP/SL geometrileriyle GERÇEK 1m mumlarla resolve et — backend'in bozuk
resolution'ına GÜVENME. +EV geometri var mı bul.

GARANTİLER (kullanıcı şartı: "yanlış veri / veri kaçağı olmayacak"):
 1. LOOKAHEAD YOK: yalnız sinyal created_at'İNDEN SONRA kapanan mumlar (candle_time > created_at).
 2. TICK KİRLİLİĞİ FİLTRESİ: candle_cache '1m' içinde saniyelik tick kayıtları var → SADECE
    :00 saniyeli gerçek dakika mumları (second==0 & microsecond==0) kullanılır.
 3. INTRABAR KONSERVATİF: bir mumda hem TP hem SL vurulursa → hangisi önce belirsiz → LOSS say.
 4. DEDUP: saatlik (otokorelasyon şişirmesini kırar; pulse ~3dk'da bir sinyal veriyor).
 5. SPREAD: XAU spread R'den düşülür (varsayılan 0.05R ≈ ~0.3$ / tipik SL).
 6. Saat-frame doğrulandı (candle_cache & created_at AYNI UTC — broker-shift yok).

Yeni geometri seçenekleri (mirror yerine): TP = SL_riski × RR_hedef. Ters yön SABİT (%61 doğru),
sadece TP mesafesi taranır → breakeven RR (~0.64) üstü +EV olanı bulunur.
"""
from __future__ import annotations
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "yeni deneme"))
import config  # noqa: E402
import requests  # noqa: E402

SYMBOL = "XAUUSD"
MODEL = "pulse2"
DIRECTION = "SELL"          # en kötü model+yön → tersi (BUY) test edilir
HORIZON_H = 48
DEDUP_H = 1                 # saatlik dedup
SPREAD_R = 0.05             # R cinsinden işlem maliyeti (spread+slippage yaklaşık)
RR_GRID = [0.58, 0.7, 0.8, 1.0, 1.2, 1.5]   # taranan TP/SL geometrileri (0.58≈mirror)

HDR = {"apikey": config.SUPABASE_SERVICE_KEY,
       "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}"}
BASE = config.SUPABASE_URL.rstrip("/") + "/rest/v1"


def _get(path: str) -> list:
    r = requests.get(BASE + path, headers=HDR, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_signals(since="2026-06-01", until="2026-07-03") -> list[dict]:
    """En kötü model+yön sinyalleri: entry/stop/target dolu, geçerli geometri."""
    rows, off = [], 0
    while True:
        page = _get(f"/prediction_logs?symbol=eq.{SYMBOL}&model_type=eq.{MODEL}"
                    f"&ml_direction=eq.{DIRECTION}&ml_entry_price=not.is.null&ml_stop_price=not.is.null"
                    f"&ml_target_price=not.is.null&created_at=gte.{since}&created_at=lt.{until}"
                    f"&select=created_at,ml_entry_price,ml_stop_price,ml_target_price"
                    f"&order=created_at.asc&limit=1000&offset={off}")
        rows += page
        if len(page) < 1000:
            break
        off += 1000
    # geçerli SELL geometri: stop > entry > target
    out = []
    for s in rows:
        e, st, tg = s["ml_entry_price"], s["ml_stop_price"], s["ml_target_price"]
        if e and st and tg and st > e > tg:
            out.append({"t": datetime.fromisoformat(s["created_at"].replace("Z", "+00:00")),
                        "e": float(e), "stop": float(st), "target": float(tg)})
    return out


def fetch_candles_1m(since: datetime, until: datetime) -> list[tuple]:
    """1m mumlar — SADECE gerçek dakika (:00). Tick kirliliği filtrelenir. (epoch, high, low)."""
    out, off = [], 0
    # tz'siz ISO (değer UTC) — '+00:00' URL'de 400 veriyor
    s_iso = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    u_iso = until.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    while True:
        page = _get(f"/candle_cache?symbol=eq.{SYMBOL}&timeframe=eq.1m"
                    f"&candle_time=gte.{s_iso}&candle_time=lt.{u_iso}"
                    f"&select=candle_time,high,low&order=candle_time.asc&limit=1000&offset={off}")
        for c in page:
            ct = datetime.fromisoformat(c["candle_time"].replace("Z", "+00:00"))
            if ct.second == 0 and ct.microsecond == 0:        # TICK KİRLİLİĞİ FİLTRESİ
                out.append((ct.timestamp(), float(c["high"]), float(c["low"])))
        if len(page) < 1000:
            break
        off += 1000
    return out


def resolve_one(sig: dict, candles: list, tp_price: float, sl_price: float):
    """Ters BUY resolve — lookahead-safe + intrabar-konservatif. Dönüş: 'WIN'|'LOSS'|None."""
    import bisect
    t0 = sig["t"].timestamp()
    i = bisect.bisect_right([c[0] for c in candles], t0)   # created_at'ten SONRAKİ ilk mum
    end = t0 + HORIZON_H * 3600
    for j in range(i, len(candles)):
        ct, high, low = candles[j]
        if ct > end:
            break
        hit_sl = low <= sl_price       # BUY SL (aşağı)
        hit_tp = high >= tp_price      # BUY TP (yukarı)
        if hit_sl:                     # konservatif: çift-değme → SL (LOSS)
            return "LOSS"
        if hit_tp:
            return "WIN"
    return None


def dedup(sigs: list[dict]) -> list[dict]:
    last, out = None, []
    for s in sorted(sigs, key=lambda x: x["t"]):
        if last is None or (s["t"] - last).total_seconds() > DEDUP_H * 3600:
            out.append(s); last = s["t"]
    return out


def main():
    print(f"XAU TERS SHADOW — {MODEL} {DIRECTION} → ters BUY, 1m HONEST\n" + "=" * 64)
    sigs = fetch_signals()
    print(f"Sinyal: {len(sigs)} geçerli (stop>entry>target)")
    sigs = dedup(sigs)
    print(f"Dedup (saatlik): {len(sigs)} bağımsız işlem")
    if not sigs:
        return
    lo = min(s["t"] for s in sigs) - timedelta(minutes=5)
    hi = max(s["t"] for s in sigs) + timedelta(hours=HORIZON_H + 1)
    print(f"1m mum çekiliyor ({lo:%Y-%m-%d} → {hi:%Y-%m-%d})...")
    candles = fetch_candles_1m(lo, hi)
    print(f"Gerçek dakika mumu (:00, tick-filtreli): {len(candles)}\n")

    print(f"{'geometri (RR)':<16}{'işlem':>7}{'WR':>8}{'EV(R)':>9}{'EV-spread':>11}{'karar':>8}")
    print("-" * 60)
    for rr in RR_GRID:
        win = loss = openn = 0
        for s in sigs:
            sl_dist = s["e"] - s["target"]        # BUY SL riski = target mesafesi (R birimi)
            tp_price = s["e"] + rr * sl_dist       # BUY TP = RR × risk yukarı
            sl_price = s["target"]                 # BUY SL = target (aşağı)
            o = resolve_one(s, candles, tp_price, sl_price)
            if o == "WIN":
                win += 1
            elif o == "LOSS":
                loss += 1
            else:
                openn += 1
        n = win + loss
        if not n:
            continue
        wr = win / n
        ev = wr * rr - (1 - wr) * 1.0
        ev_net = ev - SPREAD_R
        tag = "✅ +EV" if ev_net > 0.03 else ("~" if ev_net > -0.03 else "❌")
        note = " (≈mirror)" if abs(rr - 0.58) < 0.02 else ""
        print(f"{('RR='+format(rr,'.2f')+note):<16}{n:>7}{wr*100:>7.0f}%{ev:>+9.3f}{ev_net:>+11.3f}{tag:>8}")

    print(f"\nSpread varsayımı: {SPREAD_R}R. WR HONEST (1m, lookahead-yok, tick-filtreli, "
          f"intrabar-konservatif, saatlik-dedup). Backend'in {MODEL} {DIRECTION} %2.9'una GÜVENME.")


if __name__ == "__main__":
    main()
