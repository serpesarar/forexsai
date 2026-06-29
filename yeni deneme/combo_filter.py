"""
combo_filter.py — ÇOK-GÖSTERGELİ filtre keşfi, OVERFIT KORUMALI.
====================================================================================
Tek gösterge +17pp veriyorsa 2-3 gösterge birlikte daha güçlü olabilir AMA arama
uzayı büyük → in-sample sahte kurallar bulmak kolay. Bu yüzden 3 katmanlı:

  1. Greedy forward rule-builder : kuralı adım adım kur (her adımda OOS-WR'ı en çok
     artıran koşulu ekle), gösterge başına 1 koşul, min retention zorunlu.
  2. Nested cross-validation     : kuralı TRAIN'de keşfet, TEST'te ölç → DÜRÜST OOS WR
     (in-sample değil — gerçek genelleme).
  3. Placebo (permütasyon) testi : etiketleri karıştır, aynı aramayı yap → sahte-lift
     dağılımı. Gerçek kuralın lift'i bunun üstündeyse GERÇEK, değilse overfit.

Çıktı: deploy edilebilir kural + in-sample WR + nested-CV (dürüst) WR + placebo p.
"""
from __future__ import annotations
import random
from discrimination import _is_stationary, _numeric


def _passes(r: dict, key: str, d: str, thr: float) -> bool:
    v = r["ind"].get(key)
    if not _numeric(v):
        return False                      # gösterge yoksa → koşulu geçemez (muhafazakar)
    return v < thr if d == "<" else v > thr


def evaluate(rows: list[dict], conds: list[tuple]) -> tuple[float, int]:
    kept = [r for r in rows if all(_passes(r, k, d, t) for k, d, t in conds)]
    if not kept:
        return 0.0, 0
    return sum(1 for r in kept if r["win"]) / len(kept), len(kept)


def candidates(rows: list[dict], qs=(0.25, 0.40, 0.55, 0.70)) -> list[tuple]:
    """Sabit aday eşik ızgarası: her durağan gösterge için quantile'lar × iki yön."""
    keys = set()
    for r in rows:
        keys.update(k for k, v in r["ind"].items() if _numeric(v) and _is_stationary(k))
    out = []
    for k in sorted(keys):
        vals = sorted(r["ind"][k] for r in rows if _numeric(r["ind"].get(k)))
        if len(vals) < 20:
            continue
        for q in qs:
            thr = vals[int(q * (len(vals) - 1))]
            out += [(k, "<", thr), (k, ">", thr)]
    return out


_TF_TOKENS = ("1m", "5m", "15m", "30m", "1h", "4h")


def _tf_of(key: str) -> str:
    """Anahtarın TF öneki (ör. '5m_rsi14'→'5m'); öneksizse 'base'."""
    pre = key.split("_", 1)[0]
    return pre if pre in _TF_TOKENS else "base"


def discover_rule(rows: list[dict], cands: list[tuple], max_conds=3,
                  min_keep_frac=0.25, min_gain=0.03, min_tfs=1) -> list[tuple]:
    """Greedy forward: her adımda WR'ı en çok artıran koşulu ekle (gösterge başına 1).
    min_tfs>1: kuralın EN AZ o kadar FARKLI timeframe kullanmasını zorla (cross-TF).
    Zorlama yalnızca çeşitliliği kaçırma riskinde devreye girer (aksi halde en iyiyi seçer).
    """
    if not rows:
        return []
    base = sum(r["win"] for r in rows) / len(rows)
    floor = max(15, int(len(rows) * min_keep_frac))
    avail_tfs = {_tf_of(k) for (k, _, _) in cands}
    need = min(min_tfs, len(avail_tfs))            # mevcut TF sayısına göre nazikçe sınırla
    conds, used_keys, used_tfs, cur = [], set(), set(), base
    for step in range(max_conds):
        deficit = need - len(used_tfs)
        force_new_tf = deficit > 0 and (max_conds - step) <= deficit   # kalan adım = açık → zorla
        best = None
        for (k, d, t) in cands:
            if k in used_keys:
                continue
            if force_new_tf and _tf_of(k) in used_tfs:
                continue                           # çeşitlilik için yeni-TF zorunlu
            wr, kept = evaluate(rows, conds + [(k, d, t)])
            if kept < floor:
                continue
            if best is None or wr > best[0]:
                best = (wr, kept, (k, d, t))
        if best is None:
            break
        if best[0] - cur < min_gain and not force_new_tf:
            break                                  # zorlanmadıysa zayıf eklemeyi alma
        conds.append(best[2]); used_keys.add(best[2][0])
        used_tfs.add(_tf_of(best[2][0])); cur = best[0]
    return conds


def nested_cv(rows: list[dict], cands: list[tuple], k=4, **kw) -> tuple | None:
    """Her fold: TRAIN'de keşfet, TEST'te ölç → ağırlıklı dürüst OOS WR."""
    r = rows[:]; random.shuffle(r)
    folds = [r[i::k] for i in range(k)]
    num = den = used = 0
    for i in range(k):
        test = folds[i]
        train = [x for j, f in enumerate(folds) if j != i for x in f]
        rule = discover_rule(train, cands, **kw)
        if not rule:
            continue
        wr, kept = evaluate(test, rule)
        if kept >= 5:
            num += wr * kept; den += kept; used += 1
    return (num / den, den, used) if den else None


def placebo(rows: list[dict], cands: list[tuple], M=120, **kw) -> float:
    """Etiketleri M kez karıştır, aynı aramayı yap → gerçek lift'in p-değeri."""
    base = sum(r["win"] for r in rows) / len(rows)
    real_rule = discover_rule(rows, cands, **kw)
    real_lift = (evaluate(rows, real_rule)[0] - base) if real_rule else 0.0
    ge = 0
    for _ in range(M):
        labels = [r["win"] for r in rows]
        random.shuffle(labels)
        shuf = [{"win": labels[i], "ind": rows[i]["ind"]} for i in range(len(rows))]
        rule = discover_rule(shuf, cands, **kw)
        lift = (evaluate(shuf, rule)[0] - base) if rule else 0.0
        if lift >= real_lift - 1e-9:
            ge += 1
    return ge / M


def combo_report(rows: list[dict], title: str, max_conds=3, min_n=60, min_tfs=1) -> None:
    n = len(rows)
    mode = f" [zorunlu ≥{min_tfs} TF]" if min_tfs > 1 else ""
    print("=" * 78)
    print(f"ÇOK-GÖSTERGE FİLTRE{mode} — {title} | n={n}")
    print("=" * 78)
    if n < min_n:
        print(f"  n<{min_n} — çok-gösterge keşfi overfit'e açık, atlandı.")
        return
    base = sum(r["win"] for r in rows) / n
    cands = candidates(rows)
    if not cands:
        print("  aday gösterge yok."); return
    avail_tfs = {_tf_of(k) for (k, _, _) in cands}
    if min_tfs > 1 and len(avail_tfs) < min_tfs:
        print(f"  ⚠ sadece {sorted(avail_tfs)} TF mevcut — ≥{min_tfs} TF zorlanamıyor "
              f"(canlıda data_recorder çok-TF besler).")
    rule = discover_rule(rows, cands, max_conds=max_conds, min_tfs=min_tfs)
    if not rule:
        print(f"  base WR={base*100:.0f}% — anlamlı kombinasyon kuralı bulunamadı.")
        return
    wr, kept = evaluate(rows, rule)
    cv = nested_cv(rows, cands, max_conds=max_conds, min_tfs=min_tfs)
    p = placebo(rows, cands, M=120, max_conds=max_conds, min_tfs=min_tfs)

    tfs_used = sorted({_tf_of(k) for k, _, _ in rule})
    print(f"  base WR={base*100:.0f}%  ({n} işlem)  | kuraldaki TF'ler: {tfs_used}")
    print(f"  KURAL: " + "  AND  ".join(f"{k} {d} {t:.4g}" for k, d, t in rule))
    print(f"  in-sample : WR {wr*100:.0f}%  ({kept}/{n} işlem, +{(wr-base)*100:.0f}pp)")
    if cv:
        print(f"  nested-CV : WR {cv[0]*100:.0f}%  (DÜRÜST OOS, {cv[2]}/4 fold, {cv[1]} test işlemi)")
    else:
        print(f"  nested-CV : foldlarda yeterli işlem kalmadı")
    verdict = ("✅ GERÇEK görünüyor" if p < 0.05 else
               "⚠️ SINIRDA" if p < 0.20 else "❌ SAHTE/overfit riski yüksek")
    print(f"  placebo p : {p:.3f}  → {verdict}")
    print(f"  → Güven: in-sample değil, nested-CV WR + placebo p'ye bak. "
          f"CV≈base veya p yüksekse kuralı DEPLOY ETME.")
