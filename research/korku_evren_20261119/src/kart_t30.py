"""kart_t30.py — K1-T30 paketi (TWAP ≤ −%0,3 ∧ son saat < 0, OPEX vetolu, XP) için 2. KURAL kartı + giriş sonrası düşüş (MAE) istatistikleri.
Birincil ölçüm Dukascopy NDX 1m 2018-26 (giriş 16:00 açılışı + spread); ikincil MT5 NAS100 M30. Çıktı:
  backend/data/evolution/go_live_cards/ndx_korku_t30_paket.json, results/t30_islemler.csv, results/t30_dusus.json
python kart_t30.py
"""
from __future__ import annotations

import json
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

import esik as E

warnings.filterwarnings("ignore")
CARD = E.ROOT / "backend/data/evolution/go_live_cards/ndx_korku_t30_paket.json"
T30 = E.CELLS["T30"]


def full_build(b, step, name) -> pd.DataFrame:
    orig = E.VR.entry_features

    def patched(bb, ss, ev=None):
        dp, f, _ = orig(bb, ss, ev)
        return dp, f, T30(f).fillna(False)
    E.VR.entry_features = patched
    try:
        t = E.VR.build(b, step, name)
    finally:
        E.VR.entry_features = orig
    t = t[(t.d <= E.CUT) & ~t.opex_k.isin([0, 1, 2])].reset_index(drop=True)
    # icra / sürtünme: giriş 16:00 + 1 dk (sonraki M1 açılışı + spread) ve spread ×1,5
    tt, o, sp = b.t.values, b.o.values, b.sp.values
    late, s15 = [], []
    for r in t.itertuples():
        u0 = E.VR.ts(r.d, 16, 0)
        i0 = int(np.searchsorted(tt, u0))
        i1 = int(np.searchsorted(tt, u0 + 60)) if step == 60 else i0 + 1
        ask, ask_l, ask_s = r.giris, o[i1] + sp[i1], o[i0] + 1.5 * sp[i0]
        g = r.net + E.VR.FIN * (r.cikis - r.d).days               # brüt (bp) → çıkış/giriş
        late.append((g / 1e4 + 1) * ask / ask_l * 1e4 - 1e4 - E.VR.FIN * (r.cikis - r.d).days)
        s15.append((g / 1e4 + 1) * ask / ask_s * 1e4 - 1e4 - E.VR.FIN * (r.cikis - r.d).days)
    return t.assign(net_gec=late, net_s15=s15)


def single_position(t: pd.DataFrame) -> pd.DataFrame:
    keep, busy = [], pd.Timestamp("1900-01-01")
    for r in t.sort_values("d").itertuples():
        if r.d >= busy:
            keep.append(r.Index)
            busy = r.cikis
    return t.loc[keep]


def card_checks(t: pd.DataFrame) -> dict:
    v = t.net.values
    h = len(t) // 2
    blocks = pd.to_datetime(t.d).dt.to_period("M").astype(str).values
    ub = np.unique(blocks)
    P = float(np.mean([np.concatenate([v[blocks == u] for u in E.RNG.choice(ub, len(ub))]).mean() > 0 for _ in range(2000)]))
    sp = single_position(t)
    gec = t.net_gec.mean()
    return {"1_hacim": {"deger": len(t), "gecti": len(t) >= 150},
            "2_beklenti": {"deger": f"{v.mean():+.1f} bp P(EV>0) {P:.3f}", "gecti": bool(v.mean() > 0 and P >= 0.9)},
            "3_kararlilik": {"deger": f"{t.net.iloc[:h].mean():+.1f} / {t.net.iloc[h:].mean():+.1f}",
                             "gecti": bool(t.net.iloc[:h].mean() >= 0 and t.net.iloc[h:].mean() >= 0)},
            "4_surtunme": {"deger": f"spread ×1,5 {t.net_s15.mean():+.1f}", "gecti": bool(t.net_s15.mean() > 0)},
            "5_icra": {"deger": f"16:00 {v.mean():+.1f} vs sonraki mum açılışı {gec:+.1f}",
                       "gecti": bool(gec > 0 and v.mean() - gec < 0.5 * abs(v.mean()))},
            "6_sira_bagimli": {"deger": f"tek pozisyon {sp.net.mean():+.1f} (n {len(sp)})", "gecti": bool(sp.net.mean() > 0)}}


def dusus(t: pd.DataFrame) -> dict:
    """MAE: girişten çıkışa kadar fiyatın girişin ne kadar altına indiği (bp, giriş ask'ına göre)."""
    m = t.mae.values
    w, l = t[t.net > 0], t[t.net <= 0]

    def s(x):
        return {"n": len(x), "ort": round(float(x.mae.mean()), 1), "medyan": round(float(x.mae.median()), 1),
                "en_derin_%10": round(float(np.percentile(x.mae, 10)), 1), "en_derin": round(float(x.mae.min()), 1),
                "dibe_saat_medyan": round(float(x.mae_saat.median()), 1)}
    return {"tum": s(t), "kazananlar": s(w), "kaybedenler": s(l),
            "dagilim_%": {k: round(float((m <= -k).mean() * 100), 1) for k in (25, 50, 100, 200, 300, 500)},
            "en_kotu_islem_net": round(float(t.net.min()), 1), "en_derin_gun": str(t.loc[t.mae.idxmin(), "d"].date()),
            "mfe_ort": round(float(t.mfe.mean()), 1), "tutus_gun_ort": round(float(t.tutus_gun.mean()), 2)}


def main() -> None:
    F = E.feeds()
    out = {}
    for nm in ("DUKA_NDX", "MT5_NAS100"):
        b, st = F[nm]
        t = full_build(b, st, nm)
        out[nm] = {"islem": t, "checks": card_checks(t), "dusus": dusus(t)}
        t.to_csv(E.RES / f"t30_islemler_{nm}.csv", index=False)
        print(nm, len(t), "işlem", round(t.net.mean(), 1), "bp", {k: c["gecti"] for k, c in out[nm]["checks"].items()}, flush=True)
        print("   ", {k: c["deger"] for k, c in out[nm]["checks"].items()})
        print("   düşüş:", out[nm]["dusus"], flush=True)
    d, m = out["DUKA_NDX"], out["MT5_NAS100"]
    t = d["islem"]
    yrs = {int(y): round(float(g.net.mean()), 1) for y, g in t.groupby(t.d.dt.year)}
    ok = all(c["gecti"] for c in d["checks"].values())
    cs = np.cumsum(t.net.values)
    card = {"scope": "ndx_korku_t30_paket", "tarih": datetime.now().isoformat(timespec="seconds"),
            "aciklama": "NDX korku gecesi paketi, T30 eşiği: 16:00 ET fiyatı 09:30'dan beri TWAP'ın ≥ %0,3 altında ∧ 15:00→16:00 aşağı → 16:00 AL. "
                        "OPEX vetosu (vadeye 0–2 işlem günü kala açma). Çıkış XP: sonraki ilk 16:00'da fiyat önceki 16:00'nın üstündeyse, en geç 5. işlem günü. TP/SL yok.",
            "ana_olcum": "Dukascopy NDX 1m 2018-04 → 2026-11-05, giriş 16:00 açılışı + spread, çıkış 16:00 açılışı, finansman; ikincil MT5 NAS100 M30",
            "olay": len(t), "ort_bp": round(float(t.net.mean()), 1), "isabet": round(float((t.net > 0).mean()), 3),
            "checks": d["checks"], "kart_6_6": ok, "mt5_nas100_checks": m["checks"],
            "risk": {"std_bp": round(float(t.net.std()), 1), "en_kotu_bp": round(float(t.net.min()), 1),
                     "maxDD_bp": round(float((cs - np.maximum.accumulate(cs)).min()), 1), "yillar": yrs},
            "dusus_MAE": {"DUKA_NDX": d["dusus"], "MT5_NAS100": m["dusus"]},
            "verdict": "LIVE" if ok else "SHADOW", "sinif": "B",
            "verdict_gerekce": "EV-01: eklenen işlemler KEŞİF +32,9 / TEST +38,9 bp, 5/5 beslemede paket Sharpe artar. Canlıya alma: kullanıcı kararı 2026-11-19.",
            "kanit": "research/korku_evren_20261119/ (PROTOCOL, RAPOR; defter §2.101 EV-01); paket §2.95 kapı 03"}
    CARD.write_text(json.dumps(card, indent=1, ensure_ascii=False, default=str))
    (E.RES / "t30_dusus.json").write_text(json.dumps({k: v["dusus"] for k, v in out.items()}, indent=1, ensure_ascii=False))
    print("KART", card["verdict"], "6/6" if ok else "", "yıllar", yrs, "maxDD", card["risk"]["maxDD_bp"])


if __name__ == "__main__":
    main()
