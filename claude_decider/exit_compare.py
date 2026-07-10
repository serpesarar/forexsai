"""
exit_compare.py — hangi çıkış stratejisi sembol başına en kârlı? (exit optimization)
=============================================================================
outcomes.py her işlemi 6 çıkışla grade etti (exit_grades, ATR biriminde P&L). Bu modül
sembol başına her politikanın ortalama pnl_atr'ını (= işlem başı beklenen ATR kazancı)
kıyaslar, en iyiyi bulur, mevcut varsayılanla (fixed_1.0/1.5) farkı gösterir.

ATR birimi → politikalar adil kıyaslanır. En yüksek ortalama pnl_atr = en çok para/işlem.
Kanıt-kapısı: min örnek + en iyinin varsayılanı belirgin geçmesi (yoksa varsayılan kalır).
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL  # noqa: E402
from exits import POLICIES, DEFAULT_POLICY  # noqa: E402

MIN_N = 15        # bir sembol için güvenilir çıkış kıyası
MIN_EDGE = 0.10   # en iyi, varsayılanı en az bu kadar ATR/işlem geçmeli → öneri


def _load():
    if not JOURNAL_JSONL.exists():
        return []
    from decide import load_journal
    return load_journal(clean=True)   # donuk-kopya karantinası (analiz katmanı)


def _stats(vals):
    n = len(vals)
    if not n:
        return 0.0, 0.0, 0
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n if n > 1 else 0.0
    return mean, (var / n) ** 0.5, n   # ortalama, std-err, n


def _report(title, rows):
    graded = [r for r in rows if isinstance(r.get("exit_grades"), dict) and r["exit_grades"]]
    print("=" * 72)
    print(f"{title}  |  exit-grade'li işlem: {len(graded)}")
    print("=" * 72)
    if len(graded) < MIN_N:
        print(f"  ⏳ yetersiz ({len(graded)}/{MIN_N}) — exit_grades YENİ özellik, veri biriktikçe dolar.\n")
        return None
    by_pol = defaultdict(list)
    for r in graded:
        for pol, pnl in r["exit_grades"].items():
            if isinstance(pnl, (int, float)):
                by_pol[pol].append(pnl)
    ranked = []
    for pol in POLICIES:
        m, se, n = _stats(by_pol.get(pol, []))
        ranked.append((pol, m, se, n))
    ranked.sort(key=lambda x: -x[1])
    base = next((m for p, m, se, n in ranked if p == DEFAULT_POLICY), 0.0)
    print(f"  {'çıkış politikası':<18}{'EV(ATR)':>9}{'±se':>7}{'n':>5}   (varsayılan {DEFAULT_POLICY} = {base:+.3f})")
    print("  " + "-" * 56)
    for pol, m, se, n in ranked:
        star = "  ⬅ varsayılan" if pol == DEFAULT_POLICY else ""
        best = "  🏆" if pol == ranked[0][0] else ""
        print(f"  {pol:<18}{m:>+9.3f}{se:>7.3f}{n:>5}{best}{star}")
    best_pol, best_m = ranked[0][0], ranked[0][1]
    edge = best_m - base
    if best_pol != DEFAULT_POLICY and edge >= MIN_EDGE and ranked[0][3] >= MIN_N:
        print(f"  → ✅ ÖNERİ: '{best_pol}' varsayılanı +{edge:.3f} ATR/işlem geçiyor → bu çıkışı düşün.")
    else:
        print(f"  → varsayılan ({DEFAULT_POLICY}) savunulabilir (en iyi fark +{edge:.3f} < {MIN_EDGE} ya da n az).")
    print()
    return best_pol, edge


def main():
    rows = _load()
    print("\nÇIKIŞ STRATEJİSİ OPTİMİZASYONU — hangi çıkış sembol başına en kârlı?\n")
    _report("TÜM SEMBOLLER", rows)
    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r.get("symbol")].append(r)
    for sym, items in sorted(by_sym.items()):
        _report(f"SEMBOL: {sym}", items)
    print("Not: pnl_atr = işlem başı beklenen ATR kazancı (lot×ATR-değeri = para). En yüksek")
    print("ortalama = en kârlı çıkış. Öneri çıkarsa decide.py stop_mults / yeni exit-config'e wire edilir.")


if __name__ == "__main__":
    main()
