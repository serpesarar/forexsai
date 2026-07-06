"""CORTEX validated confluence rules — the brain's learned playbook.

Human-readable, OOS-validated intraday confluence rules discovered by the
research pipeline (research/cortex_confluence/). Exposed so the debate agents
"know" them as prior evidence. These are NOT auto-executed; they are context +
an optional live evaluator.

Honest calibration is baked into each rule's `note`. NASDAQ rules are validated
on 2019-2024 NQ; other instruments are added as their studies complete.
"""
from __future__ import annotations

from typing import Any, Optional

# Each rule: instrument, side, session (ET decision), horizon, plain conditions,
# out-of-sample hit-rate, coverage, and an honesty note.
CONFLUENCE_RULES: list[dict[str, Any]] = [
    # ── NASDAQ LONG (momentum-persistence, 11:00 ET) ──
    {"id": "NDX_L_rsi_momentum", "instrument": "NDX.INDX", "side": "long",
     "session_et": "11:00", "horizon": "24h", "oos_hit": 0.69, "coverage": 0.11,
     "conditions": "rsi_M30 > 73 (güçlü momentum)",
     "note": "OOS 2023-24 %69, 2022 ayıda bile %71. NDX momentum devam eder, dönmez."},
    {"id": "NDX_L_full_alignment", "instrument": "NDX.INDX", "side": "long",
     "session_et": "11:00", "horizon": "6h/24h", "oos_hit": 0.78, "coverage": 0.06,
     "conditions": "bull_score ≥ 11/12 (neredeyse tüm göstergeler hizalı) VE tüm-TF momentum yukarı VE kısa-vade RSI güçlü",
     "note": "En güçlü long. TEST %75-78, her yıl (2022 dahil). Tam çakışma = yüksek güven."},
    {"id": "NDX_L_price_ext", "instrument": "NDX.INDX", "side": "long",
     "session_et": "11:00", "horizon": "24h", "oos_hit": 0.62, "coverage": 0.23,
     "conditions": "fiyat, M30 EMA20'nin %0.38+ üstünde",
     "note": "Yüksek kapsam (%23), TEST %62. Trend-sağlam filtresi."},
    # ── NASDAQ SHORT (stress-gated breakdown, 10:00 ET) ──
    {"id": "NDX_S_stress_mom", "instrument": "NDX.INDX", "side": "short",
     "session_et": "10:00", "horizon": "6h", "oos_hit": 0.57, "coverage": 0.13,
     "conditions": "ret1_H1 < 0 VE fiyat < EMA20_H1 VE VIX ≥ ELEVATED (≥20)",
     "note": "NDX short TAVANI ~%57-59, sadece stres rejiminde. Sakin piyasada short çalışmaz."},
    {"id": "NDX_S_stress_rates", "instrument": "NDX.INDX", "side": "short",
     "session_et": "10:00", "horizon": "6h", "oos_hit": 0.59, "coverage": 0.07,
     "conditions": "ret6_M30 < 0 VE VIX ≥ ELEVATED VE US10Y yükseliyor (prior-day)",
     "note": "Stres + faiz baskısı + aşağı momentum. NDX'te %70 short OOS'ta İMKÂNSIZ (kanıtlı)."},
    # NOT: Gold/DAX/USOIL kuralları cortex_confluence_rules.JSON'dan gelir (sızıntısız,
    # prior-day makro, PRELIMINARY). Eski "çift-makro %89" gold kuralları 2026-07-04'te
    # SİLİNDİ — same-day makro LOOK-AHEAD SIZINTISI idi (sızıntısız ~%47). NDX kuralları
    # prior-day makro ile hesaplandığı için sızıntısız ve geçerli kalır.
]


def rules_for(instrument: str, side: Optional[str] = None) -> list[dict]:
    return [r for r in all_rules()
            if r["instrument"] == instrument and (side is None or r["side"] == side)]


TOP_PER_INSTRUMENT = 5

def rules_prompt_block(instrument: str = "NDX.INDX") -> str:
    """Concise validated-playbook text for the debate CIO (prior evidence)."""
    rs = sorted(rules_for(instrument),
                key=lambda r: -(r.get("oos_hit", 0) * (r.get("coverage", 0) + 0.03)))[:TOP_PER_INSTRUMENT]
    if not rs:
        return ""
    lines = ["VALIDATED CONFLUENCE PLAYBOOK (OOS-tested historical rules — prior "
             "evidence, not auto-signals):"]
    for r in rs:
        lines.append(
            f"- [{r['side'].upper()} · {r['session_et']} ET · {r['horizon']}] "
            f"{r['conditions']} → %{int(r['oos_hit']*100)} isabet (kapsam %{int(r['coverage']*100)})")
    lines.append("Equity indices (NDX/DAX): long-heavy, short structurally weak. "
                 "Gold: two-sided, DXY/US10Y-driven. Weigh as base rates, not auto-signals.")
    return "\n".join(lines)


# ── Auto-discovered rules (≥70% OOS) persisted by the research pipeline ────────
import json as _json, os as _os
_DISCOVERED_PATH = _os.path.join(_os.path.dirname(__file__), "cortex_confluence_rules.json")

def load_discovered() -> list:
    try:
        with open(_DISCOVERED_PATH) as fh:
            return _json.load(fh)
    except Exception:
        return []

def all_rules() -> list:
    return CONFLUENCE_RULES + load_discovered()
