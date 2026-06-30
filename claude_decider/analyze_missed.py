"""
analyze_missed.py — "Açmadığı işlemlerden hangileri kazanırdı?" (RECALL + filtre keşfi).
=============================================================================
Decider'ın AÇTIKLARINI (precision) outcomes.py zaten ölçer. Bu modül AÇMADIKLARINI
(WAIT) inceler: karşı-olgu (counterfactual) grade'lerinden — açsaydı kazanır mıydı?

İKİ ÇIKTI:
 1) Filtre fazla korumacı mı? Per-sembol: WAIT'lerin karşı-olgu WR'ı.
    - WAIT cf-WR < ~%60 (breakeven) → filtre DOĞRU reddediyor (koruma yerinde).
    - WAIT cf-WR > %65 (n≥15) → FAZLA KORUMACI, kazananları kaçırıyor.
 2) Yeni filtre adayı: kazanan WAIT'leri kaybeden WAIT'lerden AYIRAN özellik
    (rev_chan/rev_vwap/adx/vix...) — placebo p<0.05 + min örnek geçerse aday.

GÜVENLİK (kritik): kazananları toplayıp kural çıkarmak = overfit. Bu yüzden
kazanan-vs-kaybeden AYRIMI + placebo zorunlu. Aday yalnız LESSONS 'izlenenler'e gider,
kararı OTOMATİK etkilemez — distill_journal n≥20'de teyit edince ✅'e taşınır.
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

MIN_N = 15            # recall verdict için min karşı-olgu örneği
MIN_DISC = 20         # filtre keşfi için min örnek (overfit engeli)
BREAKEVEN = 0.60      # RR~0.67 → başabaş WR
PLACEBO_M = 300
random.seed(13)


def _load():
    if not JOURNAL_JSONL.exists():
        return []
    return [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]


def _wr(items, key="cf_outcome"):
    g = [r for r in items if r.get(key) in ("WIN", "LOSS")]
    if not g:
        return None
    w = sum(1 for r in g if r[key] == "WIN")
    return w, len(g), 100 * w / len(g)


def _cf_feat(r, key):
    """Karşı-olgu yönünün canlı feature'ı (primary_dir'in live'ı)."""
    cf = r.get("counterfactual") or {}
    lv = cf.get("live") or {}
    if key == "vix_fresh":
        return 1.0 if (r.get("vix") or {}).get("fresh") else 0.0
    if key == "open_positions":
        return (r.get("context") or {}).get("open_positions")
    return lv.get(key)


def _placebo_split(vals, wins, M=PLACEBO_M):
    """En iyi tek-eşik lift + placebo p. Dönüş (op, thr, lift_pp, p) | (None,...)."""
    if len(vals) < MIN_DISC:
        return None, None, 0.0, 1.0
    base = sum(wins) / len(wins)
    sv = sorted(vals)
    cands = [sv[int(q * (len(sv) - 1))] for q in (0.2, 0.35, 0.5, 0.65, 0.8)]

    def best(w):
        bl, bop, bt = -1, None, None
        for thr in cands:
            for op in (">", "<"):
                sel = [w[i] for i, v in enumerate(vals) if (v > thr if op == ">" else v < thr)]
                if len(sel) >= MIN_DISC // 2 and len(sel) >= 8:
                    lift = sum(sel) / len(sel) - base
                    if lift > bl:
                        bl, bop, bt = lift, op, thr
        return bl, bop, bt
    obs, op, thr = best(wins)
    if obs < 0:
        return None, None, 0.0, 1.0
    ge = sum(1 for _ in range(M) if best(random.sample(wins, len(wins)))[0] >= obs)
    return op, thr, obs * 100, (ge + 1) / (M + 1)


def main():
    rows = _load()
    has_cf = [r for r in rows if r.get("cf_outcome") in ("WIN", "LOSS")]
    print("=" * 70)
    print(f"RECALL ANALİZİ — {len(rows)} karar, {len(has_cf)} karşı-olgu grade edilmiş")
    print("=" * 70)
    if not has_cf:
        print("\n⏳ Henüz grade edilmiş karşı-olgu yok. Bu özellik YENİ — decider'ın bundan")
        print("   sonra açmadığı işlemler için karşı-olgu kaydı tutulacak; outcomes.py grade")
        print("   ettikçe burası dolacak. Eski WAIT'lerde counterfactual yok (geriye dönük yok).")
        return

    waited = [r for r in has_cf if str((r.get("decision") or {}).get("action", "")).upper() == "WAIT"]
    opened = [r for r in has_cf if str((r.get("decision") or {}).get("action", "")).upper() == "OPEN"]

    # 1) FAZLA KORUMACI MI — per sembol WAIT karşı-olgu WR
    print("\n[1] AÇMADIKLARI (WAIT) — açsaydı kazanır mıydı? (per sembol)")
    print(f"    {'sembol':<14}{'WAIT-cf':>9}{'WR':>7}  yorum")
    by = defaultdict(list)
    for r in waited:
        by[r["symbol"]].append(r)
    for sym, items in sorted(by.items()):
        res = _wr(items)
        if not res:
            continue
        w, n, pct = res
        if n < MIN_N:
            verdict = f"n={n} az, izle"
        elif pct >= 65:
            verdict = "⚠️ FAZLA KORUMACI — kazananları kaçırıyor"
        elif pct < BREAKEVEN * 100:
            verdict = "✓ koruma YERİNDE (açsaydı kaybederdi)"
        else:
            verdict = "~ sınırda"
        print(f"    {sym:<14}{f'{w}/{n}':>9}{pct:>6.0f}%  {verdict}")

    # 2) KAÇIRILAN KAZANANLARIN ORTAK ÖZELLİĞİ (placebo-kapılı keşif)
    print("\n[2] YENİ FİLTRE ADAYI — kazanan WAIT'leri kaybedenlerden ayıran özellik?")
    print("    (placebo p<0.05 + min örnek; yoksa gürültü → aday değil)")
    found = []
    for key, label in [("rev_chan", "kanal aşırılığı"), ("rev_vwap", "VWAP aşırılığı"),
                       ("adx", "ADX"), ("open_positions", "açık pozisyon")]:
        pairs = [(_cf_feat(r, key), 1 if r["cf_outcome"] == "WIN" else 0)
                 for r in waited if _cf_feat(r, key) is not None]
        if len(pairs) < MIN_DISC:
            continue
        vals = [p[0] for p in pairs]; wins = [p[1] for p in pairs]
        op, thr, lift, p = _placebo_split(vals, wins)
        if op and lift >= 8 and p < 0.05:
            msg = f"✅ WAIT iken {key} {op} {thr:.2g} → +{lift:.0f}pp kazanma ({label}); placebo p={p:.3f}"
            print(f"    {msg}")
            print(f"       → bu kurulumda Opus FAZLA temkinli; filtreyi burada gevşetmeyi değerlendir.")
            found.append(msg)
        elif op and lift >= 8:
            print(f"    ⏳ {key} {op} {thr:.2g} → +{lift:.0f}pp ama p={p:.2f} (≥0.05) — gürültü olabilir, izle")
    if not found:
        print("    (kanıt-kapısını geçen yeni filtre adayı YOK — mevcut filtreler savunulabilir)")

    # 3) genel kıyas
    ro = _wr(opened); rw = _wr(waited)
    print("\n[3] ÖZET")
    if ro:
        print(f"    AÇTIKLARI (gerçek): {ro[2]:.0f}% WR ({ro[0]}/{ro[1]})")
    if rw:
        sign = "fazla korumacı" if rw[2] >= 65 else "doğru reddetmiş" if rw[2] < 60 else "sınırda"
        print(f"    AÇMADIKLARI (karşı-olgu): {rw[2]:.0f}% WR ({rw[0]}/{rw[1]}) → {sign}")
    print(f"\n    Not: aday filtreler distill_journal n≥20'de placebo ile teyit edilince")
    print(f"    LESSONS '✅ onaylı'ya taşınır. Otomatik karar etkisi YOK (güvenli).")


if __name__ == "__main__":
    main()
