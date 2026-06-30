"""
calibration.py — Tahminler gerçeği tutuyor mu? (güvenilirlik / reliability diagram)
=============================================================================
İki kalibrasyon sorusu (öğrenme sağlığı):

 [1] KANIT base-rate'leri kalibre mi? evidence "bu kurulum %85 kazanır" dediğinde canlı
     gerçekten ~%85 mi geliyor? Sistematik altındaysa → evidence_tables ESKİMİŞ/iyimser
     (Plan #5 tazeleme sinyali). Reliability diagram + ECE (kalibrasyon hatası) + yön (bias).

 [2] size_factor GÜVENİLİR mi? Opus 0.8 derken 0.4'ten gerçekten çok mu kazanıyor?
     Monoton artıyorsa konviksiyon GERÇEK; düzse gürültü (sizing değer katmıyor).

Veri: her gate-fired kayıttan primary_dir tahmini evidence_tables'tan YENİDEN hesaplanır
(dirs_live + tablo) → cf_outcome ile eşlenir. OPEN+WAIT hepsi → maksimum örnek.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL  # noqa: E402
import evidence as ev  # noqa: E402

MIN_N = 8           # bir kovada minimum örnek
MIN_TOTAL = 15      # genel analiz için minimum
_TABLES = ev.load_tables()


def _load():
    if not JOURNAL_JSONL.exists():
        return []
    return [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]


def _predicted_wr(symbol, direction, lf) -> float | None:
    """evidence_tables'tan bu kurulumun TAHMİN edilen WR'ı (en spesifik hücre, OOS tercih)."""
    if not lf:
        return None
    pack = ev.evidence_pack(symbol, direction, lf, _TABLES)
    # öncelik: rev_chan bucket → rev_vwap bucket → gate_setup (hep OOS tercih)
    for key in ("rev_chan_bucket", "rev_vwap_bucket"):
        h = (pack.get(key) or {}).get("hist")
        if h and h.get("n", 0) >= 10:
            return h.get("oos_wr") if h.get("oos_wr") is not None else h.get("wr")
    g = pack.get("gate_setup")
    if g:
        return g.get("oos_wr") if g.get("oos_wr") is not None else g.get("wr")
    return None


def _cf_pairs(rows):
    """(tahmin_wr, kazandı?) çiftleri — gate-fired + cf grade'li kayıtlardan."""
    pairs = []
    for e in rows:
        cf = e.get("counterfactual") or {}
        if not (cf.get("live") or {}).get("gate_fired"):
            continue
        if e.get("cf_outcome") not in ("WIN", "LOSS"):
            continue
        lf = cf.get("live") or (e.get("dirs_live") or {}).get(cf.get("dir"))
        pred = _predicted_wr(e["symbol"], cf.get("dir"), lf)
        if pred is not None:
            pairs.append((pred, 1 if e["cf_outcome"] == "WIN" else 0, e["symbol"]))
    return pairs


def reliability(pairs):
    """Reliability diagram: tahmin kovası → gerçekleşen WR. + ECE + bias."""
    bins = [(50, 60), (60, 70), (70, 80), (80, 90), (90, 101)]
    print("    tahmin kovası   söz~     gerçek    n    sapma")
    print("    " + "-" * 48)
    ece, bias_sum, tot = 0.0, 0.0, 0
    for lo, hi in bins:
        sel = [(p, w) for p, w, _ in pairs if lo <= p < hi]
        if len(sel) < MIN_N:
            if sel:
                print(f"    {lo}-{hi if hi <= 100 else 100}%        (n={len(sel)} az)")
            continue
        n = len(sel); obs = 100 * sum(w for _, w in sel) / n
        pred_mid = sum(p for p, _ in sel) / n
        dev = obs - pred_mid
        flag = "✓" if abs(dev) <= 7 else ("⚠" if abs(dev) <= 14 else "🔴 şişik" if dev < 0 else "🔴 düşük")
        print(f"    {lo}-{hi if hi <= 100 else 100}%        ~{pred_mid:.0f}%    {obs:>5.0f}%   {n:>3}   {dev:+.0f}pp  {flag}")
        ece += abs(dev) * n; bias_sum += dev * n; tot += n
    if tot:
        ece /= tot; bias = bias_sum / tot
        yon = ("kanıt base'leri ŞİŞİK (canlı altında) → evidence_tables TAZELE (Plan #5)" if bias < -5
               else "kanıt base'leri DÜŞÜK (canlı üstünde) → muhafazakar, fırsat var" if bias > 5
               else "kanıt base'leri kalibre ✓")
        print(f"    → Ortalama kalibrasyon hatası (ECE): {ece:.1f}pp | bias {bias:+.1f}pp → {yon}")
    return tot


def size_reliability(rows):
    """size_factor kovaları → gerçek WR (OPEN'lar). Monoton mu = konviksiyon gerçek mi."""
    opens = [e for e in rows if str((e.get("decision") or {}).get("action", "")).upper() == "OPEN"
             and e.get("outcome") in ("WIN", "LOSS")]
    sized = [(e.get("decision", {}).get("size_factor"), 1 if e["outcome"] == "WIN" else 0)
             for e in opens if isinstance((e.get("decision") or {}).get("size_factor"), (int, float))]
    if len(sized) < MIN_TOTAL:
        print(f"    (n az: {len(sized)}/{MIN_TOTAL})"); return
    bins = [(0.0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]
    print("    size kovası    gerçek WR    n")
    print("    " + "-" * 32)
    wrs = []
    for lo, hi in bins:
        sel = [w for s, w in sized if lo <= s < hi]
        if len(sel) < MIN_N:
            if sel:
                print(f"    {lo:.1f}-{min(hi,1.0):.1f}      (n={len(sel)} az)")
            continue
        wr = 100 * sum(sel) / len(sel); wrs.append(wr)
        print(f"    {lo:.1f}-{min(hi,1.0):.1f}      {wr:>6.0f}%   {len(sel)}")
    if len(wrs) >= 2:
        mono = wrs[-1] - wrs[0]
        v = ("konviksiyon GERÇEK (büyük size → çok kazanıyor) ✓" if mono >= 8
             else "TERS (küçük size daha iyi!) 🔴" if mono <= -8
             else "size zayıf sinyal (sizing değer katmıyor) ~")
        print(f"    → en yüksek − en düşük kova: {mono:+.0f}pp → {v}")


def main():
    rows = _load()
    pairs = _cf_pairs(rows)
    print("=" * 60)
    print("KALİBRASYON — tahminler gerçeği tutuyor mu?")
    print("=" * 60)
    print(f"Journal: {len(rows)} | kalibrasyon çifti (gate-fired+grade): {len(pairs)}\n")
    print("[1] KANIT BASE-RATE KALİBRASYONU (evidence ne vaat etti vs ne oldu)")
    if len(pairs) < MIN_TOTAL:
        print(f"    ⏳ yetersiz ({len(pairs)}/{MIN_TOTAL}) — counterfactual'la YENİ, veri biriktikçe dolar.")
    else:
        reliability(pairs)
    print("\n[2] size_factor GÜVENİLİRLİĞİ (Opus konviksiyon → gerçek WR)")
    size_reliability(rows)
    print("\nNot: [1] kanıt şişikse → evidence_tables tazele. [2] monoton değilse → Opus'un")
    print("güveni gürültü; sizing'i sadeleştir. İkisi de sistemin 'kendini tanıması'.")


if __name__ == "__main__":
    main()
