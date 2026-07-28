"""fakeout_bridge.py — backend sahte-kırılım radarının decider köprüsü.

backend/services/fakeout_service.assess_bars SAF çekirdeğini decider'ın kendi
MT5 barlarıyla çağırır (backend HTTP'sine bağımlılık yok). Kurallar sembol-başına
çözülür (fakeout_service._rules_path_for): NDX legacy `fakeout_rules.json`,
diğerleri `fakeout_rules_<BASE>.json` — 4 sembol de destekli (NDX/GDAXI/XAU/USOIL,
hepsi OOS ≥%70). Kural dosyası olmayan sembolde çekirdek "no_rules" → None.
Dönüşteki `detector.oos` sembolün KENDİ isabet/kapsamını taşır; prompt metni
bunu okur (decide._fakeout_stats_line) — sabit NDX rakamı YAZILMAZ.

Neden ayrı 400-bar çekim: run_decider BARS_N=120 bar kullanır; fakeout
çekirdeği ≥125 bar ister (kanal penceresi 96 + pivot teyidi 24). Mevcut
evidence hesaplarını etkilememek için fakeout kendi çekimini yapar (MT5 lokal,
maliyet ihmal edilir).

Fail-open: her hata None döner — situation'a gürültü taşınmaz, karar akışı
asla bloklanmaz.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent / "backend"

_FAKEOUT_BARS_N = 400
_MIN_BARS = 130


def fakeout_context(sym_map: dict[str, str], fx_sym: str) -> dict | None:
    """Sembol için taze kırılım değerlendirmesi; ilginç değilse None.

    Args:
        sym_map: iç ad → broker sembolü eşlemesi (run_decider._SYM_MAP).
        fx_sym: iç sembol adı (örn. "NDX.INDX").
    """
    try:
        import MetaTrader5 as mt5
        mt5_sym = sym_map.get(fx_sym)
        if not mt5_sym:
            return None
        # pos=1: forming bar atlanır — dedektör yalnız KAPANMIŞ barlarla
        # doğrulandı (2026-07-20 denetim; broker-saatli barda duvar-saati
        # filtresi çalışmadığı için kaynakta dışlanır).
        rates = mt5.copy_rates_from_pos(mt5_sym, mt5.TIMEFRAME_M5, 1, _FAKEOUT_BARS_N)
        if rates is None or len(rates) < _MIN_BARS:
            return None
        bars = [{"open": float(r["open"]), "high": float(r["high"]),
                 "low": float(r["low"]), "close": float(r["close"]),
                 "volume": float(r["tick_volume"]), "time": int(r["time"])}
                for r in rates]

        if str(_BACKEND) not in sys.path:
            sys.path.append(str(_BACKEND))     # append: decider modüllerini gölgeleme
        from services.fakeout_service import assess_bars

        fk = assess_bars(bars, symbol=fx_sym)
        if fk.get("status") != "assessed":
            return None
        return {k: fk[k] for k in ("breakout", "fake_probability", "verdict",
                                   "breakout_score", "genuine_probability",
                                   "recommendation", "detector", "confirmation",
                                   "matched_rules", "base_fake_rate", "note") if k in fk}
    except Exception:
        return None
