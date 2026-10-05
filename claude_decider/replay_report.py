"""
replay_report.py — batch_eval replay sonuçlarını pencere/sembol/hafta kırılımıyla özetle (LLM çağrısız).
=============================================================================
Kullanım: python replay_report.py --model=claude-sonnet-5-5 --since=2026-09-11
Karşılaştırma tabanı AYNI pencerenin "hepsini aç" (cf) sonucudur — seçim alfası
modelin OPEN dediği kümenin EV'si ile tabanın EV'si arasındaki farktır. Başabaş: RR 0.667 → %60.
"""
from __future__ import annotations
import json
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import load_journal  # noqa: E402

BOOT_N = 4000
WIN_R, LOSS_R = 0.667, -1.0


def _r(e: dict) -> float:
    v = e.get("cf_pnl_r")
    if v is not None:
        return float(v)
    return WIN_R if e.get("cf_outcome") == "WIN" else LOSS_R


def _stats(rs: list[float]) -> str:
    if not rs:
        return "n=0"
    n, w = len(rs), sum(1 for x in rs if x > 0)
    return f"n={n:<4} WR %{100*w/n:4.1f}  EV {sum(rs)/n:+.3f}R"


def _p_pos(rs: list[float]) -> float:
    random.seed(7)
    if len(rs) < 5:
        return float("nan")
    pos = sum(1 for _ in range(BOOT_N)
              if sum(random.choices(rs, k=len(rs))) > 0)
    return pos / BOOT_N


def main() -> None:
    model, since = "claude-sonnet-5-5", "2026-09-11"
    for a in sys.argv[1:]:
        if a.startswith("--model="):
            model = a.split("=", 1)[1]
        elif a.startswith("--since="):
            since = a.split("=", 1)[1]
    rows = [e for e in load_journal(clean=True)
            if (e.get("batch_eval") or {}).get(model) and e.get("cf_outcome") in ("WIN", "LOSS")
            and str(e.get("ts") or "") >= since]
    opened, mism = [], 0
    for e in rows:
        a = e["batch_eval"][model]
        if str(a.get("action", "")).upper() != "OPEN":
            continue
        if str(a.get("direction", "")).upper() != str((e.get("counterfactual") or {}).get("dir", "")).upper():
            mism += 1
            continue
        opened.append(e)
    print(f"[{model}] pencere ≥{since}: değerlendirilen {len(rows)}, OPEN {len(opened) + mism} "
          f"(grade'li {len(opened)}, yön-eşleşmedi {mism})")
    base = [_r(e) for e in rows]
    sel = [_r(e) for e in opened]
    print(f"  TABAN (hepsini aç)   {_stats(base)}")
    print(f"  MODEL OPEN kümesi    {_stats(sel)}   P(EV>0)=%{100*_p_pos(sel):.0f}")
    rest = [_r(e) for e in rows if e not in opened]
    print(f"  MODELİN ELEDİĞİ      {_stats(rest)}")
    print("  (başabaş WR %60 @RR0.667; seçim alfası = MODEL OPEN − TABAN EV farkı)")
    for title, keyf in (("SEMBOL", lambda e: e.get("symbol")),
                        ("HAFTA", lambda e: datetime.fromisoformat(str(e["ts"]).replace("Z", "+00:00")).strftime("%G-W%V"))):
        print(f"\n  {title} kırılımı:  [taban]  →  [model OPEN]")
        gb, go = defaultdict(list), defaultdict(list)
        for e in rows:
            gb[keyf(e)].append(_r(e))
        for e in opened:
            go[keyf(e)].append(_r(e))
        for k in sorted(gb, key=str):
            print(f"    {str(k):<14} {_stats(gb[k])}  →  {_stats(go.get(k, []))}")
    live = [e for e in rows if str((e.get("decision") or {}).get("action", "")).upper() == "OPEN"
            and e.get("outcome") in ("WIN", "LOSS")]
    if live:
        lr = [WIN_R if e["outcome"] == "WIN" else LOSS_R for e in live]
        print(f"\n  (canlı Opus-dönemi OPEN'ları bu pencerede: {_stats(lr)} — arıza öncesi kayıtlar)")


if __name__ == "__main__":
    main()
