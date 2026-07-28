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


def exit_be30_runner(direction, entry, atr, bars, sl_mult=1.5, be_bars=6, tp_mult=1.0, trail_r=0.6):
    """ÖLÇÜLMÜŞ NDX BUY yönetimi (trade-mgmt-be30-runner-2026-07: 223 gerçek işlem, 1m
    sızıntısız replay, Δ+29.5R [16.4,43.5] P=%100; TP olan işlemler TP sonrası medyan +1.42R
    devam ediyor): girişten be_bars×5m (~30dk) sonra kârdaysa SL→girişe (BE); TP'ye VARINCA
    TP KALDIRILIR ve HWM−trail_r×R iz süren stopla koşturulur (R = sl_mult×ATR).
    YALNIZ BUY — SELL pozisyonuna BE/trail aynı araştırmada Δ−7.5R ölçüldü → SELL'de None
    (grade edilmez; havuz istatistiğini kirletmesin). Konservatif intrabar: önce SL/trail."""
    if str(direction).upper() != "BUY":
        return None
    sl = entry - sl_mult * atr
    tp = entry + tp_mult * atr
    trail_dist = trail_r * sl_mult * atr      # 0.6R (sl1.5'te 0.9×ATR)
    hwm, runner, moved_be = entry, False, False
    for i, b in enumerate(bars):
        if b["low"] <= sl:                    # konservatif: önce stop
            pnl = (sl - entry) / atr
            return ("TRAIL" if runner else "BE" if moved_be else "SL"), round(pnl, 3)
        if not runner and b["high"] >= tp:
            runner = True                     # TP kaldırıldı — kazananı koştur
        if runner:
            hwm = max(hwm, b["high"])
            sl = max(sl, hwm - trail_dist)
        if not moved_be and i + 1 >= be_bars and b["close"] > entry:
            sl = max(sl, entry); moved_be = True   # BE@30dk (yalnız kârdayken)
    return _eod(direction, entry, atr, bars)


# Politika seti — isim → fonksiyon. 'fixed_1.0/1.5' mevcut varsayılan (baz).
POLICIES = {
    "fixed_1.0/1.5":  lambda d, e, a, b: exit_fixed(d, e, a, b, 1.0, 1.5),   # mevcut default
    "fixed_1.5/1.5":  lambda d, e, a, b: exit_fixed(d, e, a, b, 1.5, 1.5),   # simetrik
    "fixed_2.0/1.5":  lambda d, e, a, b: exit_fixed(d, e, a, b, 2.0, 1.5),   # koşan TP
    "trail_1.0":      lambda d, e, a, b: exit_trail(d, e, a, b, 1.5, 1.0, 1.0),
    "breakeven_tp2":  lambda d, e, a, b: exit_breakeven(d, e, a, b, 1.5, 1.0, 2.0),
    "time_2h":        lambda d, e, a, b: exit_time(d, e, a, b, 1.5, 24),
    "be30_runner":    lambda d, e, a, b: exit_be30_runner(d, e, a, b),       # yalnız BUY (SELL→None)
}
DEFAULT_POLICY = "fixed_1.0/1.5"

# Sembol-özel ek politikalar (2026-07-27 denetimi): XAU'nun o günkü CANLI geometrisi (1.0/2.5)
# eski sette HİÇ yoktu (hepsi sl=1.5) → exit_compare yanlış bazla kıyaslıyordu ve 2.5 katsayısı
# kendini asla doğrulayamıyordu. Ölçüm yapılınca (2026-07-28) 2.5 ELENDİ ve XAU ev varsayılanına
# döndü; sl2.5 varyantları kıyas setinde KALIYOR — dönüşün yanlış olup olmadığı ancak onlar
# ölçülmeye devam ederse görülür. fixed_0.75/1.0 = XAU fakeout dedektörünün OOS geometrisi.
XAU_POLICIES = {
    "fixed_1.0/2.5":        lambda d, e, a, b: exit_fixed(d, e, a, b, 1.0, 2.5),   # canlı XAU bazı
    "fixed_0.75/1.0":       lambda d, e, a, b: exit_fixed(d, e, a, b, 0.75, 1.0),  # dedektör geometrisi
    "fixed_1.5/2.5":        lambda d, e, a, b: exit_fixed(d, e, a, b, 1.5, 2.5),
    "trail_1.0/sl2.5":      lambda d, e, a, b: exit_trail(d, e, a, b, 2.5, 1.0, 1.0),
    "breakeven_tp2/sl2.5":  lambda d, e, a, b: exit_breakeven(d, e, a, b, 2.5, 1.0, 2.0),
}


def policies_for(symbol: str | None = None) -> dict:
    """Sembolün grade edileceği politika seti (temel + sembol-özel varyantlar)."""
    if symbol == "XAUUSD":
        return {**POLICIES, **XAU_POLICIES}
    return POLICIES


def baseline_for(symbol: str | None = None) -> str:
    """exit_compare kıyas bazı = sembolün CANLI geometrisi. decide.stop_mults'tan TÜRETİLİR —
    sabit yazılırsa geometri değişince kıyas yanlış baza kayar (2026-07-28 XAU dersi)."""
    try:
        from decide import stop_mults
        tp, sl = stop_mults(symbol)
        name = f"fixed_{tp:g}/{sl:g}"
        if name in policies_for(symbol):
            return name
    except Exception:
        pass
    return DEFAULT_POLICY


def grade_all(direction: str, entry: float, atr: float, bars: list,
              symbol: str | None = None) -> dict:
    """Tüm politikaları grade et → {politika: pnl_atr}. Geçersiz girdi → {}.
    Yön-kapsamlı politikalar (be30_runner SELL'de) None döner → atlanır."""
    if not atr or atr <= 0 or not bars:
        return {}
    out = {}
    for name, fn in policies_for(symbol).items():
        try:
            res = fn(direction, entry, atr, bars)
            if res is not None:
                out[name] = res[1]
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
