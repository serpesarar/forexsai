"""
integrity_audit.py — "bu WR gerçek mi, şişirilmiş mi?" sorusunun ÖLÇÜLMÜŞ cevabı.
=============================================================================
Kullanıcı sorusu (2026-07-28): "başarı oranı kesinlikle doğru mu, geleceği görme ya da
bu tarz bir şey yok değil mi?"

Bu script iddia etmez, SAYAR. Beş sızıntı/şişme vektörünü tek tek test eder:
  1. GELECEĞİ GÖRME: sonuç zamanı girişten önce olan kayıt var mı? (olmamalı)
  2. TEMİZLİK YANLILIĞI: load_journal(clean=True) atılan kayıtlar sistematik KAYIP mı?
     (atılanlar kayıpsa, temiz WR şişer)
  3. EXPIRE muhasebesi: WR paydasından düşen nötrler ne kadar, hangi yöne eğilimli?
  4. AYNI-BAR ÇAKIŞMASI: TP ve SL aynı barda → LOSS sayılıyor; oranı ne?
     (bu KONSERVATİF yön; oran yüksekse gerçek belirsizlik yüksek demektir)
  5. ANINDA-KAZANÇ: 1 barda biten kazançlar (wick-dokunuşu şüphesi) oranı.
Ayrıca sürtünme (spread) ve icra gerçekliği hakkında ölçülebilen ne varsa raporlar.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL, load_journal  # noqa: E402


def _raw():
    return [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]


def _wr(rs):
    g = [r for r in rs if r.get("outcome") in ("WIN", "LOSS")]
    if not g:
        return 0.0, 0
    return 100 * sum(1 for r in g if r["outcome"] == "WIN") / len(g), len(g)


def _cf_wr(rs):
    g = [r for r in rs if r.get("cf_outcome") in ("WIN", "LOSS")]
    if not g:
        return 0.0, 0
    return 100 * sum(1 for r in g if r["cf_outcome"] == "WIN") / len(g), len(g)


def main():
    raw, clean = _raw(), load_journal(clean=True)
    ids = {(r.get("ts"), r.get("symbol")) for r in clean}
    dropped = [r for r in raw if (r.get("ts"), r.get("symbol")) not in ids]
    print("=" * 74)
    print("DECIDER BAŞARI ORANI — SIZINTI / ŞİŞME DENETİMİ")
    print("=" * 74)
    print(f"ham kayıt {len(raw)} | temiz {len(clean)} | temizlikte atılan {len(dropped)}\n")

    # ── 1. geleceği görme
    print("[1] GELECEĞİ GÖRME TESTİ (sonuç zamanı < karar zamanı olan kayıt)")
    bad = 0
    for r in raw:
        oa = r.get("outcome_at")
        if oa:
            try:
                if datetime.fromisoformat(oa) < datetime.fromisoformat(r["ts"]):
                    bad += 1
            except Exception:
                pass
    tr_bad = sum(1 for r in raw if (r.get("trade") or {}).get("entry_bar_time") and
                 (r["trade"]["entry_bar_time"] > datetime.fromisoformat(r["ts"]).timestamp() + 900))
    print(f"    sonuç-önce-karar: {bad}  (0 olmalı)")
    print(f"    giriş barı karardan >15dk İLERİDE: {tr_bad}  (0 olmalı — ileri bar = sızıntı)")

    # ── 2. temizlik yanlılığı
    print("\n[2] TEMİZLİK YANLILIĞI (atılan kayıtlar sistematik kayıp mı?)")
    rw, rn = _wr(raw); cw, cn = _wr(clean); dw, dn = _wr(dropped)
    print(f"    HAM   WR {rw:5.1f}%  (n={rn})")
    print(f"    TEMİZ WR {cw:5.1f}%  (n={cn})   ← raporlanan")
    print(f"    ATILAN WR {dw:5.1f}%  (n={dn})")
    if dn:
        print(f"    → temizlik WR'ı {cw - rw:+.1f}pp değiştiriyor. Atılanlar "
              f"{'KAYIP ağırlıklı → temiz WR ŞİŞİK' if dw < rw else 'kazanç ağırlıklı → temiz WR muhafazakâr'}")
    rcw, rcn = _cf_wr(raw); ccw, ccn = _cf_wr(clean); dcw, dcn = _cf_wr(dropped)
    print(f"    (karşı-olgu) ham {rcw:.1f}% n={rcn} | temiz {ccw:.1f}% n={ccn} | atılan {dcw:.1f}% n={dcn}")

    # ── 3. EXPIRE muhasebesi
    print("\n[3] EXPIRE (48h'te sonuçlanmayan) — WR paydasından düşüyor")
    for tag, rs in (("gerçek", clean), ):
        c = Counter(r.get("outcome") for r in rs if r.get("outcome"))
        exp = c.get("EXPIRE", 0); tot = c.get("WIN", 0) + c.get("LOSS", 0) + exp
        print(f"    {tag}: WIN {c.get('WIN',0)} | LOSS {c.get('LOSS',0)} | EXPIRE {exp} "
              f"→ EXPIRE payı %{100*exp/max(tot,1):.1f}")
        cc = Counter(r.get("cf_outcome") for r in rs if r.get("cf_outcome"))
        cexp = cc.get("EXPIRE", 0); ctot = cc.get("WIN", 0) + cc.get("LOSS", 0) + cexp
        print(f"    karşı-olgu: WIN {cc.get('WIN',0)} | LOSS {cc.get('LOSS',0)} | EXPIRE {cexp} "
              f"→ EXPIRE payı %{100*cexp/max(ctot,1):.1f}")

    # ── 4/5. yol metrikleri
    print("\n[4] AYNI-BAR TP+SL ÇAKIŞMASI (kod LOSS sayıyor = konservatif)")
    print("[5] ANINDA SONUÇ (1 barda biten) — wick-dokunuşu şüphesi")
    fast_w = fast_l = 0
    b2o = defaultdict(int)
    amb = 0
    for r in clean:
        p = r.get("path") or {}
        b = p.get("bars_to_outcome")
        if b is None:
            continue
        b2o[min(b, 10)] += 1
        if b <= 1:
            if r.get("outcome") == "WIN":
                fast_w += 1
            elif r.get("outcome") == "LOSS":
                fast_l += 1
        # aynı bar çakışması: MAE=1.0 (SL) ve MFE tp mesafesine ulaşmış
        if p.get("mae_r") and p["mae_r"] >= 1.0 and (p.get("tp_progress") or 0) >= 1.0:
            amb += 1
    tot_p = sum(b2o.values())
    print(f"    aynı-barda ikisi de değmiş (LOSS sayıldı): {amb} / {tot_p} = %{100*amb/max(tot_p,1):.1f}")
    print(f"    1 barda biten: WIN {fast_w} / LOSS {fast_l}  "
          f"(WIN oranı %{100*fast_w/max(fast_w+fast_l,1):.0f} — %50'nin çok üstüyse şüphelen)")
    print("    bar/sonuç dağılımı:", dict(sorted(b2o.items())))

    # ── sürtünme
    print("\n[6] SÜRTÜNME (spread) — WR'ın ölçmediği maliyet")
    sp = [(r.get("trade") or {}).get("spread_atr") for r in clean]
    sp = [s for s in sp if s]
    nets = [r.get("pnl_r_net") for r in clean if r.get("pnl_r_net") is not None]
    if sp:
        print(f"    ölçülen spread kaydı: {len(sp)} | ortalama {sum(sp)/len(sp):.4f}×ATR")
    else:
        print("    ölçülen spread kaydı YOK (2026-07-27'den önceki tüm kayıtlar sürtünmesiz)")
    print(f"    net-P&L hesaplanmış kayıt: {len(nets)}")
    print("    → Bu tarihten önceki TÜM WR/EV rakamları spread ve slippage İÇERMEZ.")

    print("\n" + "=" * 74)
    print("NOT: shadow modda execute() stub — hiçbir emir MT5'e gitmedi. Bu sayılar")
    print("KAĞIT ÜSTÜ dolum varsayar (TP'ye DOKUNUŞ = dolum). Gerçek hesapta doldurulmama,")
    print("kayma ve komisyon bu rakamların ALTINDA sonuç verir.")
    print("=" * 74)


if __name__ == "__main__":
    main()
