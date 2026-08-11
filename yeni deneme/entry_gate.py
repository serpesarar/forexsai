"""
entry_gate.py — 8 koşullu giriş skoru + seans saat kapıları (BOT-YEREL).

Kaynak: analiz_paketi_2026-07-09/RAPOR_MT5_ISLEM_OTOPSISI.md §5, §6, §9.
14 günlük GERÇEK MT5 otopsisi: NDX skor≥7 → WR %60→%65, USOIL skor≥7 → WR %49→%72;
skor kapısının bloklayacağı işlemlerin toplam PnL'i her iki sembolde de negatif.

Backend'deki services/signal_gates.py aynı mantığı 5m veriyle (1m stream yok)
yaklaşık uygular. Bot MT5'ten GERÇEK 1m çektiği için burada eşikler analizdeki
ORİJİNAL 1m-ATR tabanıyla hesaplanır — en yüksek sadakat.

Uygulama kapsamı (analiz kararı):
  - VIXREG (NDX) ve MOM/SR momentum scope'ları (NDX/USOIL) → skor kapısı UYGULANIR.
  - CHREV (mean-reversion) → UYGULANMAZ (doğası karşı-trend; TP'leri de düşük skorlu).
  - VIXREG'e EK mikro-yapı kapısı: fiyat EMA200(1m) üstündeyken SELL açma
    (otopsi: 24 işlem −1.800$, WR %50 vs altında %66) + taze ralli ortasında erteleme.

Tüm kapılar FAIL-OPEN: veri yetersiz/hatalıysa BLOKLAMAZ (mevcut kapı felsefesi).
"""
from __future__ import annotations

import numpy as np

from indicators import _ema, _atr, _adx  # DRY: botun kanıtlanmış gösterge tabanı

# ─── Sabitler (config yoksa güvenli varsayılan) ─────────────────────────────

# UTC saat blokları — otopsi §5: NDX {3,4,18,22} ΔPnL +5.078; USOIL 00-11 +1.868.
DEFAULT_SESSION_BLOCK_HOURS_UTC = {
    "NDX.INDX": frozenset({3, 4, 18, 22}),
    "USOIL.FOREX": frozenset(range(0, 12)),
}
DEFAULT_SCORE_SYMBOLS = frozenset({"NDX.INDX", "USOIL.FOREX"})
DEFAULT_MIN_SCORE = 7

# 1m-ATR tabanlı eşikler (otopsi §6 orijinal tanımları):
_MOM60_MIN_ATR = -1.0    # 1h (60×1m) yön-momentum > −1.0·ATR1m
_RUN30_MIN_ATR = -1.5    # son 30dk (30×1m) run > −1.5·ATR1m (bıçak-yakalama değil)
_ADX_MIN = 20.0
_VOL_RATIO_MAX = 1.5
# VIXREG mikro-yapı: taze ralli erteleme eşiği (yön-işaretli run30, ATR1m).
_VIX_RALLY_DEFER_ATR = 1.5


def _sig(direction: str) -> float:
    return 1.0 if direction == "BUY" else -1.0


def compute_entry_score(
    fx_symbol: str,
    direction: str,
    c1m: list[dict] | None,
    c5m: list[dict] | None,
    c30m: list[dict] | None,
    hour_utc: int,
    session_block_hours: dict | None = None,
) -> tuple[int, list[str]]:
    """8 koşullu giriş skoru (saf/senkron çekirdek, test edilebilir).

    Her koşul veri yetersizliğinde SAĞLANMIŞ sayılır (fail-open). Dönen liste
    yalnızca İHLAL edilen koşulların adlarıdır; skor = 8 − ihlal sayısı.

    Mumlar kronolojik (eski→yeni), botun candles_tf() formatı:
    {"high","low","close","volume"}.
    """
    sgn = _sig(direction)
    fails: list[str] = []
    blk = (session_block_hours or DEFAULT_SESSION_BLOCK_HOURS_UTC).get(fx_symbol) or frozenset()

    # 1) saat penceresi
    if hour_utc in blk:
        fails.append("saat_penceresi")

    # ── 1m tabanlı koşullar ──
    if c1m and len(c1m) >= 61:
        c = np.array([b["close"] for b in c1m], float)
        h = np.array([b["high"] for b in c1m], float)
        l = np.array([b["low"] for b in c1m], float)
        v = np.array([b.get("volume", 0.0) for b in c1m], float)
        last = c[-1]
        atr1 = _atr(h, l, c, 14)

        # 4) EMA200 doğru tarafta (1m)
        ema200 = _ema(c, 200)[-1] if len(c) >= 200 else _ema(c, len(c))[-1]
        if sgn * (last - ema200) <= 0:
            fails.append("ema200_tarafi")

        # 5b) ADX(1m) ≥ 20
        adx1, _, _ = _adx(h, l, c, 14)
        if adx1 < _ADX_MIN:
            fails.append("adx_dusuk")

        # 6) hacim sakin: son 1m hacmi / 60-bar ortalaması < 1.5
        base = v[-61:-1].mean()
        if base > 0 and v[-1] / base >= _VOL_RATIO_MAX:
            fails.append("hacim_patlamasi")

        # 7) 1h momentum lehte (60×1m, ATR1 ölçekli)
        if atr1 > 0 and sgn * (last - c[-61]) / atr1 <= _MOM60_MIN_ATR:
            fails.append("1h_karsi_momentum")

        # 8) bıçak yakalama değil (30×1m)
        if atr1 > 0 and sgn * (last - c[-31]) / atr1 <= _RUN30_MIN_ATR:
            fails.append("bicak_yakalama")

    # 5) 5m trend hizası (close vs EMA50)
    if c5m and len(c5m) >= 50:
        c5 = np.array([b["close"] for b in c5m], float)
        if sgn * (c5[-1] - _ema(c5, 50)[-1]) <= 0:
            fails.append("5m_trend")

    # 3) 30m trend hizası
    if c30m and len(c30m) >= 50:
        c30 = np.array([b["close"] for b in c30m], float)
        if sgn * (c30[-1] - _ema(c30, 50)[-1]) <= 0:
            fails.append("30m_trend")

    return 8 - len(fails), fails


def entry_score_ok(
    fx_symbol: str,
    direction: str,
    c1m: list[dict] | None,
    c5m: list[dict] | None,
    c30m: list[dict] | None,
    hour_utc: int,
    min_score: int = DEFAULT_MIN_SCORE,
    score_symbols: frozenset | set | None = None,
    session_block_hours: dict | None = None,
) -> tuple[bool, str, int]:
    """Skor kapısı kararı. Kapsam dışı sembolde her zaman geçer.

    Returns:
        (ok, reason, score): ok=False ise reason blok açıklamasıdır.
    """
    syms = score_symbols if score_symbols is not None else DEFAULT_SCORE_SYMBOLS
    if fx_symbol not in syms:
        return True, "", 8
    score, fails = compute_entry_score(
        fx_symbol, direction, c1m, c5m, c30m, hour_utc,
        session_block_hours=session_block_hours,
    )
    if score < min_score:
        return False, f"giriş skoru {score}/8 < {min_score} (ihlal: {','.join(fails)})", score
    return True, "", score


def vix_regime_micro_ok(
    direction: str,
    c1m: list[dict] | None,
    rally_defer_atr: float = _VIX_RALLY_DEFER_ATR,
) -> tuple[bool, str]:
    """VIXREG'e ÖZEL mikro-yapı kapısı (NDX).

    Otopsi §9.2: VIXREG makro yön verir ama gün-içi yapıyı kontrol etmez.
      - Fiyat EMA200(1m) ÜSTÜNDEyken SELL: WR %50, −1.800$ (altında %66, +4.078).
        → EMA200 üstünde SELL BLOK, EMA200 altında BUY BLOK (karşı-rejim).
      - Taze ralli ortasında (yön-karşıtı run30 büyük) giriş ertele.
    Fail-open: 1m veri yoksa geçer.
    """
    if not c1m or len(c1m) < 31:
        return True, ""
    c = np.array([b["close"] for b in c1m], float)
    h = np.array([b["high"] for b in c1m], float)
    l = np.array([b["low"] for b in c1m], float)
    last = c[-1]
    ema200 = _ema(c, 200)[-1] if len(c) >= 200 else _ema(c, len(c))[-1]
    sgn = _sig(direction)

    # rejim uyumu: SELL yalnız EMA200 ALTINDA, BUY yalnız EMA200 ÜSTÜNDE serbest.
    # aligned = sgn*(last-ema200) > 0 (otopsi above_ema200_s feature'ı); < 0 → karşı-rejim.
    if sgn * (last - ema200) < 0:
        yon = "EMA200 üstünde SELL" if direction == "SELL" else "EMA200 altında BUY"
        return False, f"VIXREG mikro: {yon} (karşı-rejim; otopsi WR %50) — blok"

    # taze ralli/düşüş ortasında girme (yön-karşıtı 30dk run büyükse ertele)
    atr1 = _atr(h, l, c, 14)
    if atr1 > 0:
        run30 = sgn * (last - c[-31]) / atr1
        if run30 < -rally_defer_atr:
            return False, (
                f"VIXREG mikro: taze karşı-hareket ortası (run30={run30:.1f}·ATR "
                f"< −{rally_defer_atr}) — giriş ertelendi"
            )
    return True, ""
