"""
discrimination.py — WIN vs LOSS gösterge ayrıştırması + tek-gösterge filtre keşfi.
Hem retrospektif (yerel veri) hem üretim (Supabase) analizleri bunu kullanır.

rows: list[{"win": bool, "ind": {gösterge: değer}}]
"""
from __future__ import annotations
from typing import Iterable


def auc(wins: list[float], losses: list[float]) -> float:
    """AUC = P(rastgele KAYIP değeri > rastgele KAZANÇ değeri). 0.5=ayrım yok.
    >0.5: yüksek değer KAYIPLA ilişkili. <0.5: yüksek değer KAZANÇLA ilişkili."""
    nw, nl = len(wins), len(losses)
    if nw == 0 or nl == 0:
        return 0.5
    combined = sorted(wins + losses)
    rank = {}
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1] == combined[i]:
            j += 1
        avg = (i + j) / 2 + 1                      # 1-based ortalama rank (tie)
        rank[combined[i]] = avg
        i = j + 1
    rank_sum_loss = sum(rank[v] for v in losses)
    u = rank_sum_loss - nl * (nl + 1) / 2
    return u / (nw * nl)


def _numeric(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# Durağan (normalize/sınırlı) göstergeler — mutlak fiyat seviyeleri (ema/close/bb
# bantları/sar) zaman-konfounduyla SAHTE ayrım verir, onları dışla.
STATIONARY = {"rsi14", "stoch_k", "stoch_d", "adx14", "plus_di", "minus_di",
              "macd_hist", "bb_width", "bb_pct_b", "dist_ema20_atr",
              "dist_ema50_atr", "sar_dist_atr", "atr_pct"}


def _is_stationary(key: str) -> bool:
    return any(key == s or key.endswith("_" + s) for s in STATIONARY)


def best_filter(rows: list[dict], key: str, min_keep: float = 0.30) -> dict | None:
    """Bu göstergede WR'ı en çok artıran tek eşik+yön filtresini bul (≥%min_keep tut)."""
    vals = [(r["ind"][key], bool(r["win"])) for r in rows
            if key in r["ind"] and _numeric(r["ind"][key])]
    n = len(vals)
    if n < 20:
        return None
    base = sum(w for _, w in vals) / n
    best = None
    for thr in sorted({v for v, _ in vals}):
        for d in ("<", ">"):
            kept = [w for v, w in vals if (v < thr if d == "<" else v > thr)]
            if len(kept) < n * min_keep:
                continue
            wr = sum(kept) / len(kept)
            if best is None or wr - base > best["lift"]:
                best = {"thr": round(thr, 4), "dir": d, "wr": wr,
                        "kept": len(kept), "lift": wr - base}
    return {"base_wr": base, "n": n, **best} if best else None


def discriminate(rows: list[dict], min_n: int = 20, stationary_only: bool = True) -> list[dict]:
    """Her gösterge için win/loss ayrımı (AUC + ortalamalar). |AUC-0.5|'e göre sıralı.
    stationary_only: mutlak-fiyat (non-stationary) göstergeleri dışla (sahte ayrım)."""
    keys = set()
    for r in rows:
        keys.update(k for k, v in r["ind"].items() if _numeric(v))
    if stationary_only:
        keys = {k for k in keys if _is_stationary(k)}
    out = []
    for k in sorted(keys):
        wv = [r["ind"][k] for r in rows if r["win"] and k in r["ind"] and _numeric(r["ind"][k])]
        lv = [r["ind"][k] for r in rows if not r["win"] and k in r["ind"] and _numeric(r["ind"][k])]
        if len(wv) < min_n or len(lv) < min_n:
            continue
        a = auc(wv, lv)
        mw = sum(wv) / len(wv); ml = sum(lv) / len(lv)
        out.append({"indicator": k, "auc": round(a, 3), "sep": round(abs(a - 0.5), 3),
                    "win_mean": round(mw, 4), "loss_mean": round(ml, 4),
                    "n_win": len(wv), "n_loss": len(lv)})
    out.sort(key=lambda x: -x["sep"])
    return out


def print_report(rows: list[dict], title: str, top: int = 12) -> None:
    n = len(rows); nwin = sum(1 for r in rows if r["win"])
    print("=" * 78)
    print(f"{title}  |  n={n}  WR={nwin/n*100:.1f}%" if n else f"{title} | veri yok")
    print("=" * 78)
    if n < 40:
        print("  (az örnek — gösterge bazında ayrım güvenilmez, n≥40 önerilir)")
    disc = discriminate(rows)
    if not disc:
        print("  yeterli gösterge örneği yok."); return
    print(f"  {'gösterge':18s} {'AUC':>6s} {'ayrım':>6s} {'WIN ort':>10s} {'LOSS ort':>10s}  yön")
    for d in disc[:top]:
        arrow = "↑değer→KAYIP" if d["auc"] > 0.5 else "↑değer→KAZANÇ"
        print(f"  {d['indicator']:18s} {d['auc']:6.3f} {d['sep']:6.3f} "
              f"{d['win_mean']:10.3f} {d['loss_mean']:10.3f}  {arrow}")
    # en iyi filtre önerileri (ilk 5 ayrıştırıcı gösterge için)
    print(f"\n  EN İYİ TEK-GÖSTERGE FİLTRELER (WR artışı, ≥%30 işlem tutar):")
    seen = 0
    for d in disc:
        bf = best_filter(rows, d["indicator"])
        if bf and bf["lift"] > 0.03:
            print(f"    {d['indicator']:18s} {bf['dir']}{bf['thr']:<9} → WR "
                  f"{bf['base_wr']*100:.0f}%→{bf['wr']*100:.0f}% "
                  f"(+{bf['lift']*100:.0f}pp, {bf['kept']}/{bf['n']} işlem)")
            seen += 1
        if seen >= 6:
            break
    if seen == 0:
        print("    belirgin tek-gösterge filtresi yok (çok-gösterge gerekebilir).")
