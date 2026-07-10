"""
data_contract.py — SIFIR-GÜVEN VERİ SÖZLEŞMESİ: her bar tüketicisi girdisini doğrular.
=============================================================================
Bugüne kadarki TÜM veri kazaları aynı sınıftı — sistem girdisine güvendi:
tick-kirli candle_cache · broker-saat karışıklığı · forming-bar hacmi · frozen hafta-sonu
feed'i (334 zehirli kayıt) · sahte backend resolution. Her birini tek tek yakalayıp yamadık.
Bu katman sınıfın KENDİSİNİ kapatır: bar verisi kullanılmadan önce sözleşmeden geçer;
ihlal = SESSİZ ZEHİR yerine GÜRÜLTÜLÜ ATLAMA (fail-closed).

Kontroller (saat-dilimi BAĞIMSIZ — mutlak saat kıyası yapmaz):
 1. yeterlilik: min bar sayısı
 2. zaman monotonik ARTAN (geri giden/duplike zaman = bozuk kaynak)
 3. TF-aralık tutarlılığı: bar aralıklarının medyanı beklenen TF'e uymalı
    (tick-kirliliği yakalar: 1m serisine saniyelik kayıt karışması → medyan << TF)
 4. OHLC tutarlılığı: high≥low, high≥open/close, low≤open/close, fiyat>0, None/NaN yok
 5. flat-line şüphesi: son N barın HEPSİ high==low (ölü/sentetik feed)
Kullanım: ok, reason = validate_bars(bars, tf); ok değilse tüketici o sembolü ATLAR.
"""
from __future__ import annotations

TF_SEC = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}
MIN_BARS = 30
FLAT_N = 12            # son 12 bar hepsi high==low → ölü feed şüphesi


def validate_bars(bars: list[dict] | None, tf: str, min_bars: int = MIN_BARS) -> tuple[bool, str]:
    """Bar serisi sözleşmesi. Dönüş: (geçerli_mi, sebep). Saf/fail-closed — istisna fırlatmaz."""
    try:
        if not bars or len(bars) < min_bars:
            return False, f"yetersiz bar ({0 if not bars else len(bars)}<{min_bars})"
        times = [b.get("time") for b in bars]
        has_time = all(isinstance(t, (int, float)) for t in times)
        if has_time:
            # 2) monotonik artan
            for a, b in zip(times, times[1:]):
                if b <= a:
                    return False, f"zaman monotonik değil ({a}→{b}: duplike/geri)"
            # 3) TF-aralık tutarlılığı (tick-kirliliği dedektörü)
            exp = TF_SEC.get(tf)
            if exp:
                deltas = sorted(b - a for a, b in zip(times, times[1:]))
                med = deltas[len(deltas) // 2]
                if med < exp * 0.9:            # medyan aralık TF'ten belirgin KISA = kirli seri
                    return False, f"TF-aralık ihlali (medyan {med}s < beklenen {exp}s — tick-kirliliği?)"
        # 4) OHLC tutarlılığı
        for i, b in enumerate(bars[-min_bars:]):
            o, h, l, c = b.get("open"), b.get("high"), b.get("low"), b.get("close")
            for v in (h, l, c):
                if v is None or not isinstance(v, (int, float)) or v != v or v <= 0:
                    return False, f"bozuk fiyat (bar {i}: {v!r})"
            if h < l or c > h or c < l or (o is not None and (o > h or o < l)):
                return False, f"OHLC tutarsız (bar {i}: o={o} h={h} l={l} c={c})"
        # 5) flat-line (ölü feed): son N barın hepsi high==low
        tail = bars[-FLAT_N:]
        if len(tail) == FLAT_N and all(b["high"] == b["low"] for b in tail):
            return False, f"flat-line feed (son {FLAT_N} bar high==low — ölü kaynak)"
        return True, "ok"
    except Exception as ex:                     # sözleşme kendisi asla düşürmesin
        return False, f"sözleşme hatası: {ex}"


def validate_multi(bars_by_tf: dict, min_bars: int = MIN_BARS) -> dict:
    """Çok-TF sözlüğünü doğrula → yalnız GEÇERLİ TF'ler kalır; düşenler loglanır."""
    out = {}
    for tf, bars in (bars_by_tf or {}).items():
        ok, why = validate_bars(bars, tf, min_bars)
        if ok:
            out[tf] = bars
        else:
            print(f"  🛡 DataContract: {tf} serisi REDDEDİLDİ — {why}")
    return out


if __name__ == "__main__":
    # kendi-test: her ihlal sınıfı yakalanmalı, temiz seri geçmeli
    import math
    good = [{"open": 100 + math.sin(i / 5), "high": 100.7 + math.sin(i / 5),
             "low": 99.3 + math.sin(i / 5), "close": 100 + math.sin(i / 5),
             "volume": 1000, "time": 1000000 + i * 300} for i in range(60)]
    print("temiz 5m:", validate_bars(good, "5m"))
    bad = [dict(b) for b in good]; bad[30]["time"] = bad[29]["time"]          # duplike zaman
    print("duplike zaman:", validate_bars(bad, "5m"))
    tick = [dict(b, time=1000000 + i * 7) for i, b in enumerate(good)]        # 7s aralık = tick-kirli
    print("tick-kirli '5m':", validate_bars(tick, "5m"))
    ohlc = [dict(b) for b in good]; ohlc[-5]["high"] = ohlc[-5]["low"] - 1    # high<low
    print("OHLC bozuk:", validate_bars(ohlc, "5m"))
    flat = [dict(b, open=100.0, high=100.0, low=100.0, close=100.0) for b in good]   # ölü feed
    print("flat-line:", validate_bars(flat, "5m"))
    nan = [dict(b) for b in good]; nan[-1]["close"] = float("nan")
    print("NaN fiyat:", validate_bars(nan, "5m"))
