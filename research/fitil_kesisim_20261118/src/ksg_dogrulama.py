"""ksg_dogrulama.py — PROTOCOL EK-1 (a)–(d): fitilli KSG'nin bağımsız besleme, bağımsız piyasa, oynaklık plasebosu ve kart sınaması."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/ndx_10y_1m_20261116/src"))
sys.path.insert(0, str(ROOT / "research/fitil_zamanlama_20261118/src"))
sys.path.insert(0, str(ROOT / "research/ndx_tf_yapilandirma_20261117/src"))
import lib  # noqa: E402
import rules  # noqa: E402
import fz  # noqa: E402
import kesisim as KS  # noqa: E402

NY = fz.NY
RES = Path(__file__).resolve().parents[1] / "results"
W = 6 * 3600
CARD = ROOT / "backend/data/evolution/go_live_cards/ndx_ksg_fitil.json"


def tag(t_in: np.ndarray, times: np.ndarray, w: int = W) -> np.ndarray:
    return np.searchsorted(times, t_in, "right") > np.searchsorted(times, t_in - w, "left")


def comp(df: pd.DataFrame, col: str, mask: np.ndarray) -> dict:
    a, b = df[mask], df[~mask]
    return {"n_fitil": int(mask.sum()), "fitil": round(float(a[col].mean()), 3) if len(a) else None,
            "fitilsiz": round(float(b[col].mean()), 3) if len(b) else None,
            "P_fark": round(KS.diff_p(a[col].values, a.d.astype(str).values, b[col].values, b.d.astype(str).values), 4) if len(a) >= 3 else None}


# ─────────── MT5 M30 KSG ───────────

def mt5_m30(sym: str, since: str | None = None) -> pd.DataFrame:
    import kaynak
    x = pd.read_csv(ROOT / f"research/c1_turev_20261105/data/mt5/{sym}_M30.csv.gz")
    t = kaynak.server_to_utc(x["t"].to_numpy())
    d = pd.DataFrame({"t": t, "o": x.o, "h": x.h, "l": x.l, "c": x.c, "sp": x.sp * 0.1}).dropna(subset=["t"])
    d["t"] = d.t.astype(np.int64)
    d = d.drop_duplicates("t").sort_values("t").reset_index(drop=True)
    if since:
        d = d[d.t >= int(pd.Timestamp(since, tz=NY).timestamp())].reset_index(drop=True)
    ok = np.r_[True, np.diff(d.t.values) >= 1800]
    return d[ok].reset_index(drop=True)


def ksg_m30(d: pd.DataFrame) -> pd.DataFrame:
    ny = pd.to_datetime(d.t, unit="s", utc=True).dt.tz_convert(NY)
    d = d.assign(day=ny.dt.date, hm=ny.dt.hour * 60 + ny.dt.minute)
    by = {k: g.set_index("hm") for k, g in d.groupby("day")}
    days = sorted(by)
    rows = []
    for i, dd in enumerate(days[:-1]):
        g = by[dd]
        if dd.weekday() >= 5 or lib.nyse.is_holiday(dd) or lib.nyse.is_early_close(dd) or not {900, 960}.issubset(g.index):
            continue
        o15, o16 = float(g.loc[900, "o"]), float(g.loc[960, "o"])
        if o16 / o15 - 1 >= 0:
            continue
        nd = days[i + 1]
        if 570 not in by[nd].index:
            continue
        px_in = o16 + float(g.loc[960, "sp"])
        px_out = float(by[nd].loc[570, "o"])
        nights = (nd - dd).days
        net = (px_out / px_in - 1) * 1e4 - lib.FIN_BP_PER_DAY * nights
        rows.append({"d": dd, "t_in": int(g.loc[960, "t"]), "net_bp": net})
    return pd.DataFrame(rows)


def wicks_m30(d: pd.DataFrame) -> np.ndarray:
    p = fz.veri.PathBars(d.t.values, d.o.values, d.h.values, d.l.values, d.c.values, d.sp.values, 1800, "m30")
    b = fz.veri.add_wicks(fz.agg(p, 3600))
    ok = (b.lw_pct >= 0.50) & (b.uw_pct <= 0.5 * b.lw_pct)
    return np.sort(b.tend.values[ok.values]).astype(np.int64)


def main() -> None:
    out = {}
    # ── Dukascopy temel + (c) oynaklık plasebosu + (d) kart ──
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    k = lib.to_frame(rules.ksg(m1, D)).dropna(subset=["net_bp"]).reset_index(drop=True)
    p = fz.veri.PathBars(m1.t, m1.o, m1.h, m1.l, m1.c, m1.spr, 60, "NDX")
    b = fz.veri.add_wicks(fz.agg(p, 3600))
    b["rng"] = (b.high - b.low) / b.close * 100
    wk = (b.lw_pct >= 0.50) & (b.uw_pct <= 0.5 * b.lw_pct)
    rng_thr = float(b.rng[wk].median())
    vol = (b.rng >= rng_thr) & (b.lw_pct < 0.20)
    tw, tv = np.sort(b.tend.values[wk.values]), np.sort(b.tend.values[vol.values])
    mw, mv = tag(k.t_in.values, tw), tag(k.t_in.values, tv)
    out["duka"] = comp(k, "net_bp", mw)
    a, v = k[mw], k[mv & ~mw]
    out["c_oynaklik_plasebo"] = {"rng_esik_%": round(rng_thr, 3), "n_oynak": int(len(v)), "oynak_ort": round(float(v.net_bp.mean()), 2),
                                  "fitil_ort": round(float(a.net_bp.mean()), 2),
                                  "P": round(KS.diff_p(a.net_bp.values, a.d.astype(str).values, v.net_bp.values, v.d.astype(str).values), 4)}
    out["c_gecti"] = bool(out["c_oynaklik_plasebo"]["fitil_ort"] > out["c_oynaklik_plasebo"]["oynak_ort"] and out["c_oynaklik_plasebo"]["P"] >= 0.90)
    print("Dukascopy", out["duka"], "| oynaklık plasebosu", out["c_oynaklik_plasebo"], flush=True)
    # kart (d)
    ka = k[mw].sort_values("t_in").reset_index(drop=True)
    k1 = lib.to_frame(rules_ksg_delayed(m1, D)).dropna(subset=["net_bp"])
    k1 = k1[tag(k1.t_in.values - 60, tw)]
    h = len(ka) // 2
    s15 = float(ka.net_bp_s15.mean())
    P = lib.block_boot_p(ka.net_bp.values, pd.to_datetime(ka.d).dt.to_period("M").astype(str).values)
    checks = {"1_hacim": {"deger": len(ka), "gecti": len(ka) >= 150},
              "2_beklenti": {"deger": f"{ka.net_bp.mean():+.1f} bp P {P:.3f}", "gecti": bool(ka.net_bp.mean() > 0 and P >= 0.9)},
              "3_kararlilik": {"deger": f"{ka.net_bp.iloc[:h].mean():+.1f} / {ka.net_bp.iloc[h:].mean():+.1f}",
                               "gecti": bool(ka.net_bp.iloc[:h].mean() >= 0 and ka.net_bp.iloc[h:].mean() >= 0)},
              "4_surtunme": {"deger": f"spread×1,5 {s15:+.1f} bp", "gecti": s15 > 0},
              "5_icra": {"deger": f"16:00 {ka.net_bp.mean():+.1f} vs 16:01 {k1.net_bp.mean():+.1f} bp",
                         "gecti": bool(ka.net_bp.mean() - k1.net_bp.mean() < 0.5 * abs(k1.net_bp.mean()) and k1.net_bp.mean() > 0)},
              "6_sira_bagimli": {"deger": "gecede tek işlem (yapısal)", "gecti": bool(ka.net_bp.mean() > 0)}}
    out["d_kart"] = {k_: v_ for k_, v_ in checks.items()}
    out["d_gecti"] = all(c["gecti"] for c in checks.values())
    out["yillar"] = {int(y): round(float(g.net_bp.mean()), 1) for y, g in ka.groupby(pd.to_datetime(ka.d).dt.year)}
    print("kart", {k_: v_["gecti"] for k_, v_ in checks.items()}, out["yillar"], flush=True)
    # ── (a) MT5 NAS100 ──
    for sym, since in (("NAS100", None), ("US500", "2021-01-01"), ("US30", None), ("US2000", None)):
        d = mt5_m30(sym, since)
        kk = ksg_m30(d)
        mm = tag(kk.t_in.values, wicks_m30(d))
        out[sym] = comp(kk, "net_bp", mm) | {"aralik": [str(kk.d.min()), str(kk.d.max())], "n_ksg": int(len(kk))}
        print(sym, out[sym], flush=True)
    a_ = out["NAS100"]
    out["a_gecti"] = bool(a_["fitil"] is not None and a_["fitil"] > 0 and a_["fitil"] > a_["fitilsiz"] and a_["P_fark"] >= 0.90)
    others = [out[s] for s in ("US500", "US30", "US2000")]
    pos = sum(1 for o in others if o["fitil"] is not None and o["fitil"] > o["fitilsiz"])
    # havuz farkı: her sembolde (fitil − fitilsiz) ağırlıklı
    pool_a = pd.concat([ksg_tagged(s, since, True) for s, since in (("US500", "2021-01-01"), ("US30", None), ("US2000", None))])
    pool_b = pd.concat([ksg_tagged(s, since, False) for s, since in (("US500", "2021-01-01"), ("US30", None), ("US2000", None))])
    pP = KS.diff_p(pool_a.net_bp.values, pool_a.d.astype(str).values, pool_b.net_bp.values, pool_b.d.astype(str).values)
    out["b_havuz"] = {"artı_fark": f"{pos}/3", "fitil": round(float(pool_a.net_bp.mean()), 2), "fitilsiz": round(float(pool_b.net_bp.mean()), 2),
                      "P": round(pP, 4)}
    out["b_gecti"] = bool(pos >= 2 and pP >= 0.90)
    out["hukum"] = ("B" if all(out[k_] for k_ in ("a_gecti", "b_gecti", "c_gecti", "d_gecti")) else
                    "C+" if out["a_gecti"] and out["c_gecti"] else "C")
    print({k_: out[k_] for k_ in ("a_gecti", "b_gecti", "c_gecti", "d_gecti", "hukum")}, out["b_havuz"], flush=True)
    (RES / "ksg_dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def ksg_tagged(sym: str, since: str | None, wick: bool) -> pd.DataFrame:
    d = mt5_m30(sym, since)
    kk = ksg_m30(d)
    m = tag(kk.t_in.values, wicks_m30(d))
    return kk[m] if wick else kk[~m]


def rules_ksg_delayed(m1, D) -> list:
    """Kart icra ölçütü: aynı KSG, giriş 16:01 açılışı."""
    days = D.d.tolist()
    tr = []
    for j, row in enumerate(D.itertuples()):
        if not row.full or j + 1 >= len(days):
            continue
        o0, o16 = row.O15, (row.O16 if np.isfinite(row.O16) else row.c1600)
        if not (np.isfinite(o0) and np.isfinite(o16)) or o16 / o0 - 1 >= 0:
            continue
        x = lib.time_trade(m1, "KSG1", row.d, lib.utc(row.d, 961), lib.utc(days[j + 1], 570), +1)
        if x:
            tr.append(x)
    return tr


if __name__ == "__main__":
    main()
