"""
model_compare.py — Opus 4.8 vs Fable 5: aynı veriye iki model, hangisi iyi karar veriyor?
=============================================================================
Her kararda Opus (asıl/canlı) ve Fable5 (gölge) AYNI prompt'u aldı; kararları ayrı grade
edildi. Bu araç ikisini kıyaslar:

 [1] KARAR ANLAŞMASI: iki model ne sıklıkla aynı şeyi diyor (action + yön)?
 [2] AÇILAN İŞLEM KALİTESİ: her modelin OPEN WR/EV (kendi açtıklarında).
 [3] SEÇİCİLİK: kim daha çok açıyor (WAIT oranı) — biri fazla agresif mi?
 [4] AYRIŞMA KİMİN LEHİNE: sadece biri OPEN dediğinde, o işlem kazandı mı?
     (bir modelin diğerinin kaçırdığı kazananı yakalaması = o modelin katkısı)

Not: Fable gölge (canlı değil) — sadece ölçüm. İyi çıkarsa DECIDE_MODEL/SHADOW_MODEL
değiştirilebilir. Kanıt-kapısı: yeterli örnek + net fark; yoksa 'ayırt edilemez'.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL, DECIDE_MODEL, SHADOW_MODEL  # noqa: E402

MIN_N = 12


def _load():
    if not JOURNAL_JSONL.exists():
        return []
    return [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]


def _act(d):
    return str((d or {}).get("action", "")).upper()


def _wr_ev(items):
    """items: [(outcome, pnl_r, rr)]. WIN/LOSS olanlar."""
    g = [(o, p, rr) for o, p, rr in items if o in ("WIN", "LOSS")]
    if not g:
        return None
    w = sum(1 for o, _, _ in g if o == "WIN")
    ev = sum((p if p is not None else (rr if o == "WIN" else -1.0)) for o, p, rr in g) / len(g)
    return w, len(g), 100 * w / len(g), ev


def main():
    rows = [r for r in _load() if r.get("shadow_model")]   # yalnız gölge-model'li kayıtlar
    print("=" * 68)
    print(f"MODEL KIYAS — {DECIDE_MODEL} (asıl) vs {SHADOW_MODEL or 'gölge(tarihsel)'} (gölge)")
    print("=" * 68)
    print(f"Gölge-model'li karar: {len(rows)}")
    if len(rows) < MIN_N:
        print(f"\n⏳ yetersiz ({len(rows)}/{MIN_N}) — gölge-model YENİ; decider çalıştıkça dolar.")
        return

    # her kayıt: opus kararı (decision) vs fable (shadow_model.decision)
    both, agree_act, agree_dir = 0, 0, 0
    opus_trades, fable_trades = [], []
    opus_only_win = opus_only_n = fable_only_win = fable_only_n = 0
    opus_opens = fable_opens = 0

    for r in rows:
        od = r.get("decision") or {}
        sm = r.get("shadow_model") or {}
        fd = sm.get("decision") or {}
        oa, fa = _act(od), _act(fd)
        if not oa or not fa:
            continue
        both += 1
        if oa == fa:
            agree_act += 1
            if oa != "OPEN" or od.get("direction") == fd.get("direction"):
                agree_dir += 1
        if oa == "OPEN":
            opus_opens += 1
        if fa == "OPEN":
            fable_opens += 1
        # trade sonuçları
        if r.get("outcome") in ("WIN", "LOSS"):
            opus_trades.append((r["outcome"], r.get("pnl_r"), (r.get("trade") or {}).get("rr", 0.667)))
        if sm.get("outcome") in ("WIN", "LOSS"):
            fable_trades.append((sm["outcome"], sm.get("pnl_r"), (sm.get("trade") or {}).get("rr", 0.667)))
        # ayrışma: sadece biri OPEN
        if oa == "OPEN" and fa != "OPEN" and r.get("outcome") in ("WIN", "LOSS"):
            opus_only_n += 1; opus_only_win += (r["outcome"] == "WIN")
        if fa == "OPEN" and oa != "OPEN" and sm.get("outcome") in ("WIN", "LOSS"):
            fable_only_n += 1; fable_only_win += (sm["outcome"] == "WIN")

    print(f"\n[1] KARAR ANLAŞMASI (n={both})")
    print(f"    Aynı aksiyon (OPEN/WAIT): {100*agree_act/both:.0f}%")
    print(f"    Aynı aksiyon+yön:         {100*agree_dir/both:.0f}%")

    # SHADOW_MODEL=None olabilir (canlı gölge kapalı, tarihsel kayıtlar analiz ediliyor) →
    # None'ı formatlamak TypeError veriyordu (2026-07-09 paket denetiminde bulunan çökme).
    shadow_name = SHADOW_MODEL or "gölge(tarihsel)"
    print("\n[2] AÇILAN İŞLEM KALİTESİ (kendi OPEN'larında)")
    for name, tr in ((str(DECIDE_MODEL), opus_trades), (shadow_name, fable_trades)):
        res = _wr_ev(tr)
        print(f"    {name:<16} " + (f"WR {res[2]:.0f}% ({res[0]}/{res[1]})  EV {res[3]:+.3f}R" if res else "grade'li OPEN yok"))

    print("\n[3] SEÇİCİLİK (kim daha çok açıyor)")
    print(f"    {DECIDE_MODEL}: {opus_opens}/{both} OPEN ({100*opus_opens/both:.0f}%)  ·  "
          f"{SHADOW_MODEL or 'gölge'}: {fable_opens}/{both} OPEN ({100*fable_opens/both:.0f}%)")

    print("\n[4] AYRIŞMA KİMİN LEHİNE (yalnız biri OPEN dediğinde kazandı mı)")
    if opus_only_n:
        print(f"    Sadece {DECIDE_MODEL} açtı: {opus_only_win}/{opus_only_n} kazandı ({100*opus_only_win/opus_only_n:.0f}%)")
    if fable_only_n:
        print(f"    Sadece {SHADOW_MODEL or 'gölge'} açtı: {fable_only_win}/{fable_only_n} kazandı ({100*fable_only_win/fable_only_n:.0f}%)")
    if not opus_only_n and not fable_only_n:
        print("    (henüz ayrışan grade'li OPEN yok)")

    # verdikt
    ro, rf = _wr_ev(opus_trades), _wr_ev(fable_trades)
    print("\n[VERDİKT]")
    if ro and rf and min(ro[1], rf[1]) >= MIN_N:
        d = rf[3] - ro[3]
        if abs(d) < 0.05:
            print(f"    İki model ~denk (EV farkı {d:+.3f}R). Fable ~4× ucuz → maliyet için Fable düşünülebilir.")
        elif d > 0:
            print(f"    ⚡ Fable5 daha iyi (+{d:.3f}R/işlem) VE ucuz → DECIDE_MODEL=fable dene.")
        else:
            print(f"    Opus daha iyi ({d:+.3f}R/işlem) → asıl model olarak kalsın.")
    else:
        print(f"    Grade'li OPEN az (Opus {ro[1] if ro else 0}, Fable {rf[1] if rf else 0}) — daha çok veri gerek.")


if __name__ == "__main__":
    main()
