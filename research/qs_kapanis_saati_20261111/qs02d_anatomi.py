"""QS-02 anatomi (betimsel, karar dışı): coşku sonrası aşağı boşluk (E ∧ G−) günlerinin gün içi yolu, boşluk kapanma oranı,
gün dibinin saati — tüm aşağı boşluk günleriyle (G−) kıyas. Broker NAS100 M30 2018-26 + QQQ günlük 1999-2018 (kapanma)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt  # noqa: E402
from qs02 import day_table, features  # noqa: E402

CHK = {"10:00": 600, "11:00": 660, "12:00": 720, "13:00": 780, "14:00": 840, "15:00": 900, "16:00": 960}


def path_table(mk: Mkt, t: pd.DataFrame) -> pd.DataFrame:
    pos = pd.Series(np.arange(len(mk.m)), index=mk.et)
    rows = []
    for d, r in t.iterrows():
        row = {"d": d}
        for lab, m in CHK.items():
            i = pos.get(d + pd.Timedelta(minutes=m))
            row[lab] = (mk.o[i] / r.O - 1) * 1e4 if i is not None else np.nan
        bars = [pos.get(d + pd.Timedelta(minutes=m)) for m in range(570, 960, 30)]
        bars = [b for b in bars if b is not None]
        lows = mk.l[bars]; highs = mk.h[bars]
        row["dip_saati"] = 570 + 30 * int(np.argmin(lows))
        row["kapandi"] = bool(highs.max() >= r.C1)  # aşağı boşluk: gün içinde dünkü kapanışa geri döndü mü
        row["kapanis_dunun_ustu"] = bool(r.C >= r.C1)
        rows.append(row)
    return pd.DataFrame(rows).set_index("d")


def summarize(p: pd.DataFrame) -> dict:
    return {"n": int(len(p)), "yol_medyan_bp": {k: round(float(p[k].median()), 1) for k in CHK},
            "yol_ort_bp": {k: round(float(p[k].mean()), 1) for k in CHK},
            "bosluk_kapanma": round(float(p.kapandi.mean()), 3), "gun_dunun_ustunde_kapanis": round(float(p.kapanis_dunun_ustu.mean()), 3),
            "dip_ilk_saatte": round(float((p.dip_saati < 630).mean()), 3), "dip_son_saatte": round(float((p.dip_saati >= 900).mean()), 3)}


def main() -> None:
    mk = Mkt("NAS100"); t = features(day_table(mk))
    p = path_table(mk, t)
    out = {"NAS100_E_G-": summarize(p[t.E & t.Gm]), "NAS100_tum_G-": summarize(p[t.Gm & ~t.E]),
           "NAS100_E_G-_buyuk(<=-0.6)": summarize(p[t.E & t.GmB])}
    q = pd.read_parquet(H.parent / "ndx_kapi_20261110/data/QQQ.parquet"); q = q[q.index < "2018-05-01"]
    c1 = q.Close.shift(1); r1 = (q.Close / c1 - 1).shift(1); k1 = ((q.Close - q.Low) / (q.High - q.Low)).shift(1)
    gap = q.Open / c1 - 1
    E = (r1 >= 0.015) & (k1 >= 0.75); Gm = gap <= -0.003
    fill = q.High >= c1
    out["QQQ_1999_2018"] = {"E_G-_kapanma": round(float(fill[E & Gm].mean()), 3), "n": int((E & Gm).sum()),
                            "tum_G-_kapanma": round(float(fill[Gm & ~E].mean()), 3), "n_tum": int((Gm & ~E).sum())}
    (H / "results/qs02d_anatomi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
