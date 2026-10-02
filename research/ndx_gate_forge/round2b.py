"""Tur 2b — tur 2'nin açtığı sorular (SONRADAN kurulan; kendi doğrulamasıyla raporlanır).

F2 Ölçek haritası: 'işleme karşı kanal-z ≥ 2' (fade) etkisi kanal zaman dilimine göre (1/5/15/30/60 dk).
F3 Trend-içi geri çekilme vs bıçak: 5m fade'i H1 trendiyle uyumlu/uyumsuz ayır.
F1 30m-kanal bıçak kapısı: 1m verisinde 5 dönem + bot işlemleri (30m veride 6/6 yıl bulundu).
F4 Kapitülasyon: SELL fiyat önceki RTH dibinin altındayken — stres günü / her gün.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, DATA, ROOT, load_1m, block_boot
from evaluate import load
from final_candidates import lift, conds
from round2 import tf_feats


def main() -> dict:
    b = load_1m()
    d = load(1)
    dec = b.t.to_numpy()[d.i.to_numpy()] + 60
    y = {s: (d[f"R_G80_{s}"] - d.groupby(["period", "utc_h"])[f"R_G80_{s}"].transform("mean")).to_numpy() for s in "BS"}
    days, per = d.ny_date.to_numpy(), d.period.to_numpy()
    z = np.zeros(len(d), bool)
    tr = d.h1_trend.to_numpy()
    out: dict = {"F2 ölçek haritası (fade ≥2σ, R farkı)": {}, "F2 ölçek haritası (trend yönü ≥2σ kovalama)": {}}
    cz = {}
    for tf in (1, 5, 15, 30, 60):
        cz[tf], _ = tf_feats(b, tf, dec)
        c = cz[tf]
        # fade: BUY fiyat kanal dibindeyken (z≤−2), SELL tepedeyken (z≥2)
        out["F2 ölçek haritası (fade ≥2σ, R farkı)"][f"{tf}m (kanal≈{50*tf/60:.0f}s)"] = lift(y, (c <= -2, c >= 2), days, per)
        # kovalama: BUY fiyat kanal tepesindeyken, SELL dibindeyken
        out["F2 ölçek haritası (trend yönü ≥2σ kovalama)"][f"{tf}m"] = lift(y, (c >= 2, c <= -2), days, per)
    c5 = cz[5]
    out["F3 5m fade + H1 trendle UYUMLU (geri çekilme)"] = lift(y, ((c5 <= -2) & (tr > 0), (c5 >= 2) & (tr < 0)), days, per)
    out["F3 5m fade + H1 trende KARŞI (bıçak)"] = lift(y, ((c5 <= -2) & (tr < 0), (c5 >= 2) & (tr > 0)), days, per)
    nyd = pd.to_datetime(d.ny_date)
    C = conds(nyd, d.ny_min.to_numpy(), d.wd.to_numpy(), None)
    k5 = C["K5 Stres-dönüş SELL yok"][1]
    below = d.price.to_numpy() < d.pdl.to_numpy()
    above_pdh = d.price.to_numpy() > d.pdh.to_numpy()
    out["F4 SELL < önceki RTH dibi (tüm günler)"] = lift(y, (z, below), days, per)
    out["F4 SELL < önceki dip & stres günü (kapitülasyon)"] = lift(y, (z, below & k5), days, per)
    out["F4 ayna: BUY > önceki RTH tepesi (tüm günler)"] = lift(y, (above_pdh, z), days, per)
    return out, cz


def bot(cz_tfs=(5, 30, 60)) -> dict:
    t = pd.read_csv(ROOT / "nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv")
    bx = pd.read_csv(DATA / "box_trades_40d.csv")
    bx = bx[bx.symbol == "NAS100"]
    t = pd.concat([t, bx[~bx.position_id.isin(t.position_id)]], ignore_index=True)
    t["ot"] = pd.to_datetime(t.open_time_utc, utc=True)
    t["pts"] = t.profit / t.volume
    t["dec"] = t.ot.dt.floor("min").astype(str) + t.direction
    g = t.groupby("dec").agg(ot=("ot", "first"), side=("direction", "first"), pts=("pts", "mean"), magic=("magic", "first")).reset_index()
    b = load_1m()
    dec = g.ot.astype("int64").to_numpy() // 10**9
    sgn = np.where(g.side == "BUY", 1, -1)
    out = {}
    for tf in cz_tfs:
        c, _ = tf_feats(b, tf, dec)
        chz = -sgn * c                          # + = işlem yönüne KARŞI kanal uzaklığı
        g[f"chz{tf}"] = chz
        bins = pd.cut(chz, [-9, -1, 0, 1, 2, 9], labels=["≤−1 (kovalama)", "−1..0", "0..1", "1..2", "≥2 (fade)"])
        out[f"bot chz_dir {tf}m kovası"] = g.groupby(bins, observed=True).pts.agg(["size", "mean"]).round(1).to_dict("index")
    return out


if __name__ == "__main__":
    res, _ = main()
    res.update(bot())
    (OUT / "round2b.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for k, v in res.items():
        print(f"\n## {k}")
        if isinstance(v, dict) and all(isinstance(x, dict) for x in v.values()):
            for kk, vv in v.items():
                print(f"   {kk}: {vv}")
        else:
            print("  ", v)
