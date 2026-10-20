"""SQZ filtresi (B14) İLERİ dönem kartı — her çalıştırmada 2026-08-28 sonrası gerçek bot NDX işlemleriyle yeniden ölçer.

python3 research/sikisma_derin_20261020/ileri_kart.py           # islem_otopsi'yi tazeler + kartı yazar
→ backend/data/evolution/go_live_cards/sqz_filter_ndx.json

Ön-kayıtlı ölçütler (2026-10-20; değiştirilmez — değişirse yeni ad + defter satırı):
  1 hacim         ileri dönemde SQZ ölçülebilen NDX bot işlemi ≥ 150
  2 H1            gün-blok P(Δ<0) ≥ %95   (Δ = ortR sıkışık − ortR diğer, eşik 1,00)
  3 saat-içi      saat-dilimi tabakalı Δ için P(<0) ≥ %90   (sıkışma = saat vekili değil)
  4 engel kazancı gün-blok P(kurtarılan R > 0) ≥ %90   (blok modu; ağırlık modu ayrıca raporlanır)
  5 kararlılık    ileri dönemin iki kronolojik yarısında da Δ < 0
Hepsi geçerse verdikt CANLI_ADAYI (kullanıcı kararı + bayrak SQZ_FILTER_BLOCK); aksi hâlde GÖLGE.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import core as C
import exp5 as X5
import exp6 as X6

FWD = pd.Timestamp("2026-08-28", tz="UTC")
CARD = C.ROOT / "backend" / "data" / "evolution" / "go_live_cards" / "sqz_filter_ndx.json"
MIN_N, P_H1, P_STRAT, P_SAVED = 150, 0.95, 0.90, 0.90


def fresh_trades() -> pd.DataFrame:
    days = (pd.Timestamp.now(tz="UTC") - FWD).days + 2
    out = subprocess.run([sys.executable, "-m", "scripts.islem_otopsi", "--symbol", "NDX", "--days", "3",
                          "--base-days", str(days), "--max-cards", "0", "--trade-charts", "0"],
                         cwd=C.ROOT, capture_output=True, text=True, check=True).stdout
    path = [ln.split("RAPOR: ")[1] for ln in out.splitlines() if ln.startswith("RAPOR: ")][-1]
    d = pd.read_csv(path.replace("rapor.md", "islemler.csv"))
    d = d[d.outcome.isin(["TP", "SL", "BE", "DIGER_+", "DIGER_-"])]
    return pd.DataFrame({"t": pd.to_datetime(d.entry_utc, utc=True), "s": np.where(d.direction == "BUY", 1, -1),
                         "fam": d.family, "R": d.r_exit.astype(float), "net": d.net})


def main() -> None:
    tr = fresh_trades()
    tr = tr[(tr.t >= FWD) & ~tr.fam.isin(["DECIDER", "MANUEL"])]
    F = C.compute_feats(C.bars_snapshots("NDX.INDX", "2026-08-20"))
    tr = tr.reset_index(drop=True)
    d = pd.concat([tr, C.feats_at(F, tr.t).reset_index(drop=True)], axis=1)
    d = d[np.isfinite(d.R) & d.atr_14_100.notna()].sort_values("t").reset_index(drop=True)
    st = X5.stats(d, "ileri")
    sr = X6.run(d, "ileri")
    R, sq = d.R.to_numpy(float), (d.atr_14_100 < 1).to_numpy()
    p_saved = C.boot_saved(R, sq, C.day_ids(d.t))
    h = len(d) // 2
    halves = [float(R[:h][sq[:h]].mean() - R[:h][~sq[:h]].mean()), float(R[h:][sq[h:]].mean() - R[h:][~sq[h:]].mean())]
    checks = {
        "1_hacim": {"deger": len(d), "esik": f"≥{MIN_N}", "gecti": len(d) >= MIN_N},
        "2_H1": {"deger": f"Δ={st['Δ']:+.3f} P(Δ<0)=%{100 * st['P(Δ<0)']:.1f}", "esik": f"P≥%{100 * P_H1:.0f}",
                 "gecti": st["P(Δ<0)"] >= P_H1},
        "3_saat_ici": {"deger": f"Δ_tab={sr['saat-içi Δ']:+.3f} P=%{100 * sr['P(saat-içi Δ<0)']:.1f}",
                       "esik": f"P≥%{100 * P_STRAT:.0f}", "gecti": sr["P(saat-içi Δ<0)"] >= P_STRAT},
        "4_engel_kazanci": {"deger": f"kurt_R={-R[sq].sum():+.2f} P=%{100 * p_saved:.1f}; ağırlık modu "
                            f"{st['ağırlık kazancı R']:+.2f}R P=%{100 * st['P(kazanç>0)']:.1f}",
                            "esik": f"P≥%{100 * P_SAVED:.0f}", "gecti": p_saved >= P_SAVED},
        "5_kararlilik": {"deger": f"yarılar Δ {halves[0]:+.3f} / {halves[1]:+.3f}", "esik": "ikisi de <0",
                         "gecti": all(x < 0 for x in halves)},
    }
    ok = all(c["gecti"] for c in checks.values())
    card = {"scope": "sqz_filter_ndx", "aciklama": "B14 sıkışma filtresi: ATR14(1m)/ATR100(1m) < 1,00 → NDX girişi engel",
            "tarih": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ileri_baslangic": "2026-08-28",
            "olay": len(d), "sikisik": int(sq.sum()), "ortR_sikisik": round(float(R[sq].mean()), 3),
            "ortR_diger": round(float(R[~sq].mean()), 3), "checks": checks,
            "verdikt": "CANLI_ADAYI" if ok else "GÖLGE",
            "kaynak": "research/sikisma_derin_20261020/ (SONUC.md, ön-kayıt PROTOCOL.md + ileri_kart.py başlığı)"}
    CARD.write_text(json.dumps(card, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(card, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
