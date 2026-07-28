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
from exits import POLICIES, DEFAULT_POLICY, policies_for, baseline_for  # noqa: E402

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


def _report(title, rows, symbol=None, grades_key="exit_grades"):
    """symbol verilirse sembol-özel politika seti + CANLI geometri bazı kullanılır
    (2026-07-27: XAU'nun 1.0/2.5 bazı eski sette yoktu — kıyas yanlış bazlaydı).
    grades_key='exit_grades_real' → gerçek OPEN trade'lerin grade'leri (cf değil)."""
    graded = [r for r in rows if isinstance(r.get(grades_key), dict) and r[grades_key]]
    print("=" * 72)
    print(f"{title}  |  exit-grade'li işlem: {len(graded)}")
    print("=" * 72)
    if len(graded) < MIN_N:
        print(f"  ⏳ yetersiz ({len(graded)}/{MIN_N}) — {grades_key} veri biriktikçe dolar.\n")
        return None
    by_pol = defaultdict(list)
    for r in graded:
        for pol, pnl in r[grades_key].items():
            if isinstance(pnl, (int, float)):
                by_pol[pol].append(pnl)
    base_pol = baseline_for(symbol)
    ranked = []
    for pol in policies_for(symbol):
        m, se, n = _stats(by_pol.get(pol, []))
        if n:                                    # yön-kapsamlı/yeni politikalar boş olabilir
            ranked.append((pol, m, se, n))
    if not ranked:
        print("  ⏳ politika verisi yok.\n"); return None
    ranked.sort(key=lambda x: -x[1])
    base = next((m for p, m, se, n in ranked if p == base_pol), 0.0)
    print(f"  {'çıkış politikası':<22}{'EV(ATR)':>9}{'±se':>7}{'n':>5}   (baz {base_pol} = {base:+.3f})")
    print("  " + "-" * 60)
    for pol, m, se, n in ranked:
        star = "  ⬅ baz" if pol == base_pol else ""
        best = "  🏆" if pol == ranked[0][0] else ""
        print(f"  {pol:<22}{m:>+9.3f}{se:>7.3f}{n:>5}{best}{star}")
    best_pol, best_m = ranked[0][0], ranked[0][1]
    edge = best_m - base
    if best_pol != base_pol and edge >= MIN_EDGE and ranked[0][3] >= MIN_N:
        print(f"  → ✅ ÖNERİ: '{best_pol}' bazı +{edge:.3f} ATR/işlem geçiyor → bu çıkışı düşün.")
    else:
        print(f"  → baz ({base_pol}) savunulabilir (en iyi fark +{edge:.3f} < {MIN_EDGE} ya da n az).")
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
        _report(f"SEMBOL: {sym}", items, symbol=sym)
        _report(f"SEMBOL: {sym} — GERÇEK OPEN trade'ler", items, symbol=sym,
                grades_key="exit_grades_real")
    print("Not: pnl_atr = işlem başı beklenen ATR kazancı (lot×ATR-değeri = para). En yüksek")
    print("ortalama = en kârlı çıkış. Öneri çıkarsa decide.py stop_mults / yeni exit-config'e wire edilir.")


if __name__ == "__main__":
    main()
