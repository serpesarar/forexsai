"""Tartışma motoru için KANITLANMIŞ kanıt blokları (2026-07-26).

Neden: `bias_debate_engine` ajanlara formasyon dedektörünün çıktısını "kanıt"
diye veriyordu ama o dedektörün GERÇEKTE tutup tutmadığını söylemiyordu.
`shadow_trade_tracker` aylardır sızıntısız kâğıt-işlem ölçümü yapıyor ve
verdiği hüküm sert:

    formasyon kaynaklı SELL sinyalleri:  26/115 = %22.6  (p ≈ 3e-9)
    formasyon kaynaklı BUY sinyalleri:   62/124 = %50.0  (p = 1.0)

Yani "ayı formasyonu" bir ayı kanıtı DEĞİL — istatistiksel olarak KARŞIT
kanıt. Bu bilgi tartışmaya girmediği için ajanlar ayı formasyonlarını
gerekçe gösterip ayı yanlılığını besliyordu (25 ayı / 7 boğa, p=0.002).

Bu modül iki blok üretir:
  * ``shadow_prompt_block``  — canlı sızıntısız karne + veriden TÜRETİLMİŞ direktif
  * ``fakeout_prompt_block`` — OOS doğrulanmış sahte-kırılım dedektörünün canlı çağrısı

Tasarım ilkesi: direktifler SABİT KODLANMAZ, her çağrıda veriden hesaplanır.
Formasyon SELL'i yarın düzelirse blok kendiliğinden değişir. Örneklem yetersizse
(n < eşik) veya sonuç anlamlı değilse hiçbir direktif üretilmez — gürültüyü
"kanıt" diye enjekte etmek, hiç enjekte etmemekten kötüdür.

Hepsi fail-open: DB/servis yoksa boş string döner, tartışma eskisi gibi koşar.
"""
from __future__ import annotations

import logging
import math
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

#: Karne sorgusu penceresi (gün) ve önbellek ömrü (sn). Tartışma günde birkaç
#: kez koşar; karne saatlik değişmez.
_LOOKBACK_DAYS = 60
_CACHE_TTL_SECONDS = 1800
_cache: dict[str, tuple[float, str]] = {}

#: Direktif üretmek için asgari örneklem ve anlamlılık eşikleri. Global tablo
#: daha katı (çok hücre taranıyor), sembol kırılımı biraz gevşek.
_MIN_N_GLOBAL, _MAX_P_GLOBAL = 30, 0.01
_MIN_N_SYMBOL, _MAX_P_SYMBOL = 20, 0.05
#: Karşıt/geçerli kanıt sayılma eşikleri (%).
_CONTRARIAN_WR, _VALIDATED_WR = 40.0, 60.0


def _two_sided_p(wins: int, n: int) -> float:
    """H0: p=0.5 altında iki-yönlü binom p-değeri (normal yaklaşım).

    n≥30'da scipy'nin tam binom testiyle 3 anlamlı basamağa kadar uyuşur
    (26/115 → 3.3e-9 vs tam 2.95e-9); runtime'da scipy'ye bağımlılık yaratmamak
    için tercih edildi.
    """
    if n <= 0:
        return 1.0
    z = (wins - n / 2.0) / (math.sqrt(n) / 2.0)
    return math.erfc(abs(z) / math.sqrt(2.0))


def _agg(rows: list[dict]) -> Optional[dict]:
    """Çözülmüş (win/loss) satırlardan isabet + anlamlılık."""
    res = [r for r in rows if r.get("status") in ("win", "loss")]
    if not res:
        return None
    wins = sum(1 for r in res if r["status"] == "win")
    n = len(res)
    return {"n": n, "wins": wins, "wr": round(100.0 * wins / n, 1),
            "p": _two_sided_p(wins, n)}


def _verdict(stat: dict, min_n: int, max_p: float) -> Optional[str]:
    """İstatistikten direktif üret — yalnız yeterli ve anlamlıysa."""
    if stat["n"] < min_n or stat["p"] > max_p:
        return None
    if stat["wr"] < _CONTRARIAN_WR:
        return "CONTRARIAN"
    if stat["wr"] > _VALIDATED_WR:
        return "VALIDATED"
    return None


def _fetch_rows() -> list[dict]:
    from datetime import datetime, timedelta, timezone
    from services.shadow_trade_tracker import TABLE, _db
    client = _db()
    if client is None:
        return []
    since = (datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)).isoformat()
    res = (client.table(TABLE).select("source,symbol,direction,status")
           .gte("created_at", since).limit(4000).execute())
    return (res.get("data") or []) if not res.get("error") else []


def shadow_prompt_block(symbol: str) -> str:
    """Canlı sızıntısız dedektör karnesi + veriden türetilmiş direktifler.

    Args:
        symbol: Tartışılan sembol; bloğa hem GLOBAL hem bu sembolün kırılımı girer.

    Returns:
        Prompt bloğu; veri/DB yoksa veya hiç çözülmüş işlem yoksa ``""``.
    """
    key = f"shadow:{symbol}"
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < _CACHE_TTL_SECONDS:
        return hit[1]
    try:
        rows = _fetch_rows()
        if not rows:
            return ""
        lines: list[str] = []
        directives: list[str] = []

        for source in ("pattern", "fakeout", "meta"):
            src_rows = [r for r in rows if r.get("source") == source]
            if not src_rows:
                continue
            parts: list[str] = []
            for direction in ("BUY", "SELL"):
                g = _agg([r for r in src_rows if r.get("direction") == direction])
                if not g:
                    continue
                parts.append(f"{direction} {g['wins']}/{g['n']} ({g['wr']}%)")
                v = _verdict(g, _MIN_N_GLOBAL, _MAX_P_GLOBAL)
                if v == "CONTRARIAN":
                    lean = "bearish" if direction == "SELL" else "bullish"
                    directives.append(
                        f"'{source}' {direction} signals hit only {g['wr']}% "
                        f"(n={g['n']}, p={g['p']:.0e}). A {direction} signal from "
                        f"'{source}' is therefore NOT {lean} evidence — it is "
                        f"statistically CONTRARIAN evidence. Do NOT cite it to "
                        f"support a {lean} verdict; if anything it weakly favours "
                        f"the opposite side.")
                elif v == "VALIDATED":
                    directives.append(
                        f"'{source}' {direction} signals hit {g['wr']}% "
                        f"(n={g['n']}, p={g['p']:.0e}) — a validated edge; weigh "
                        f"it as strong evidence.")
            if parts:
                lines.append(f"  {source:8s} → " + " | ".join(parts))

            # Bu sembole özel kırılım (global tablodan ayrışıyorsa değerlidir)
            for direction in ("BUY", "SELL"):
                s = _agg([r for r in src_rows if r.get("symbol") == symbol
                          and r.get("direction") == direction])
                if not s:
                    continue
                v = _verdict(s, _MIN_N_SYMBOL, _MAX_P_SYMBOL)
                if v == "CONTRARIAN":
                    directives.append(
                        f"On {symbol} specifically, '{source}' {direction} signals "
                        f"hit {s['wr']}% (n={s['n']}) — do NOT use this source in "
                        f"this direction for this symbol.")
                elif v == "VALIDATED":
                    directives.append(
                        f"On {symbol} specifically, '{source}' {direction} signals "
                        f"hit {s['wr']}% (n={s['n']}) — strong evidence for this symbol.")

        if not lines:
            return ""
        block = ("LIVE DETECTOR SCORECARD (shadow_trade_tracker — leak-free forward "
                 f"paper trades, last {_LOOKBACK_DAYS} days; entry = last CLOSED 5m bar "
                 "at decision time, resolved only on LATER bars):\n"
                 + "\n".join(lines))
        if directives:
            block += ("\n\nWHAT THIS MEANS (computed from the numbers above, not "
                      "assumed):\n" + "\n".join(f"  - {d}" for d in directives))
        _cache[key] = (time.monotonic(), block)
        return block
    except Exception as e:
        logger.debug("[debate-evidence] shadow scorecard skipped: %s", e)
        return ""


async def fakeout_prompt_block(symbol: str) -> str:
    """OOS doğrulanmış sahte-kırılım dedektörünün ŞU ANKİ çağrısı.

    Dedektör 4 sembolde de kronolojik OOS testinde %70+ isabet tutturdu ve
    deploy edilen artefakt test edilenin ta kendisi (bkz. CLAUDE.md Fakeout
    Radar). Tartışmaya hiç bağlı değildi — sistemin en sıkı doğrulanmış
    bileşeni prompt'ta yoktu.
    """
    try:
        from services.fakeout_service import assess_symbol
        r = await assess_symbol(symbol)
        status = r.get("status")
        if status == "no_breakout":
            pf = r.get("pre_forecast") or {}
            if not pf:
                return ""
            return ("FAKEOUT DETECTOR (OOS-validated, 4/4 symbols ≥70% on held-out "
                    "test): no fresh S/R or channel breakout right now. "
                    f"Pre-breakout forecast if one happens: {pf}")
        if status != "assessed":
            return ""
        det = r.get("detector") or {}
        bo = r.get("breakout") or {}
        # Eksik kırılım/dedektör → blok üretme. Null dolu satırları prompt'a
        # yazmaktansa hiç yazmamak doğru: LLM "None @ None" gördüğünde onu
        # yine de gerekçeye çevirmeye çalışır.
        if not det.get("call") or bo.get("level_price") is None:
            return ""
        call, stage = det.get("call"), det.get("stage")
        oos = det.get("oos") or {}
        head = ("FAKEOUT DETECTOR (OOS-validated LightGBM; the deployed artifact IS "
                "the tested one — this system's most rigorously validated component):")
        side = "UP" if bo.get("direction", 0) > 0 else "DOWN"
        lines = [
            f"  fresh breakout: {side} through {bo.get('level_kind')} @ "
            f"{bo.get('level_price')} ({bo.get('touches')} touches, "
            f"{bo.get('age_bars')} bars old)",
            f"  detector call: {call!r} (stage {stage}, p_fake {det.get('p_fake')}%)",
            f"  combined fake probability: {r.get('fake_probability')}% "
            f"(base rate {r.get('base_fake_rate')}%)",
            f"  recommendation: {r.get('recommendation')}",
        ]
        if oos:
            lines.append(f"  detector OOS record: {oos}")
        if call == "fake":
            lines.append("  → A 'fake' call is FADE evidence: the breakout is "
                         "expected to fail, favouring the direction OPPOSITE the "
                         "breakout. Do NOT cite this breakout as trend evidence.")
        elif call == "genuine":
            lines.append(f"  → A 'genuine' call supports continuation {side}.")
        else:
            lines.append("  → Detector abstains; treat the breakout as unresolved.")
        return head + "\n" + "\n".join(lines)
    except Exception as e:
        logger.debug("[debate-evidence] fakeout block skipped for %s: %s", symbol, e)
        return ""
