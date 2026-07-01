"""
outcomes.py — SHADOW kararlarını ölç: açık journal kayıtlarını WIN/LOSS/EXPIRE'a çöz.
=============================================================================
Karar anında entry+ATR-bazlı TP/SL (RR~0.67) `trade` bloğunda kaydedildi. Bu modül
karardan SONRAKİ 5m barları tarar: TP mı SL mi önce vuruldu? Aynı barda ikisi de →
konservatif LOSS (SL önce — ground-truth dürüstlüğü, "win sanılan SL-first kayıplar").

Bu, shadow'u ÖLÇÜLEBİLİR yapar + öğrenme yakıtı (distill_journal) üretir. WAIT kararları
gerçek/sanal işlem değil → "WAIT" işaretlenir, grade edilmez.
"""
from __future__ import annotations
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import decider_config as config  # noqa: E402
from decide import JOURNAL_JSONL  # noqa: E402
import exits  # noqa: E402  (çoklu çıkış politikası grade'i)

MAX_HORIZON_H = 48      # bu süre içinde ne TP ne SL → EXPIRE (nötr)


# ── Saf çözüm mantığı (test edilebilir) ──────────────────────────────────────
def resolve_path(direction: str, tp: float, sl: float, bars_after: list[dict]):
    """Karardan sonraki barlarda TP mi SL mi önce? Dönüş: (outcome|None, hit_time|None).
    bars_after: [{high,low,close,time}, ...] zaman sıralı. Çift-değme → LOSS (konservatif)."""
    buy = direction.upper() == "BUY"
    for b in bars_after:
        hit_tp = (b["high"] >= tp) if buy else (b["low"] <= tp)
        hit_sl = (b["low"] <= sl) if buy else (b["high"] >= sl)
        if hit_sl:                      # SL önce sayılır (aynı bar dahil) → dürüst
            return "LOSS", b.get("time")
        if hit_tp:
            return "WIN", b.get("time")
    return None, None


def pnl_r(outcome: str, rr: float = 0.667) -> float:
    """WIN → +rr (R cinsinden; R = SL riski), LOSS → −1.0. rr per-trade (sembole göre stop)."""
    return round(float(rr), 3) if outcome == "WIN" else (-1.0 if outcome == "LOSS" else 0.0)


# Bar kaynağı (MT5 fetcher) run_decider'da tanımlı (Pepperstone sembol map'iyle) ve
# resolve_journal'a parametre olarak verilir — outcome çözümü her cycle orada yapılır.


# ── Journal'ı çöz ────────────────────────────────────────────────────────────
def resolve_journal(fetcher, max_horizon_h: float = MAX_HORIZON_H) -> tuple[int, list]:
    if not JOURNAL_JSONL.exists():
        return 0, []
    rows = [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    now = time.time(); changed = 0

    def _bars_after(e):
        anchor = (e.get("trade") or e.get("counterfactual") or {}).get("entry_bar_time")
        ts = datetime.fromisoformat(e["ts"]).timestamp()
        since = anchor or ts
        return [b for b in fetcher(e["symbol"], since) if b["time"] > since], ts

    for e in rows:
        need_real = e.get("outcome") is None
        # KARŞI-OLGU grade: primary_dir trade "açsaydı" ne olurdu (recall analizi, HER kayıtta)
        cf = e.get("counterfactual")
        need_cf = cf is not None and e.get("cf_outcome") is None
        # GÖLGE model (Fable) — kendi OPEN trade'ini grade et (A/B kıyas)
        sm = e.get("shadow_model")
        sm_tr = (sm or {}).get("trade")
        need_sm = sm is not None and sm.get("outcome") is None and \
            (sm_tr is not None or str((sm.get("decision") or {}).get("action", "")).upper() != "OPEN")
        if not need_real and not need_cf and not need_sm:
            continue
        bars = None
        # 1) gerçek karar (yalnız OPEN'lar P&L sayılır)
        if need_real:
            act = str(e.get("decision", {}).get("action", "")).upper()
            if act != "OPEN":
                e["outcome"] = "WAIT"; changed += 1
            else:
                tr = e.get("trade")
                if not tr:
                    e["outcome"] = "NO_LEVELS"; changed += 1
                else:
                    bars, ts = _bars_after(e)
                    outcome, hit = resolve_path(e["decision"]["direction"], tr["tp"], tr["sl"], bars)
                    if outcome:
                        e["outcome"] = outcome
                        e["outcome_at"] = datetime.fromtimestamp(hit, tz=timezone.utc).isoformat() if hit else None
                        e["pnl_r"] = pnl_r(outcome, tr.get("rr", 0.667)); changed += 1
                    elif now - datetime.fromisoformat(e["ts"]).timestamp() > max_horizon_h * 3600:
                        e["outcome"] = "EXPIRE"; e["pnl_r"] = 0.0; changed += 1
        # 2) karşı-olgu (her kayıtta: primary_dir açsaydı) + ÇOKLU ÇIKIŞ grade'i
        if need_cf:
            if bars is None:
                bars, ts = _bars_after(e)
            cfo, _ = resolve_path(cf["dir"], cf["tp"], cf["sl"], bars)
            mature = now - datetime.fromisoformat(e["ts"]).timestamp() > max_horizon_h * 3600
            if cfo:
                e["cf_outcome"] = cfo
                e["cf_pnl_r"] = pnl_r(cfo, cf.get("rr", 0.667)); changed += 1
            elif mature:
                e["cf_outcome"] = "EXPIRE"; e["cf_pnl_r"] = 0.0; changed += 1
            # Çıkış politikaları: tam ileri pencere üzerinde 6 çıkışı grade et (sembol başına
            # en iyi çıkışı öğrenmek için — exit_compare.py analiz eder). cf çözülünce/olgunlaşınca.
            if e.get("exit_grades") is None and cf.get("atr") and bars and (cfo or mature):
                eg = exits.grade_all(cf["dir"], cf["entry_price"], cf["atr"], bars)
                if eg:
                    e["exit_grades"] = eg; changed += 1
        # 3) GÖLGE model (Fable) kararını grade et
        if need_sm:
            act = str((sm.get("decision") or {}).get("action", "")).upper()
            if act != "OPEN":
                sm["outcome"] = "WAIT"; changed += 1
            elif sm_tr:
                if bars is None:
                    bars, ts = _bars_after(e)
                smo, _ = resolve_path(sm["decision"]["direction"], sm_tr["tp"], sm_tr["sl"], bars)
                if smo:
                    sm["outcome"] = smo; sm["pnl_r"] = pnl_r(smo, sm_tr.get("rr", 0.667)); changed += 1
                elif now - datetime.fromisoformat(e["ts"]).timestamp() > max_horizon_h * 3600:
                    sm["outcome"] = "EXPIRE"; sm["pnl_r"] = 0.0; changed += 1
    if changed:
        with open(JOURNAL_JSONL, "w", encoding="utf-8") as f:
            for e in rows:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return changed, rows


def summary(rows: list) -> str:
    graded = [r for r in rows if r.get("outcome") in ("WIN", "LOSS")]
    opens = [r for r in rows if r.get("outcome") is None]
    waits = [r for r in rows if r.get("outcome") == "WAIT"]
    exp = [r for r in rows if r.get("outcome") == "EXPIRE"]
    if not graded:
        return f"henüz grade edilmiş işlem yok | açık={len(opens)} bekle={len(waits)} expire={len(exp)}"
    w = sum(1 for r in graded if r["outcome"] == "WIN")
    ev = sum(r.get("pnl_r", 0) for r in graded) / len(graded)
    return (f"OPEN kararlar: {len(graded)} grade | WR {100*w/len(graded):.0f}% ({w}/{len(graded)}) | "
            f"EV {ev:+.3f}R/işlem | açık={len(opens)} bekle={len(waits)} expire={len(exp)}")


def main():
    """Standalone: journal'daki MEVCUT sonuçların WR/EV özeti (yeni çözüm run_decider döngüsünde
    her cycle yapılır). MT5 gerekmez — sadece okur."""
    if not JOURNAL_JSONL.exists():
        print("journal yok (decider henüz çalışmadı)."); return
    rows = [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("Decider performans özeti:")
    print("  " + summary(rows))


if __name__ == "__main__":
    main()
