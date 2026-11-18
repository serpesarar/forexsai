"""ve.py — VIX vade eğrisi / sıçrama → NDX 09:30 AL, çıkış aynı gün / +1 / +4 gün 16:00 (PROTOCOL). python ve.py kesif | dogrula"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/cosku_capraz_20261118/src"))
import cc  # noqa: E402
K, G, GR = cc.K, cc.G, cc.GR

RES = ROOT / "research/vix_egri_20261118/results"
TZ = "America/New_York"
HOLDS = {"ayni_16:00": 0, "+1_16:00": 1, "+4_16:00": 4}
N_MIN, N_PL, MAX_FROZEN = 25, 20, 4


def vix_signals() -> pd.DataFrame:
    m = pd.read_parquet(ROOT / "research/nom_20261113/data/macro/macro_daily.parquet")[["date", "VIX_close", "VIX9D_close", "VIX3M_close"]].dropna()
    m["date"] = pd.to_datetime(m.date).dt.date
    m = m.sort_values("date").reset_index(drop=True)
    m["r9"] = m.VIX9D_close / m.VIX_close
    m["r3"] = m.VIX_close / m.VIX3M_close
    m["chg"] = m.VIX_close.pct_change()
    return m


def lagged(days: list, m: pd.DataFrame) -> pd.DataFrame:
    """Her işlem günü d için d'den ÖNCEKİ son VIX satırı."""
    dv = m.date.values
    idx = np.searchsorted(dv, np.array(days, dtype=object), side="left") - 1
    out = m.iloc[np.clip(idx, 0, None)].reset_index(drop=True)
    out.loc[idx < 0, ["r9", "r3", "chg"]] = np.nan
    out["d"] = days
    return out


SIGS = {("S1", 1.00): lambda v: v.r9 >= 1.00, ("S1", 1.10): lambda v: v.r9 >= 1.10,
        ("S2", 1.00): lambda v: v.r3 >= 1.00, ("S2", 1.05): lambda v: v.r3 >= 1.05,
        ("S3", 0.15): lambda v: v.chg >= 0.15, ("S3", 0.25): lambda v: v.chg >= 0.25}


def trades(d: pd.DataFrame, step: int) -> dict:
    dp = G.day_prices(d, TZ, [570, 960], step)
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x)]
    vs = lagged(days, vix_signals()).set_index("d")
    out = {}
    for hn, h in HOLDS.items():
        rows = []
        for i, dd in enumerate(days):
            if i + h >= len(days):
                break
            r, x = dp.loc[dd], dp.loc[days[i + h]]
            oe, ox = r.get("o570"), x.get("o960")
            if not (np.isfinite(oe) and np.isfinite(ox)):
                continue
            pin = oe + r.s570
            net = (ox / pin - 1) * 1e4 - G.lib.FIN_BP_PER_DAY * (days[i + h] - dd).days
            rows.append({"d": dd, "t_in": int(r.t570), "net_bp": net, "net_bp_s15": net - 0.5 * (r.s570 + x.s960) / pin * 1e4})
        df = pd.DataFrame(rows)
        df["era"] = np.where(df.d <= G.ESKI_END, "ESKI", "YENI")
        v = vs.reindex(df.d.values)
        out[hn] = (df, {k: np.nan_to_num(f(v).values.astype(float)).astype(bool) for k, f in SIGS.items()})
    return out


def grid(T, era, n_boot, shift=0):
    rows = []
    for hn, (df, ms) in T.items():
        sel = (df.era == era).values if era else np.ones(len(df), bool)
        for k, m in ms.items():
            mm = np.roll(m, shift) if shift else m
            rows.append({"S": k[0], "esik": k[1], "cikis": hn, **cc.cell(df[sel].reset_index(drop=True), mm[sel], n_boot)})
    return pd.DataFrame(rows)


def kesif():
    RES.mkdir(exist_ok=True)
    T = trades(G.ndx_bars(), 60)
    gr = grid(T, "ESKI", 4000)
    gr.to_csv(RES / "kesif_izgara.csv", index=False)
    real = cc.passing(gr)
    rng = np.random.default_rng(31)
    pc = [int(len(cc.passing(grid(T, "ESKI", 300, int(rng.integers(1, 11) * rng.choice([-1, 1])))))) for _ in range(N_PL)]
    frozen = real.sort_values("t", ascending=False).head(MAX_FROZEN).to_dict("records")
    oz = {"hucre": len(gr), "aday": len(real), "plasebo": sorted(pc), "plasebo_p95": float(np.percentile(pc, 95)),
          "sans_ustu": bool(len(real) > np.percentile(pc, 95)), "donmus": frozen}
    (RES / "kesif_ozet.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: oz[k] for k in ("hucre", "aday", "plasebo", "plasebo_p95", "sans_ustu")}, ensure_ascii=False))
    print(gr.sort_values("t", ascending=False)[["S", "esik", "cikis", "n", "tetik", "taban", "P", "t"]].round(3).to_string(index=False))


def dogrula():
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    if not frozen:
        print("dondurulan yok")
        return
    d = G.ndx_bars()
    T = trades(d, 60)
    FD = {nm: trades(b, st) for nm, (b, st) in GR.feeds().items()}
    k1 = cc.ndx_k1_days(d, 60)
    dp = G.day_prices(d, TZ, [570], 60)
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x)]
    prev = {days[i]: days[i - 1] for i in range(1, len(days))}
    out = []
    for c in frozen:
        df, ms = T[c["cikis"]]
        m = ms[(c["S"], c["esik"])]
        y = cc.cell(df[df.era == "YENI"].reset_index(drop=True), m[(df.era == "YENI").values])
        tot = cc.cell(df, m)
        fr = {nm: cc.cell(F[c["cikis"]][0], F[c["cikis"]][1][(c["S"], c["esik"])]) for nm, F in FD.items()}
        ov = np.array([prev.get(x) in k1 for x in df.d])
        inc = cc.cell(df[~ov].reset_index(drop=True), m[~ov])
        ok = {"1_yeni": bool(y.get("tetik", -1) > 0 and y.get("P", 0) >= 0.975),
              "2_beslemeler": all(f.get("tetik", -1) > 0 and f.get("tetik", -1) > f.get("taban", 9e9) for f in fr.values()),
              "3_surtunme": bool(y.get("s15", -1) > 0), "4_hacim": bool(tot.get("n", 0) >= 150)}
        hk = "B" if all(ok.values()) else ("C+" if ok["1_yeni"] and ok["2_beslemeler"] else "X")
        out.append({"hucre": c, "YENI": y, "TUM": tot, "beslemeler": fr, "K1_ortusme": round(float(ov[m].mean()), 3) if m.any() else None,
                    "K1_disi": inc, "olcut": ok, "hukum": hk})
        print(f"{c['S']} {c['esik']} {c['cikis']} | ESKİ {c['tetik']:+.1f} vs {c['taban']:+.1f} | YENİ {y.get('tetik', float('nan')):+.1f} vs "
              f"{y.get('taban', float('nan')):+.1f} (n {y.get('n')}, P {y.get('P', 0):.3f}) | " + " ".join(
                  f"{nm} {f.get('tetik', float('nan')):+.1f}/{f.get('taban', float('nan')):+.1f}" for nm, f in fr.items())
              + f" | K1 örtüşme {out[-1]['K1_ortusme']}, K1 dışı {inc.get('tetik', float('nan')):+.1f} vs {inc.get('taban', float('nan')):+.1f} | n {tot.get('n')} | {hk}", flush=True)
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula}[sys.argv[1]]()
