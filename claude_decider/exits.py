"""
exits.py — Çıkış stratejisi politikaları (her işlemi paralel grade et, en iyiyi öğren).
=============================================================================
Sorun: edge'in yarısı ÇIKIŞTA ama tek sabit TP/SL (1×/1.5×ATR) ile grade ediyoruz;
Opus'un management notu çöpe gidiyor. Bu modül her işlemi 6 farklı çıkışla grade eder.

P&L birimi = ATR (politikalar adil kıyaslanır; ortalama pnl_atr en yüksek = en kârlı çıkış).
Konservatif intrabar: bir mum içinde önce ALEYHTE hareket varsayılır (SL/trail önce) →
trailing/breakeven performansı şişirilmez (ground-truth dürüstlüğü).

Her politika: (direction, entry, atr, bars_after) → (etiket, pnl_atr).
bars_after: [{high,low,close,time}, ...] giriş SONRASI, zaman sıralı, TÜM ileri pencere.
"""
from __future__ import annotations


def _eod(direction: str, entry: float, atr: float, bars: list) -> tuple[str, float]:
    """Hiçbir çıkış tetiklenmedi → son kapanışta çık (pencere sonu)."""
    last = bars[-1]["close"] if bars else entry
    pnl = (last - entry) / atr if direction == "BUY" else (entry - last) / atr
    return "EOD", round(pnl, 3)


def exit_fixed(direction, entry, atr, bars, tp_mult=1.0, sl_mult=1.5):
    """Sabit TP/SL. Çift-değme → SL (konservatif)."""
    buy = direction == "BUY"
    tp = entry + tp_mult * atr if buy else entry - tp_mult * atr
    sl = entry - sl_mult * atr if buy else entry + sl_mult * atr
    for b in bars:
        hit_sl = b["low"] <= sl if buy else b["high"] >= sl
        hit_tp = b["high"] >= tp if buy else b["low"] <= tp
        if hit_sl:
            return "SL", round(-sl_mult, 3)
        if hit_tp:
            return "TP", round(tp_mult, 3)
    return _eod(direction, entry, atr, bars)


def exit_trail(direction, entry, atr, bars, sl_mult=1.5, trail=1.0, activate=1.0):
    """Trailing stop: +activate×ATR kâra geçince stop'u trail×ATR geriden takip et."""
    buy = direction == "BUY"
    sl = entry - sl_mult * atr if buy else entry + sl_mult * atr
    hwm = entry; active = False
    for b in bars:
        # konservatif: önce mevcut SL aleyhte vuruldu mu
        if (b["low"] <= sl) if buy else (b["high"] >= sl):
            pnl = (sl - entry) / atr if buy else (entry - sl) / atr
            return ("TRAIL" if active else "SL"), round(pnl, 3)
        # sonra HWM güncelle + trail
        if buy:
            hwm = max(hwm, b["high"])
            if not active and hwm >= entry + activate * atr:
                active = True
            if active:
                sl = max(sl, hwm - trail * atr)
        else:
            hwm = min(hwm, b["low"])
            if not active and hwm <= entry - activate * atr:
                active = True
            if active:
                sl = min(sl, hwm + trail * atr)
    return _eod(direction, entry, atr, bars)


def exit_breakeven(direction, entry, atr, bars, sl_mult=1.5, be_trigger=1.0, tp_mult=2.0):
    """+be_trigger×ATR'de SL'i girişe (breakeven) taşı, sonra TP tp_mult×ATR'ye koş."""
    buy = direction == "BUY"
    sl = entry - sl_mult * atr if buy else entry + sl_mult * atr
    tp = entry + tp_mult * atr if buy else entry - tp_mult * atr
    moved = False
    for b in bars:
        if (b["low"] <= sl) if buy else (b["high"] >= sl):      # konservatif: SL önce
            pnl = (sl - entry) / atr if buy else (entry - sl) / atr
            return ("BE" if moved else "SL"), round(pnl, 3)
        if (b["high"] >= tp) if buy else (b["low"] <= tp):
            return "TP", round(tp_mult, 3)
        if not moved and ((b["high"] >= entry + be_trigger * atr) if buy else (b["low"] <= entry - be_trigger * atr)):
            sl = entry; moved = True
    return _eod(direction, entry, atr, bars)


def exit_time(direction, entry, atr, bars, sl_mult=1.5, n_bars=24):
    """N mum sonra kapanışta çık (zaman-stop); arada SL korur. 24×5m = 2 saat."""
    buy = direction == "BUY"
    sl = entry - sl_mult * atr if buy else entry + sl_mult * atr
    for i, b in enumerate(bars):
        if (b["low"] <= sl) if buy else (b["high"] >= sl):
            return "SL", round(-sl_mult, 3)
        if i + 1 >= n_bars:
            pnl = (b["close"] - entry) / atr if buy else (entry - b["close"]) / atr
            return "TIME", round(pnl, 3)
    return _eod(direction, entry, atr, bars)


# Politika seti — isim → fonksiyon. 'fixed_1.0/1.5' mevcut varsayılan (baz).
POLICIES = {
    "fixed_1.0/1.5":  lambda d, e, a, b: exit_fixed(d, e, a, b, 1.0, 1.5),   # mevcut default
    "fixed_1.5/1.5":  lambda d, e, a, b: exit_fixed(d, e, a, b, 1.5, 1.5),   # simetrik
    "fixed_2.0/1.5":  lambda d, e, a, b: exit_fixed(d, e, a, b, 2.0, 1.5),   # koşan TP
    "trail_1.0":      lambda d, e, a, b: exit_trail(d, e, a, b, 1.5, 1.0, 1.0),
    "breakeven_tp2":  lambda d, e, a, b: exit_breakeven(d, e, a, b, 1.5, 1.0, 2.0),
    "time_2h":        lambda d, e, a, b: exit_time(d, e, a, b, 1.5, 24),
}
DEFAULT_POLICY = "fixed_1.0/1.5"


def grade_all(direction: str, entry: float, atr: float, bars: list) -> dict:
    """Tüm politikaları grade et → {politika: pnl_atr}. Geçersiz girdi → {}."""
    if not atr or atr <= 0 or not bars:
        return {}
    out = {}
    for name, fn in POLICIES.items():
        try:
            _, pnl = fn(direction, entry, atr, bars)
            out[name] = pnl
        except Exception:
            pass
    return out


if __name__ == "__main__":
    # kendi-test: BUY entry=100, atr=2. Senaryo: yukarı koşar (102→104) → tp2 kazanmalı
    bars_up = [{"high": 101.5, "low": 99.8, "close": 101.0, "time": 1},
               {"high": 103.0, "low": 100.5, "close": 102.5, "time": 2},
               {"high": 105.0, "low": 102.0, "close": 104.5, "time": 3}]
    print("Yukarı koşan (BUY):", grade_all("BUY", 100.0, 2.0, bars_up))
    # Senaryo: önce +1ATR sonra geri döner → breakeven/trail korur, fixed_2 kaybeder
    bars_rev = [{"high": 102.5, "low": 100.0, "close": 102.0, "time": 1},   # +1ATR'yi geçti
                {"high": 102.0, "low": 96.5, "close": 97.0, "time": 2}]      # SL'e döndü
    print("Geri dönen (BUY):", grade_all("BUY", 100.0, 2.0, bars_rev))
