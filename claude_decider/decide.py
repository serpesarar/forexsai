"""
decide.py — Opus'un KANIT-TEMELLİ ÖZERK karar katmanı (Pro headless, API maliyeti yok).
=============================================================================
ROL: Opus sabit bir adayı yargılamaz — sembolün canlı durumu + benzer geçmiş kurulumların
GERÇEK WR kanıtından (evidence.py) KENDİ görüşünü oluşturur (aç/bekle, yön, boyut, yönetim).
Kanıt-temelli: grafik folkloruna (H&S/RSI-div/sweep — bizde çöktü) değil, BİZİM 21.5k
deduped sinyalimizin istatistiğine dayanır.

SERT GÜVENLİK (kodda zorlanır, Opus ihlal edemez): XAU SELL + USOIL BUY kalıcı yasak;
size_factor [0,1.0]; günlük zarar limiti executor'da. Bunlar "veteran"a verilen kelepçe
değil, firma kuralları — kanıtla -EV olduğu için.

Model: Opus 4.8 (max) — yargı en iyi brain'i hak eder; kapı/durum seyrek olduğu için
quota sürdürülebilir. Quota sıkışırsa DECIDE_MODEL="sonnet".
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import decider_config as config  # noqa: E402

MEM = HERE / "memory"
JOURNAL_JSONL = MEM / "journal.jsonl"
DECIDE_MODEL = "opus"
# Per-sembol ATR stop çarpanları (grading + trade). Varsayılan RR~0.67.
# XAUUSD "patient WR" ([[xauusd-meta-stop-sizing]]): dar stop → dönüş tamamlanmadan SL.
# Geniş SL ver → sabırlı bounce stop yemeden realize olsun (canlı gözlem: XAU BUY %43/−0.29R dar stopla).
DEFAULT_STOP_ATR = (1.0, 1.5)
STOP_ATR = {
    "XAUUSD": (1.0, 2.5),       # TP 1×ATR (VWAP'a dönüş), SL 2.5×ATR (geniş — sabırlı)
}
TP_ATR, SL_ATR = DEFAULT_STOP_ATR   # geriye-uyum (varsayılan)


def stop_mults(symbol: str) -> tuple[float, float]:
    return STOP_ATR.get(symbol, DEFAULT_STOP_ATR)

# Sert yasaklar — kanıtlı -EV, Opus ihlal edemez (kod zorlar). config'i de birleştir.
HARD_BANS: set[tuple[str, str]] = {("XAUUSD", "SELL"), ("USOIL.FOREX", "BUY")} | \
    set(getattr(config, "BLOCKED_SYMBOL_DIRECTIONS", set()))

SYSTEM = (
    "Sen ForexSAI'nin baş trader'ısın — 50 yıllık deneyimli, soğukkanlı, KANITA dayalı bir "
    "veteran. Sana bir sembolün canlı durumu VE benzer geçmiş kurulumların gerçek WR kanıtı "
    "(bizim 21.5k deduped sinyalimizden) sunulur. KENDİ görüşünü oluştur: işlem aç mı, bekle mi? "
    "hangi yön? ne boyut? KRİTİK: grafik folkloruna (head&shoulders, RSI-divergence, sweep — "
    "bunlar BİZİM verimizde çöktü) DEĞİL, sana verilen geçmiş istatistiğe dayan. Kanıt zayıfsa "
    "(düşük WR/az örnek) ya da bağlam kötüyse BEKLE — işlem açmamak da karardır. "
    "size_factor ∈ [0,1.0]: konviksiyon × bağlam (korelasyon/event/rejim). Çıktın SADECE tek-satır JSON."
)


def _read(name: str) -> str:
    p = MEM / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_prompt(situation: dict) -> str:
    sym = situation["symbol"]
    bans = [f"{s} {d}" for (s, d) in HARD_BANS if s == sym]
    return f"""{SYSTEM}

=== PLAYBOOK (doğrulanmış priorlar) ===
{_read('PLAYBOOK.md')}

=== LESSONS (terfi etmiş dersler) ===
{_read('LESSONS.md')}

=== REGIME (güncel piyasa bağlamı) ===
{_read('REGIME.md')}

=== CANLI DURUM: {sym} ===
{json.dumps(situation, ensure_ascii=False, indent=2)}

=== SERT YASAK (bu sembol) ===
{bans or "yok"}

GÖREV — {sym} için KENDİ görüşünü oluştur (kanıttan muhakeme et):
- Her yönün `evidence`'ı: benzer geçmiş kurulumda gerçek WR + örnek (n) + OOS. Buna dayan.
- rev_chan/rev_vwap yüksek (ters yönde aşırı) = mean-reversion fırsatı; düşük/negatif = kovalama (kanıtta düşük WR).
- NDX'te VIX rejimi yönü etkiler AMA yalnız vix.fresh=true ise; vix.fresh=false (off-hours/neutral_band → ^VIX donuk/bıçak-sırtı) → VIX'e GÜVENME, yalnız fiyat-kanıtına dayan.
- Açık pozisyon/korelasyon yığılması, near_event=true → küçült/bekle.
- XAU BUY ise: "patient WR", GENİŞ stop şart (management'a yaz, boyut düşür).
SADECE şu tek-satır JSON'u döndür:
{{"action":"OPEN","direction":"BUY","size_factor":0.7,"entry":"market","reason":"kanıta dayalı kısa gerekçe","management":"stop/hedef/çıkış notu"}}
(işlem açmıyorsan: {{"action":"WAIT","direction":null,"size_factor":0,"reason":"...","management":""}})"""


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def call_claude(prompt: str, model: str = DECIDE_MODEL, timeout: int = 180) -> dict:
    cmd = ["claude", "--dangerously-skip-permissions", "-p",
           "--model", model, "--output-format", "json"]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"action": "WAIT", "reason": "claude timeout", "_error": True}
    if r.returncode != 0:
        return {"action": "WAIT", "reason": f"claude exit {r.returncode}: {r.stderr[:200]}", "_error": True}
    try:
        meta = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"action": "WAIT", "reason": "meta parse fail", "_error": True}
    dec = _extract_json(meta.get("result", ""))
    if dec is None:
        return {"action": "WAIT", "reason": "decision parse fail",
                "_raw": meta.get("result", "")[:300], "_error": True}
    dec["_cost_usd"] = meta.get("total_cost_usd")
    dec["_ms"] = meta.get("duration_ms")
    dec["_model"] = model
    return dec


def _enforce_guardrails(symbol: str, dec: dict) -> dict:
    """Sert güvenlik — Opus ne derse desin: yasak yön → WAIT; size [0,1.0]; WAIT → size 0."""
    action = str(dec.get("action", "WAIT")).upper()
    direction = dec.get("direction")
    if action == "OPEN" and direction and (symbol, str(direction).upper()) in HARD_BANS:
        dec["action"] = "WAIT"
        dec["reason"] = f"[SERT-YASAK: {symbol} {direction}] " + str(dec.get("reason", ""))
        dec["size_factor"] = 0.0
        return dec
    try:
        sf = float(dec.get("size_factor", 0.0))
    except (TypeError, ValueError):
        sf = 0.0
    dec["size_factor"] = max(0.0, min(1.0, sf))
    if action != "OPEN":
        dec["size_factor"] = 0.0
    return dec


def decide_situation(situation: dict, model: str = DECIDE_MODEL) -> dict:
    """Opus sembol durumundan KENDİ kararını verir + sert güvenlik kıskacı."""
    dec = call_claude(build_prompt(situation), model=model)
    return _enforce_guardrails(situation["symbol"], dec)


def append_journal(situation: dict, dec: dict) -> dict:
    """Kararı ham deneyim olarak journal.jsonl'e yaz (re-damıtma yakıtı; outcome sonra dolar)."""
    sym = situation["symbol"]
    chosen = dec.get("direction")
    chosen_blk = (situation.get("directions", {}).get(chosen, {}) or {}) if chosen else {}
    used_ev = chosen_blk.get("evidence")
    live = chosen_blk.get("live") or {}

    # OPEN ise: entry + ATR-bazlı TP/SL seviyeleri (sonra outcome'da WIN/LOSS taranır)
    trade = None
    if str(dec.get("action", "")).upper() == "OPEN" and chosen:
        atr, price = live.get("atr"), situation.get("price")
        if atr and price:
            buy = str(chosen).upper() == "BUY"
            tp_atr, sl_atr = stop_mults(sym)           # per-sembol (XAU geniş SL)
            tp = price + tp_atr * atr if buy else price - tp_atr * atr
            sl = price - sl_atr * atr if buy else price + sl_atr * atr
            trade = {"entry_price": round(price, 5), "atr": round(atr, 5),
                     "tp": round(tp, 5), "sl": round(sl, 5), "rr": round(tp_atr / sl_atr, 2),
                     "entry_bar_time": situation.get("bar_time")}   # MT5-frame (broker-saat tutarlı resolve)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "symbol": sym,
        "decision": {k: dec.get(k) for k in ("action", "direction", "size_factor", "entry", "reason", "management")},
        "trade": trade,
        "live": live or None,
        "evidence_used": used_ev,
        "vix": situation.get("vix"),
        "context": situation.get("context"),
        "model": dec.get("_model", DECIDE_MODEL), "cost_usd": dec.get("_cost_usd"),
        "outcome": None,
    }
    MEM.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


if __name__ == "__main__":
    # uçtan-uca tek test: sentetik NDX oversold durumu → Opus kendi görüşü → journal
    import sys as _s
    _s.path.insert(0, str(HERE))
    import evidence as ev
    import math
    bars = [{"high": 100 + math.sin(i / 5), "low": 99 + math.sin(i / 5),
             "close": 100 + math.sin(i / 5), "volume": 1000} for i in range(60)]
    bars[-1] = {"high": 95.1, "low": 94.8, "close": 95.0, "volume": 5000}
    tables = ev.load_tables()
    sit = {"symbol": "NDX.INDX",
           "vix": {"value": 21.3, "regime": "stress", "favored": "BUY"},
           "context": {"session": "NY", "open_positions": 0, "near_event": False, "recent": "geçmiş yok"},
           "directions": {}}
    for d in ("BUY", "SELL"):
        lf = ev.live_features(bars, d, vix=21.3)
        sit["directions"][d] = {"live": lf, "evidence": ev.evidence_pack("NDX.INDX", d, lf, tables)}
    print(f"Opus karar veriyor ({DECIDE_MODEL})...")
    dec = decide_situation(sit)
    print(json.dumps({k: v for k, v in dec.items() if not k.startswith("_")}, ensure_ascii=False, indent=2))
    print(f"(cost≈${dec.get('_cost_usd')}, {dec.get('_ms')}ms)")
    append_journal(sit, dec)
    print("journal'a yazıldı.")
