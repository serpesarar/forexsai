"""moc.py — 15:50→16:00 MOC penceresi düşüşü → gece/ertesi gün (PROTOCOL). python moc.py kesif | dogrula"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/fitil_gece_20261118/src", "research/korku_gece_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import gece as G  # noqa: E402
import gece_run as GR  # noqa: E402
import korku as K  # noqa: E402

RES = ROOT / "research/moc_pencere_20261118/results"
TZ = "America/New_York"
ES = (0.10, 0.20, 0.30)
EXITS = {"09:30": 570, "16:00": 960}
N_MIN, MAX_FROZEN = 25, 3
P_YENI = 1 - 0.10 / MAX_FROZEN


def mt5_2m() -> tuple[pd.DataFrame, int]:
    d = pd.read_parquet(ROOT / "research/ndx_tf_yapilandirma_20261117/out/MT5/NDX_MT5_2m.parquet")
    sp = d.spr.values.astype(float)
    sp[~(sp > 0)] = 1.3
    return pd.DataFrame({"t": d.t.values.astype(np.int64), "o": d.open.values, "h": d.high.values, "l": d.low.values,
                         "c": d.close.values, "sp": sp}), 120


def build(b: pd.DataFrame, step: int) -> dict:
    dp = G.day_prices(b, TZ, [570, 900, 950, 960], step)
    f = K.features(b, 960, step)
    out = {}
    for en, ex in EXITS.items():
        nt = G.nights(dp, 960, ex, 900, G.nyse_ok)
        p = dp.reindex(nt.d.values)
        nt["m10"] = (p.o960.values / p.o950.values - 1) * 100
        nt["r1550"] = (p.o950.values / p.o900.values - 1) * 100
        tw = f.twap.reindex(nt.d.values).values
        nt["K1"] = np.nan_to_num(((p.o960.values / tw - 1) <= -0.005) & (nt.ksg_ret.values < 0)).astype(bool)
        nt["K3"] = np.nan_to_num(nt.ksg_ret.values <= -0.003).astype(bool)
        out[en] = nt[np.isfinite(nt.m10)].reset_index(drop=True)
    return out


def cmp(nt: pd.DataFrame, a: np.ndarray, b: np.ndarray, n_boot: int = 4000) -> dict:
    x, y = nt[a], nt[b]
    if len(x) < 3 or len(y) < 3:
        return {"n": int(len(x))}
    diff = x.net_bp.mean() - y.net_bp.mean()
    se = np.sqrt(x.net_bp.var(ddof=1) / len(x) + y.net_bp.var(ddof=1) / len(y))
    return {"n": int(len(x)), "tetik": round(float(x.net_bp.mean()), 1), "taban": round(float(y.net_bp.mean()), 1), "fark": round(float(diff), 1),
            "t": round(float(diff / se), 2), "s15": round(float(x.net_bp_s15.mean()), 1), "isabet": round(float((x.net_bp > 0).mean()), 3),
            "P": round(G.KS.diff_p(x.net_bp.values, x.d.astype(str).values, y.net_bp.values, y.d.astype(str).values, n=n_boot), 4)}


def cells(B: dict, sel_fn) -> list[dict]:
    rows = []
    for e in ES:
        for en in EXITS:
            nt = B[en]
            s = sel_fn(nt)
            m = (nt.m10 <= -e).values
            rows.append({"aile": "A", "e": e, "cikis": en, **cmp(nt, m & s, ~m & s)})
        nt = B["16:00"]
        s = sel_fn(nt) & nt.K1.values
        m = (nt.m10 <= -e).values
        rows.append({"aile": "B", "e": e, "cikis": "16:00", **cmp(nt, m & s, ~m & s)})
    return rows


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    B = build(G.ndx_bars(), 60)
    g = pd.DataFrame(cells(B, lambda nt: (nt.era == "ESKI").values))
    g.to_csv(RES / "kesif.csv", index=False)
    print(g.to_string(index=False))
    ok = g[(g.n >= N_MIN) & (g.tetik > 0) & (g.fark > 0) & (g.P >= 0.90)]
    fr = ok.sort_values("t", ascending=False).head(MAX_FROZEN)[["aile", "e", "cikis"]].to_dict("records")
    (RES / "kesif_ozet.json").write_text(json.dumps({"hucre": len(g), "aday": len(ok), "donmus": fr}, indent=1))
    print("dondurulan:", fr)
    # bilgi: son saatin ayrıştırılması (tüm dönem, 16:00 çıkışı)
    nt = B["16:00"]
    al = np.ones(len(nt), bool)
    info = {"K3_15:50_oncesi_dusus_(<=-0.2)": cmp(nt, nt.K3.values & (nt.r1550 <= -0.2).values, ~nt.K3.values),
            "K3_MOC_dusus_(<=-0.1)": cmp(nt, nt.K3.values & (nt.m10 <= -0.1).values, ~nt.K3.values),
            "muzayede_ters_(r1550<=-0.3_ve_m10>=+0.1)": cmp(nt, ((nt.r1550 <= -0.3) & (nt.m10 >= 0.1)).values, al & ~((nt.r1550 <= -0.3)).values),
            "surekli_(r1550<=-0.3_ve_m10<=-0.1)": cmp(nt, ((nt.r1550 <= -0.3) & (nt.m10 <= -0.1)).values, al & ~((nt.r1550 <= -0.3)).values)}
    for k, v in info.items():
        print(k, v)
    (RES / "bilgi_ayristirma.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))


def dogrula() -> None:
    fr = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    B = build(G.ndx_bars(), 60)
    nq, _ = None, None
    import ksg_ek2 as E
    F = {"MT5_2m": build(*mt5_2m()), "NQ_5m": build(*E.bars("NQ"))}
    out = []
    for f in fr:
        sel = {c["aile"] + str(c["e"]) + c["cikis"]: c for c in []}
        key = (f["aile"], f["e"], f["cikis"])

        def pick(rows):
            return next(r for r in rows if (r["aile"], r["e"], r["cikis"]) == key)
        y = pick(cells(B, lambda nt: (nt.era == "YENI").values))
        tot = pick(cells(B, lambda nt: np.ones(len(nt), bool)))
        fe = {nm: pick(cells(Bf, lambda nt: np.ones(len(nt), bool))) for nm, Bf in F.items()}
        ind = pick(cells(B, lambda nt: ~nt.K1.values)) if f["aile"] == "A" else None
        a = f["aile"] == "A"
        ok = {"1_yeni": bool(y.get("fark", -1) > 0 and y.get("P", 0) >= P_YENI and (not a or y.get("tetik", -1) > 0)),
              "2_beslemeler": all(v.get("fark", -1) > 0 and (not a or v.get("tetik", -1) > 0) for v in fe.values()),
              "3_K1_bagimsiz": bool(ind.get("fark", -1) > 0 and ind.get("P", 0) >= 0.90) if a else True,
              "4_surtunme": bool(y.get("s15", -1) > 0)}
        hk = "B" if all(ok.values()) else ("C+" if ok["1_yeni"] and ok["2_beslemeler"] else "X")
        rec = {"hucre": key, "YENI": y, "TUM": tot, "beslemeler": fe, "K1_disi": ind, "olcut": ok, "hukum": hk}
        out.append(rec)
        print(f"\n{key}: {hk} {ok}\n  YENİ {y}\n  TÜM {tot}\n  K1 dışı {ind}")
        for nm, v in fe.items():
            print(f"  {nm} {v}")
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula}[sys.argv[1]]()
