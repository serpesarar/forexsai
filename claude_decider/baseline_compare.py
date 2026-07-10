"""
baseline_compare.py — Opus vs NAIVE-GATE: beyin (LLM seçimi) değer katıyor mu?
=============================================================================
Varlık sorusu: Opus'un seçiciliği, "her gate ateşlemesinde aç" aptal kuralından daha mı
iyi? Yoksa gate tek başına yeterli mi (beyin quota'yı boşa mı harcıyor)?

ALTYAPI HAZIR: counterfactual her gate-fired durumu (OPEN+WAIT) primary_dir'de grade eder
(cf_outcome). Yani "naive-gate" = tüm gate-fired cf'ler. "Opus-seçili" = gerçek OPEN'lar.

ÇIKTI:
 [1] SEÇİM KALİTESİ (cf-grading, apples-to-apples): gate-fired'ları Opus AÇTI vs ATLADI →
     açtıklarının cf-WR'ı atladıklarından yüksekse Opus kazananı seçip kaybedeni eliyor.
     Permütasyon p ile anlamlılık (şans mı).
 [2] GERÇEKLEŞEN: Opus'un gerçek OPEN WR/EV'si (kendi yön+boyut seçimiyle) vs naive-gate.
 [3] BOYUT: size_factor yüksek OPEN'lar düşüklerden çok mu kazanıyor (sizing değer mi).
 [4] PER SEMBOL.

VERDİKT: Opus açtığı-WR > naive-WR → ✅ değerli · ≈ → nötr (gate yeter) · < → 🔴 TERS (alarm).
"""
from __future__ import annotations
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL  # noqa: E402

random.seed(13)
PERM_M = 500
MIN_N = 10           # bir kovada anlamlı ölçüm için min WIN/LOSS örneği
MIN_SYM = 8


def _load():
    if not JOURNAL_JSONL.exists():
        return []
    from decide import load_journal
    return load_journal(clean=True)   # donuk-kopya karantinası (analiz katmanı)


def _gate_fired(e) -> bool:
    return bool(((e.get("counterfactual") or {}).get("live") or {}).get("gate_fired"))


def _action(e) -> str:
    return str((e.get("decision") or {}).get("action", "")).upper()


def _wins(items, okey):
    """WIN=1/LOSS=0 listesi (sadece sonuçlanmışlar)."""
    return [1 if r.get(okey) == "WIN" else 0 for r in items if r.get(okey) in ("WIN", "LOSS")]


def _wr_ev(items, okey, pkey):
    g = [r for r in items if r.get(okey) in ("WIN", "LOSS")]
    if not g:
        return None
    w = sum(1 for r in g if r[okey] == "WIN")
    ev = sum((r.get(pkey) if r.get(pkey) is not None else (0.667 if r[okey] == "WIN" else -1.0)) for r in g) / len(g)
    return w, len(g), 100 * w / len(g), ev


def _perm_gap(kept_w, skip_w, M=PERM_M):
    """kept_w vs skip_w WR farkı + permütasyon p (gözlemlenen lift şans mı)."""
    if not kept_w or not skip_w:
        return 0.0, 1.0
    allw = kept_w + skip_w; nk = len(kept_w)
    obs = sum(kept_w) / nk - sum(skip_w) / len(skip_w)
    ge = 0
    for _ in range(M):
        sh = random.sample(allw, len(allw))
        k, s = sh[:nk], sh[nk:]
        if (sum(k) / len(k) - sum(s) / len(s)) >= obs:
            ge += 1
    return obs * 100, (ge + 1) / (M + 1)


def main():
    rows = _load()
    gate = [e for e in rows if _gate_fired(e)]
    gate_graded = [e for e in gate if e.get("cf_outcome") in ("WIN", "LOSS")]
    print("=" * 70)
    print("OPUS vs NAIVE-GATE — beyin (LLM seçimi) değer katıyor mu?")
    print("=" * 70)
    print(f"Journal: {len(rows)} karar | gate-fired: {len(gate)} | grade'li: {len(gate_graded)}")
    if len(gate_graded) < MIN_N:
        print(f"\n⏳ Yetersiz veri ({len(gate_graded)}/{MIN_N} grade'li gate-fired). Bu metrik")
        print("   counterfactual'la YENİ — decider çalıştıkça dolacak (eski journal'da yok).")
        print("   Birkaç gün sonra tekrar bak.")
        return

    opened = [e for e in gate_graded if _action(e) == "OPEN"]
    waited = [e for e in gate_graded if _action(e) == "WAIT"]

    # [1] SEÇİM KALİTESİ — aynı cf-grading (yön/boyut farkını izole eder)
    print("\n[1] SEÇİM KALİTESİ (gate-fired'ları cf-grading ile; apples-to-apples)")
    kept_w = _wins(opened, "cf_outcome"); skip_w = _wins(waited, "cf_outcome")
    naive = _wr_ev(gate_graded, "cf_outcome", "cf_pnl_r")
    kept = _wr_ev(opened, "cf_outcome", "cf_pnl_r")
    skip = _wr_ev(waited, "cf_outcome", "cf_pnl_r")
    print(f"    Naive (HEPSİNİ aç):  WR {naive[2]:.0f}% ({naive[0]}/{naive[1]})  EV {naive[3]:+.3f}R")
    if kept:
        print(f"    Opus AÇTI:           WR {kept[2]:.0f}% ({kept[0]}/{kept[1]})  EV {kept[3]:+.3f}R")
    if skip:
        print(f"    Opus ATLADI:         WR {skip[2]:.0f}% ({skip[0]}/{skip[1]})  EV {skip[3]:+.3f}R")
    if kept_w and skip_w:
        lift, p = _perm_gap(kept_w, skip_w)
        verdict = ("✅ Opus kazananı SEÇİP kaybedeni eliyor (değerli)" if lift >= 8 and p < 0.05
                   else "🔴 TERS — Opus kazananı atlıyor (ALARM)" if lift <= -8
                   else "~ seçim katkısı zayıf/belirsiz (gate ~yeterli)")
        print(f"    → Seçim lift (açtı−atladı): {lift:+.0f}pp  (permütasyon p={p:.3f})  {verdict}")
    else:
        print("    → (açtı veya atladı kovasında yeterli sonuç yok)")

    # [2] GERÇEKLEŞEN — Opus'un gerçek OPEN'ları (kendi yön+boyut seçimiyle) vs naive
    print("\n[2] GERÇEKLEŞEN (Opus gerçek OPEN, kendi yön+boyut) vs naive-gate")
    real_open = [e for e in rows if _action(e) == "OPEN" and e.get("outcome") in ("WIN", "LOSS")]
    ro = _wr_ev(real_open, "outcome", "pnl_r")
    if ro:
        print(f"    Opus OPEN (gerçek):  WR {ro[2]:.0f}% ({ro[0]}/{ro[1]})  EV {ro[3]:+.3f}R")
    print(f"    Naive-gate (cf):     WR {naive[2]:.0f}% ({naive[1]} işlem)  EV {naive[3]:+.3f}R")
    if ro:
        d = ro[3] - naive[3]
        print(f"    → Fark: {d:+.3f}R/işlem  ({'Opus daha iyi' if d > 0.03 else 'naive daha iyi' if d < -0.03 else 'başabaş'})")

    # [3] BOYUT DEĞER KATIYOR MU — size_factor → sonuç
    print("\n[3] BOYUT (size_factor) değer katıyor mu?")
    sized = [(e, (e.get("decision") or {}).get("size_factor")) for e in real_open]
    sized = [(e, s) for e, s in sized if isinstance(s, (int, float))]
    if len(sized) >= MIN_N:
        med = sorted(s for _, s in sized)[len(sized) // 2]
        hi = _wr_ev([e for e, s in sized if s > med], "outcome", "pnl_r")
        lo = _wr_ev([e for e, s in sized if s <= med], "outcome", "pnl_r")
        if hi and lo:
            gap = hi[2] - lo[2]
            v = ("konviksiyon GERÇEK (büyük→çok kazanıyor)" if gap >= 8
                 else "ters (küçük daha iyi!)" if gap <= -8 else "boyut zayıf sinyal")
            print(f"    size>{med:.2f}: WR {hi[2]:.0f}% (n={hi[1]}) · size≤: WR {lo[2]:.0f}% (n={lo[1]}) → {v}")
    else:
        print(f"    (n az: {len(sized)}/{MIN_N})")

    # [4] PER SEMBOL — seçim lift
    print("\n[4] PER SEMBOL (seçim kalitesi, n≥%d)" % MIN_SYM)
    by = defaultdict(lambda: {"open": [], "wait": []})
    for e in opened:
        by[e["symbol"]]["open"].append(e)
    for e in waited:
        by[e["symbol"]]["wait"].append(e)
    for sym, d in sorted(by.items()):
        kw = _wins(d["open"], "cf_outcome"); sw = _wins(d["wait"], "cf_outcome")
        if len(kw) + len(sw) < MIN_SYM:
            continue
        ko = (100 * sum(kw) / len(kw)) if kw else None
        so = (100 * sum(sw) / len(sw)) if sw else None
        lift = (ko - so) if (ko is not None and so is not None) else None
        print(f"    {sym:<14} açtı {('%.0f%%(%d)' % (ko, len(kw))) if ko is not None else '-':<10} "
              f"atladı {('%.0f%%(%d)' % (so, len(sw))) if so is not None else '-':<10} "
              f"lift {('%+.0fpp' % lift) if lift is not None else '-'}")

    print("\nNot: [1] permütasyon p<0.05 + lift≥8pp = beyin GERÇEKTEN seçici. Aksi halde")
    print("gate tek başına ~yeterli → Opus'u sadeleştir/quota düşür düşünülebilir.")


if __name__ == "__main__":
    main()
