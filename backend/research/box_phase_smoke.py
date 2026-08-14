"""box_phase_smoke.py — faz kurallarının kutuda CANLI veriyle duman testi.

SALT-OKUR: emir göndermez, paylaşılan durum dosyalarına (shadow_pending.json,
gate_skipped.jsonl, mgmt_state.json) YAZMAZ. Yalnız gerçek MT5 barlarıyla yeni
kod yollarının ne ürettiğini gösterir:

  * TP = 2.5×ATR70(1m) gerçek NASDAQ barlarında kaç puan ediyor?
  * Zaman pencereleri kapısı şu an ne diyor (bayraklar açık/kapalı)?
  * Dalga konumu + sıkı eşik + 5m RSI şu an ne durumda?
  * Probasyon bandı (1.28×ATR14×√5) kaç puan?
  * Koşullu BE ve zaman stopu kararları örnek değerlerle tutarlı mı?

Çalıştırma (kutuda): python backend/research/box_phase_smoke.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda çalışır.")

import config  # type: ignore
import phase_rules as pr  # type: ignore


class Cfg:
    """Faz-1 açıkmış gibi davranan sahte config (gerçek config'e DOKUNMAZ)."""
    def __init__(self, base, **kw):
        self._b = base
        self._o = kw

    def __getattr__(self, k):
        if k in self._o:
            return self._o[k]
        return getattr(self._b, k)


def bars(sym: str, tf, n: int) -> list[dict]:
    r = mt5.copy_rates_from_pos(sym, tf, 0, n)
    if r is None:
        return []
    return [{"high": float(x["high"]), "low": float(x["low"]),
             "close": float(x["close"])} for x in r]


def main() -> None:
    kw = {}
    if getattr(config, "MT5_ACCOUNT", None):
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
    path = getattr(config, "MT5_TERMINAL_PATH", "")
    ok = mt5.initialize(path, **kw) if path else mt5.initialize(**kw)
    if not ok:
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")

    sym = dict(getattr(config, "SYMBOL_MAP", {})).get("NDX.INDX", "NAS100")
    mt5.symbol_select(sym, True)
    tick = mt5.symbol_info_tick(sym)
    px = (tick.bid + tick.ask) / 2 if tick else 0.0
    now = datetime.now(timezone.utc)
    print(f"sembol={sym} fiyat={px:.1f} zaman(UTC)={now:%Y-%m-%d %H:%M} "
          f"gun={now.isoweekday()}")

    b1 = bars(sym, mt5.TIMEFRAME_M1, 300)
    b5 = bars(sym, mt5.TIMEFRAME_M5, 60)
    print(f"1m bar={len(b1)}  5m bar={len(b5)}")

    print("\n── FAZ 0.3: TP geometrisi ───────────────────────────────────")
    atr70 = pr.atr_simple(b1, 70)
    sl_ref = 110.0                      # botun NDX sabit SL mesafesi
    for scope in ("NDX.INDX:BUY", "NDX.INDX:SELL:VIXREG", "NDX.INDX:BUY:DAYCOMBO"):
        d, src = pr.tp_distance(scope, "NDX.INDX", b1, 80.0, config, sl_dist=sl_ref)
        print(f"  {scope:<28} TP={d:6.1f}pt  RR={d/sl_ref:4.2f}  kaynak={src}")
    if atr70:
        ham = 2.5 * atr70
        print(f"  ATR70(1m)={atr70:.1f}pt → ham TP {ham:.1f}pt (RR {ham/sl_ref:.2f}); "
              f"taban {pr.flag(config, 'TP_ATR_MIN_R')}×SL devrede mi: "
              f"{'EVET' if ham < float(pr.flag(config, 'TP_ATR_MIN_R'))*sl_ref else 'hayır'}")

    print("\n── FAZ 0.1/0.2: yönetim kararları (örnek değerlerle) ────────")
    sl_d = 110.0
    for mfe in (40, 54, 55, 90):
        print(f"  MFE={mfe:3.0f}pt (SL={sl_d:.0f}) → BE {'AÇILIR' if pr.be_should_arm('conditional_mfe', mfe, sl_d, 0, 30) else 'açılmaz'}")
    for age in (119, 239, 241):
        print(f"  yaş={age:3.0f}dk → zaman stopu "
              f"{'ÇALIŞIR' if pr.time_stop_due(age*60, pr.flag(config,'MGMT_TIME_STOP_MIN')) else 'çalışmaz'}")

    print("\n── FAZ 1: zaman pencereleri (bayraklar AÇIKMIŞ gibi) ────────")
    test_cfg = Cfg(config, NDX_SESSION_BLOCK_ENABLED=True, NDX_FRIDAY_BLOCK=True,
                   NDX_WEEKEND_HOLD_BLOCK=True, NDX_SR_ENTRY_ENABLED=False)
    blocked, why = pr.entry_window_block(now, "NDX.INDX", test_cfg)
    print(f"  Faz-1 AÇIK olsaydı şu an: {'BLOK — ' + why if blocked else 'giriş serbest'}")
    b_now, w_now = pr.entry_window_block(now, "NDX.INDX", config)
    print(f"  Gerçek (canlı) bayraklarla: {'BLOK — ' + w_now if b_now else 'giriş serbest'}")
    print(f"  S/R kolu — canlı: {'AÇIK' if pr.sr_entry_allowed('NDX.INDX', config) else 'KAPALI'}"
          f" · Faz-1'de: {'AÇIK' if pr.sr_entry_allowed('NDX.INDX', test_cfg) else 'KAPALI'}")
    print(f"  CONFIRM zorunlu mu (Faz-1.4): canlı={pr.only_confirm_required(config)} "
          f"· config.ONLY_CONFIRM_SIGNALS={getattr(config,'ONLY_CONFIRM_SIGNALS',None)}")

    print("\n── FAZ 2: dalga konumu + RSI (gölge) ────────────────────────")
    pos = pr.wave_position(b5[-48:], px) if len(b5) >= 48 else None
    if pos is None:
        print("  dalga konumu hesaplanamadı")
    else:
        for d in ("BUY", "SELL"):
            mevcut = pr.position_gate_blocks(d, pos, 0.40, 0.60)
            siki = pr.position_gate_blocks(
                d, pos, float(pr.flag(config, "POS_TIGHT_SELL_MIN")),
                float(pr.flag(config, "POS_TIGHT_BUY_MAX")))
            print(f"  konum={pos:.2f} {d:<4} → mevcut kapı: "
                  f"{'BLOK' if mevcut else 'geçer'} · sıkı kapı: "
                  f"{'BLOK' if siki else 'geçer'}")
    r = pr.rsi([x["close"] for x in b5], 14)
    print(f"  5m RSI(14) = {r:.1f} → SELL 'güce sat' kapısı: "
          f"{'geçer' if r and r > float(pr.flag(config,'SELL_RSI_MIN')) else 'geçmez'}"
          if r else "  RSI hesaplanamadı")

    print("\n── FAZ 3: probasyon bandı ───────────────────────────────────")
    atr14 = pr.atr_simple(b1, 14)
    if atr14:
        band = pr.probation_band(atr14, int(pr.flag(config, "PROBATION_BARS")),
                                 float(pr.flag(config, "PROBATION_Z")))
        print(f"  ATR14(1m)={atr14:.1f}pt → 5 barlık gürültü bandı = {band:.1f}pt")
        seg = b1[-5:]
        cancel, adverse, _ = pr.probation_verdict("BUY", b1[-6]["close"], atr14, seg)
        print(f"  (örnek) son 5 barda BUY aleyhine {adverse:.1f}pt → "
              f"{'İPTAL ederdi' if cancel else 'giriş yapardı'}")
    print("\n✅ duman testi tamam — hiçbir emir gönderilmedi, dosya yazılmadı.")
    mt5.shutdown()


if __name__ == "__main__":
    main()
