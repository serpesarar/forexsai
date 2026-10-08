"""Kanıt kuralları — decider'ın "makul hikâyeyle" çiğnediği, başka yerde kanıtlanmış kurallar.

Karardan SONRA mekanik uygulanır (regime_meter.vix_sell_gate ile aynı kalıp). Engellenen karar
WAIT'e döner ama karşı-olgu (counterfactual) engellenen yöne ayarlanır → engellemenin bedeli/
faydası journal'da notlanmaya devam eder (kapı haklı mıydı ölçülebilir).

Kaynak: research/decider_kural_20261008/SONUC.md, defter D4/D5 (2026-10-08).
  D4 — VIX < 18,4 (VIX rejimi NDX için SELL'i destekliyor) iken NDX BUY açma.
       Decider: NDX BUY'ların 44/45'i bu durumda, ort −0,13R. Bağımsız kanıt: K1 VIX_REGIME_GATE
       (A, 10 yıl, plasebo p=0), bot+panelde zaten AKTİF. VIX okunamazsa fail-open.
  D5 — USOIL SELL açma. Decider: −0,13R (88 bağımsız), açmadığı USOIL SELL'ler +0,04R.
       Bağımsız kanıt: bot B1 (USOIL SELL 47 işlem −21,7R, AKTİF).

EVIDENCE_RULES_MODE: block (varsayılan) | shadow (yalnız logla) | off.
"""
from __future__ import annotations

import os

MODE = os.getenv("EVIDENCE_RULES_MODE", "block").lower()
VIX_REGIME_THRESHOLD = 18.4


def _rule(symbol: str, direction: str, situation: dict) -> dict | None:
    if symbol == "NDX.INDX" and direction == "BUY":
        vix = situation.get("vix") or {}
        if vix.get("favored_ndx") == "SELL" and vix.get("fresh"):
            return {"kural": "D4_vix_ndx_buy", "vix": vix.get("value"), "esik": VIX_REGIME_THRESHOLD,
                    "kanit": "decider NDX BUY VIX<18,4: 44/45, ort −0,13R; K1 (A) ile aynı yön"}
    if symbol == "USOIL.FOREX" and direction == "SELL":
        return {"kural": "D5_usoil_sell", "kanit": "decider USOIL SELL −0,13R (n=88) vs açmadığı +0,04R; bot B1"}
    return None


def apply(symbol: str, dec: dict, situation: dict) -> tuple[dict, dict | None]:
    """(karar, tetik bilgisi|None). shadow/off modda karar DEĞİŞMEZ."""
    if MODE == "off" or str(dec.get("action", "")).upper() != "OPEN":
        return dec, None
    direction = str(dec.get("direction") or "").upper()
    info = _rule(symbol, direction, situation)
    if info is None:
        return dec, None
    info["yon"] = direction
    if MODE != "block":
        info["would_block"] = True
        print(f"  👁 kanıt kuralı (GÖLGE): {symbol} {direction} — {info['kural']}")
        return dec, info
    print(f"  🛑 kanıt kuralı: {symbol} {direction} OPEN → WAIT ({info['kural']})")
    situation["primary_dir"] = direction          # karşı-olgu = engellenen işlem (bedeli ölçülsün)
    info["blocked"] = True
    dec = dict(dec)
    dec["action"] = "WAIT"
    dec["size_factor"] = 0.0
    dec["evidence_rule_blocked"] = info["kural"]
    dec["reason"] = (f"[KANIT KURALI {info['kural']}: {info['kanit']}] " + str(dec.get("reason") or ""))[:500]
    return dec, info
