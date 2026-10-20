"""ME-11 SONRADAN tanılama (ön-kayıt dışı, karar değiştirmez): eşli tabana sorgu saati (NY) eklenince fark kalıyor mu?

Gerekçe: 5m/15m/30m'de 23 barlık adım gün içinde kayar; ileri oynaklık güçlü gün-içi mevsimsellik taşır ve ön-kayıtlı
taban (geriye getiri × geriye oynaklık) saati eşlemez. Yöntem: y − (geliştirme dönemindeki yapı-olmayan sorguların o NY
saatindeki ortalaması), sonra aynı eşli taban + ay-blok bootstrap.
"""
from __future__ import annotations

import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from risk_testi import (DEV_END, HO_START, HS, TARGETS, decile_bins, load_all, matched_base, mboot,  # noqa: E402
                        episode_stats, prepare, template_vectors)


def main() -> None:
    data = load_all()
    tvs = template_vectors(data[("NDX", "1h")])
    rows = []
    for (sym, tf), d in data.items():
        if tf in ("4h",):
            continue
        pr = prepare(d, tvs)
        t_q, base_ok, ex, D = pr["t_q"], pr["base_ok"], pr["ex"], pr["D"]
        hr = t_q.dt.tz_convert("America/New_York").dt.hour.to_numpy()
        devq = base_ok & ~ex & (t_q <= DEV_END).to_numpy()
        thr2, thr5 = np.percentile(D[devq], 2), np.percentile(D[devq], 5)
        det = {"D1": (D <= thr2, D > thr5), "D2": (pr["fire"], ~pr["fire"])}
        rb = decile_bins(pr["X"]["trail_ret"], pr["X"]["trail_ret"][devq])
        vb = decile_bins(pr["X"]["trail_rv"], pr["X"]["trail_rv"][devq])
        keys = [rb * 10 + vb, rb]
        ho = (t_q >= HO_START).to_numpy()
        for H in HS:
            y = pr["Y"][H]
            dev = y["valid"] & ~ex & (y["end_ts"] <= DEV_END).to_numpy()
            for dn, (sim, non) in det.items():
                for tg in ("lrv", "dd"):
                    sgn = TARGETS[tg]
                    hm = pd.Series(y[tg][dev & non]).groupby(hr[dev & non]).mean()
                    yadj = y[tg] - hm.reindex(hr).to_numpy()
                    for per, pm in (("gel", dev), ("dog", y["valid"] & ~ex & ho)):
                        s, nn = pm & sim & np.isfinite(yadj), pm & non & np.isfinite(yadj)
                        k = np.flatnonzero(s)
                        if len(k) == 0:
                            continue
                        raw = y[tg] - matched_base(y[tg], pm & non, keys, s)
                        adj = yadj - matched_base(yadj, nn, keys, s)
                        seed = zlib.crc32(f"saat|{sym}|{tf}|{H}|{dn}|{per}|{tg}".encode())
                        n_ep, med, _ = episode_stats(k, adj[k])
                        rows.append({"sembol": sym, "tf": tf, "k": dn, "H": H, "hedef": tg, "donem": per, "sorgu": len(k),
                                     "olay": n_ep, "fark_onkayit": float(np.mean(raw[k])), "fark_saat_eşli": float(np.mean(adj[k])),
                                     "P_risk_saat": mboot(sgn * adj[k], pr["month"][k], seed), "olay_medyan_saat": med})
        if tf in ("5m", "15m", "30m"):
            s = devq & det["D1"][0]
            share = pd.Series(hr[s]).value_counts(normalize=True).sort_index().round(2).to_dict()
            print(f"{sym} {tf} D1 yapı sorgularının NY saat dağılımı:", share, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(Path(__file__).resolve().parent / "results/tanilama_saat.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    print(out[out.hedef == "lrv"].round(3).to_string(index=False))
    print(out[out.hedef == "dd"].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
