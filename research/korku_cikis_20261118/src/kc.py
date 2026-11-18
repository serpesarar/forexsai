"""kc.py — korku gecesi çıkış türevleri + ikinci korku günü eklemesi (PROTOCOL). python kc.py kesif | dogrula | ekle"""
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

RES = ROOT / "research/korku_cikis_20261118/results"
GEC = ROOT / "research/korku_birlesik_20261118/results"
TZ = "America/New_York"
EXITS = ("X1", "X2", "X3", "X5", "XU", "XP", "XT")
TRIG = {"K1": lambda f: f.T_k1.values, "U2": lambda f: (f.S >= 2).values}
MAXH = 5
FIN = G.lib.FIN_BP_PER_DAY


def daily(d: pd.DataFrame, step: int, feed: str) -> pd.DataFrame:
    """İşlem günü × (16:00 bid, spread, TWAP, tetik bayrakları)."""
    dp = G.day_prices(d, TZ, [960], step)
    f = K.features(d, 960, step)
    g = pd.read_parquet(GEC / f"geceler_{feed}.parquet").set_index("d")
    days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x) and np.isfinite(dp.loc[x, "o960"])]
    out = pd.DataFrame({"p": dp.loc[days, "o960"].values, "s": dp.loc[days, "s960"].values}, index=days)
    out["twap"] = f.twap.reindex(days).values
    for k, fn in TRIG.items():
        out[k] = pd.Series(fn(g), index=g.index).reindex(days).fillna(False).astype(bool).values
    out["era"] = np.where(np.array(days) <= G.ESKI_END, "ESKI", "YENI")
    return out


def exit_ix(D: pd.DataFrame, i: int, ex: str) -> int | None:
    p, n = D.p.values, len(D)
    if i + 1 >= n:
        return None
    last = min(i + MAXH, n - 1)
    if ex in ("X1", "X2", "X3", "X5"):
        k = i + int(ex[1])
        return k if k < n else None
    pin = p[i] + D.s.values[i]
    for k in range(i + 1, last + 1):
        if ex == "XU" and p[k] > pin:
            return k
        if ex == "XP" and p[k] > p[k - 1]:
            return k
        if ex == "XT" and np.isfinite(D.twap.values[i]) and p[k] >= D.twap.values[i]:
            return k
    return last if last == i + MAXH else None


def trade(D: pd.DataFrame, i: int, k: int) -> tuple[float, float, list]:
    """net bp, spread×1,5 net, günlük piyasa değeri bp listesi [(gün indeksi, bp)]."""
    idx, p, s = D.index, D.p.values, D.s.values
    pin = p[i] + s[i]
    nts = (idx[k] - idx[i]).days
    net = (p[k] / pin - 1) * 1e4 - FIN * nts
    extra = 0.5 * (s[i] + s[k]) / pin * 1e4
    marks, prev = [], pin
    for j in range(i + 1, k + 1):
        marks.append((j, (p[j] / prev - 1) * 1e4 - FIN * (idx[j] - idx[j - 1]).days))
        prev = p[j]
    return net, net - extra, marks


def trades(D: pd.DataFrame, mask: np.ndarray, ex: str, single: bool) -> pd.DataFrame:
    rows, busy = [], -1
    for i in np.flatnonzero(mask):
        if single and i < busy:
            continue
        k = exit_ix(D, i, ex)
        if k is None:
            continue
        net, n15, mk = trade(D, i, k)
        rows.append({"i": i, "k": k, "d": D.index[i], "era": D.era.values[i], "net": net, "n15": n15, "gun": k - i, "_mk": mk})
        busy = k
    return pd.DataFrame(rows)


def portfolio(D: pd.DataFrame, tr: pd.DataFrame, era: str | None) -> dict:
    pnl = np.zeros(len(D))
    for mk in tr._mk:
        for j, v in mk:
            pnl[j] += v
    sel = (D.era.values == era) if era else np.ones(len(D), bool)
    s = pnl[sel]
    cs = np.cumsum(s)
    return {"sharpe": round(float(s.mean() / s.std() * np.sqrt(252)), 3) if s.std() > 0 else np.nan,
            "yillik_bp": round(float(s.mean() * 252), 1), "maxDD": round(float((cs - np.maximum.accumulate(cs)).min()), 1),
            "piyasada_gun_orani": round(float((s != 0).mean()), 3)}


def cell(D: pd.DataFrame, trig: str, ex: str, era: str | None, n_boot: int = 3000) -> dict:
    m = D[trig].values
    a = trades(D, m, ex, True)
    b = trades(D, ~m, ex, False)
    if era:
        a, b = a[a.era == era], b[b.era == era]
    if len(a) < 5:
        return {"n": int(len(a))}
    p = portfolio(D, a, era)
    return {"n": int(len(a)), "ort": round(float(a.net.mean()), 1), "taban": round(float(b.net.mean()), 1),
            "fark": round(float(a.net.mean() - b.net.mean()), 1), "ort_s15": round(float(a.n15.mean()), 1),
            "ort_gun": round(float(a.gun.mean()), 2), "isabet": round(float((a.net > 0).mean()), 3),
            "en_kotu": round(float(a.net.min()), 1), "sd": round(float(a.net.std()), 1),
            "P": round(float(G.KS.diff_p(a.net.values, a.d.astype(str).values, b.net.values, b.d.astype(str).values, n=n_boot)), 4), **p}


def feeds() -> dict:
    out = {"DUKA": (G.ndx_bars(), 60)}
    out.update(GR.feeds())
    return out


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    D = daily(G.ndx_bars(), 60, "DUKA")
    D.to_parquet(RES / "gunluk_DUKA.parquet")
    rows = [{"tetik": t, "cikis": e, **cell(D, t, e, "ESKI")} for t in TRIG for e in EXITS]
    g = pd.DataFrame(rows)
    g.to_csv(RES / "kesif.csv", index=False)
    print(g.to_string(index=False))
    frozen = []
    for t in TRIG:
        ref = g[(g.tetik == t) & (g.cikis == "X1")].iloc[0]
        c = g[(g.tetik == t) & (g.cikis != "X1") & (g.fark > ref.fark) & (g.sharpe > ref.sharpe) & (g.P >= 0.90)]
        if len(c):
            frozen.append(c.sort_values("sharpe", ascending=False).iloc[0][["tetik", "cikis"]].to_dict())
    (RES / "kesif_ozet.json").write_text(json.dumps({"hucre": len(g), "donmus": frozen}, indent=1, ensure_ascii=False))
    print("dondurulan:", frozen)


def dogrula() -> None:
    frozen = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    Ds = {nm: daily(b, st, nm) for nm, (b, st) in feeds().items()}
    out = []
    for f in frozen:
        t, e = f["tetik"], f["cikis"]
        D = Ds["DUKA"]
        y, y1 = cell(D, t, e, "YENI"), cell(D, t, "X1", "YENI")
        a, a1 = cell(D, t, e, None), cell(D, t, "X1", None)
        fr = {nm: (cell(Dx, t, e, None), cell(Dx, t, "X1", None)) for nm, Dx in Ds.items() if nm != "DUKA"}
        ok = {"1_yeni": bool(y["sharpe"] > y1["sharpe"] and y["fark"] > y1["fark"] and y["P"] >= 0.975),
              "2_beslemeler": sum(c["sharpe"] > c1["sharpe"] and c["fark"] > c1["fark"] for c, c1 in fr.values()) >= 2,
              "3_surtunme": bool(y["ort_s15"] > 0 and a["ort_s15"] > 0),
              "4_kuyruk": bool(a["en_kotu"] >= 1.5 * a1["en_kotu"] and a["maxDD"] >= 1.5 * a1["maxDD"])}
        hk = "B" if all(ok.values()) else ("C+" if ok["1_yeni"] and ok["2_beslemeler"] else "X")
        rec = {"tetik": t, "cikis": e, "YENI": y, "YENI_X1": y1, "TUM": a, "TUM_X1": a1,
               "beslemeler": {nm: {"cikis": c, "X1": c1} for nm, (c, c1) in fr.items()}, "olcut": ok, "hukum": hk}
        out.append(rec)
        print(f"\n{t} {e}: {hk} {ok}")
        print(f"  YENİ  {e}: {y}\n  YENİ  X1: {y1}\n  TÜM   {e}: {a}\n  TÜM   X1: {a1}")
        for nm, (c, c1) in fr.items():
            print(f"  {nm}: {e} ort {c['ort']} fark {c['fark']} sh {c['sharpe']} | X1 ort {c1['ort']} fark {c1['fark']} sh {c1['sharpe']}")
    # bilgi: tüm hücreler YENİ (seçimsiz tablo)
    D = Ds["DUKA"]
    tab = pd.DataFrame([{"tetik": t, "cikis": e, **cell(D, t, e, "YENI", 500)} for t in TRIG for e in EXITS])
    tab.to_csv(RES / "yeni_tum_hucreler.csv", index=False)
    print("\nYENİ tüm hücreler (bilgi):\n", tab[["tetik", "cikis", "n", "ort", "taban", "fark", "ort_gun", "sharpe", "maxDD", "en_kotu"]].to_string(index=False))
    (RES / "dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def ekle() -> None:
    fz = json.loads((RES / "kesif_ozet.json").read_text())["donmus"]
    ex_of = {f["tetik"]: f["cikis"] for f in fz}
    out = {}
    for nm, (b, st) in feeds().items():
        D = daily(b, st, nm)
        for t in TRIG:
            ex = ex_of.get(t, "X2")
            m = D[t].values
            units, rows = [], []
            for i in range(len(D)):
                units = [u for u in units if u > i]
                if m[i] and len(units) < 2:
                    k = exit_ix(D, i, ex)
                    if k is None:
                        continue
                    net, n15, mk = trade(D, i, k)
                    rows.append({"i": i, "k": k, "d": D.index[i], "era": D.era.values[i], "net": net, "n15": n15, "gun": k - i,
                                 "_mk": mk, "ek": len(units) == 1})
                    units.append(k)
            tr = pd.DataFrame(rows)
            rec = {"cikis": ex}
            for era in ("ESKI", "YENI"):
                x = tr[tr.era == era]
                rec[era] = {"ilk_n": int((~x.ek).sum()), "ilk_ort": round(float(x[~x.ek].net.mean()), 1),
                            "ek_n": int(x.ek.sum()), "ek_ort": round(float(x[x.ek].net.mean()), 1) if x.ek.any() else None,
                            "sharpe_tek": portfolio(D, tr[~tr.ek], era)["sharpe"], "sharpe_ekli": portfolio(D, tr, era)["sharpe"]}
            e_, y_ = rec["ESKI"], rec["YENI"]
            rec["gecer"] = bool(all(r["ek_ort"] is not None and r["ek_ort"] > 0 and r["ek_ort"] >= r["ilk_ort"] and r["sharpe_ekli"] > r["sharpe_tek"]
                                    for r in (e_, y_)))
            out[f"{nm}:{t}"] = rec
            print(nm, t, rec, flush=True)
    (RES / "ekle.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def tasima() -> None:
    import ksg_dogrulama as KD
    res = {}
    for sym, since in (("US30", None), ("US2000", None), ("US500", "2021-01-01")):
        b = KD.mt5_m30(sym, since)
        dp = G.day_prices(b, TZ, [900, 960], 1800)
        f = K.features(b, 960, 1800)
        days = [x for x in dp.index if x.weekday() < 5 and G.nyse_ok(x) and np.isfinite(dp.loc[x, "o960"])]
        D = pd.DataFrame({"p": dp.loc[days, "o960"].values, "s": dp.loc[days, "s960"].values}, index=days)
        D["twap"] = f.twap.reindex(days).values
        o9 = dp.loc[days, "o900"].values
        D["K1"] = np.nan_to_num(((D.p.values / D.twap.values - 1) <= -0.005) & (D.p.values < o9)).astype(bool)
        D["era"] = np.where(np.array(days) <= G.ESKI_END, "ESKI", "YENI")
        res[sym] = {e: {k: cell(D, "K1", e, era, 1000) for k, era in (("TUM", None), ("ESKI", "ESKI"), ("YENI", "YENI"))} for e in ("X1", "XP")}
        for e in ("X1", "XP"):
            print(sym, e, {k: {kk: v[kk] for kk in ("n", "ort", "fark", "sharpe", "maxDD")} for k, v in res[sym][e].items()}, flush=True)
    ok = sum(res[s]["XP"]["TUM"]["sharpe"] > res[s]["X1"]["TUM"]["sharpe"] for s in res)
    res["ozet"] = {"XP_daha_iyi_endeks": int(ok), "gecer": bool(ok >= 2)}
    print(res["ozet"])
    (RES / "tasima.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))

if __name__ == "__main__":
    {"kesif": kesif, "dogrula": dogrula, "ekle": ekle, "tasima": tasima}[sys.argv[1]]()
