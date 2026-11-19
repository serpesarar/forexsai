"""derin.py — KSG derin araştırma (PROTOCOL): A gece yolu gruplaması, B bilanço gecesi, C koşullu çıkış. python derin.py"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES, DATA = HERE / "results", HERE / "data"
for p in ("research/ksg_opex_canli_20261119/src", "research/korku_evren_20261119/src"):
    sys.path.insert(0, str(ROOT / p))
import oynat as Oy  # noqa: E402
import esik as E  # noqa: E402

NY = "America/New_York"
FEEDS = ["MT5_NAS100", "DUKA_NDX", "MT5_US500", "MT5_US30", "MT5_US2000"]
BLIND = ["MT5_US500", "MT5_US30", "MT5_US2000"]
KESIF_SON = pd.Timestamp("2021-10-31")
EVE = {"p18": (18, 0), "p20": (20, 0)}
MORN = {"p00": (0, 0), "p03": (3, 0), "p06": (6, 0), "p0830": (8, 30), "p0930": (9, 30)}
CHECK = {"20:00": "p20", "00:00": "p00", "03:00": "p03", "06:00": "p06"}
KS = (50, 100, 150)
TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "NFLX", "AMD", "ORCL", "COST"]
RNG = np.random.default_rng(37)


def ts(d, hh, mm) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def earnings() -> dict:
    """Kapanış sonrası (≥ 15:00 ET) bilanço günleri → açıklayan şirketler. Önbellek data/earnings.json."""
    f = DATA / "earnings.json"
    if f.exists():
        return {pd.Timestamp(k): v for k, v in json.loads(f.read_text()).items()}
    import yfinance as yf
    out: dict = {}
    for s in TICKERS:
        x = yf.Ticker(s).get_earnings_dates(limit=60)
        for t in x.index:
            loc = t.tz_convert(NY)
            if loc.hour >= 15:
                out.setdefault(str(loc.normalize().tz_localize(None).date()), []).append(s)
    DATA.mkdir(exist_ok=True)
    f.write_text(json.dumps(out))
    return {pd.Timestamp(k): v for k, v in out.items()}


def path_table(name: str) -> pd.DataFrame:
    n = Oy.nights(name)
    if name == "MT5_US500":
        n = n[n.d >= "2018-06-01"]
    b = Oy.bars30(name)
    t, o, sp = b.t.values, b.o.values, b.sp.values

    def px(u):
        i = int(np.searchsorted(t, u, side="right")) - 1          # u'da ya da önce açılan son bar
        return o[i] if i >= 0 and u - t[i] <= 2 * 3600 else np.nan
    days = sorted(set(pd.to_datetime([pd.Timestamp(x, unit="s", tz="UTC").tz_convert(NY).date() for x in t[::10]])))
    rows = []
    for r in n.itertuples():
        d = r.d
        i16 = int(np.searchsorted(t, ts(d, 16, 0)))
        ask = o[i16] + sp[i16]
        o15 = px(ts(d, 15, 0))
        # sonraki işlem günü: net'te kullanılan 09:30 (oynat ile aynı) → net'ten geri çöz
        nd = d + timedelta(days=1)
        while not Oy.kl.is_trading_day(nd.date()) or np.isnan(px(ts(nd, 9, 30))):
            nd += timedelta(days=1)
            if (nd - d).days > 6:
                break
        rec = {"besleme": name, "d": d, "nd": nd, "net": r.net, "vix_prev": r.vix_prev, "vadeye": r.vadeye, "ask": ask,
               "son_saat_bp": (o[i16] / o15 - 1) * 1e4 if o15 == o15 else np.nan,
               "fin": r.net - ((px(ts(nd, 9, 30)) / ask - 1) * 1e4)}
        for k, (hh, mm) in EVE.items():
            rec[k] = px(ts(d, hh, mm))
        for k, (hh, mm) in MORN.items():
            rec[k] = px(ts(nd, hh, mm))
        rows.append(rec)
    P = pd.DataFrame(rows)
    P["donem"] = np.where(P.d <= KESIF_SON, "KESIF", "TEST")
    a = P.ask
    P["AH"] = (P.p18 / a - 1) * 1e4
    P["ASYA"] = (P.p03 / P.p18 - 1) * 1e4
    P["AVRUPA"] = (P.p0830 / P.p03 - 1) * 1e4
    P["VERI"] = (P.p0930 / P.p0830 - 1) * 1e4
    return P


def boot_diff(a, da, b, n=2000):
    """a'nın ortalaması − b'nin ortalaması; a gün bloklu bootstrap; P(fark > 0)."""
    ud = np.unique(da)
    pos = {u: np.flatnonzero(da == u) for u in ud}
    mb = b.mean()
    return float(np.mean([np.concatenate([a[pos[u]] for u in RNG.choice(ud, len(ud))]).mean() - mb > 0 for _ in range(n)]))


def sharpe(P: pd.DataFrame, col: str) -> float:
    days = pd.bdate_range(P.d.min(), P.d.max())
    s = P.groupby("d")[col].sum().reindex(days).fillna(0)
    return round(float(s.mean() / s.std() * np.sqrt(252)), 3)


# ---------------- A ----------------
def part_a(T: dict) -> dict:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    out = {}
    P = T["MT5_NAS100"].dropna(subset=["AH", "ASYA", "AVRUPA", "VERI"])
    seg = ["AH", "ASYA", "AVRUPA", "VERI"]
    out["dilim_ort"] = {g: P[sel][seg].mean().round(1).to_dict() for g, sel in (("kazanan", P.net > 0), ("kaybeden", P.net < 0), ("tum", P.net == P.net))}
    L = P[P.net < 0]
    worst = L[seg].idxmin(axis=1).value_counts(normalize=True).round(3).to_dict()
    out["kaybeden_en_eksi_dilim_payi"] = worst
    Z = (L[seg] - L[seg].mean()) / L[seg].std()
    sil = {k: float(silhouette_score(Z, KMeans(k, n_init=10, random_state=0).fit_predict(Z))) for k in range(2, 6)}
    kb = max(sil, key=sil.get)
    lab = KMeans(kb, n_init=10, random_state=0).fit_predict(Z)
    out["kaybeden_tipleri"] = [{"tip": int(c), "n": int((lab == c).sum()), "ort_net": round(float(L.net[lab == c].mean()), 1),
                               **{s: round(float(L[s][lab == c].mean()), 1) for s in seg}} for c in range(kb)]
    # ayrıntılı grup tablosu
    ev = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev["date"] = pd.to_datetime(ev.date)
    sab = set(ev[ev.event.isin(["CPI", "NFP"])].date)
    fomc = set(ev[ev.event == "FOMC"].date)
    ern = earnings()
    t30 = set(pd.to_datetime(pd.read_csv(ROOT / "research/korku_evren_20261119/results/t30_islemler_MT5_NAS100.csv").d))
    P = T["MT5_NAS100"].copy()
    P["vix3"] = pd.qcut(P.vix_prev, 3, labels=["VIX düşük", "VIX orta", "VIX yüksek"])
    P["son3"] = pd.qcut(P.son_saat_bp, 3, labels=["son saat derin", "son saat orta", "son saat hafif"])
    P["gun"] = P.d.dt.day_name()
    flags = {"ertesi sabah CPI/NFP": P.nd.isin(sab), "ertesi gün FOMC": P.nd.isin(fomc), "KORKU-T30 gecesi": P.d.isin(t30),
             "bilanço gecesi": P.d.isin(set(ern)), "vadeye 0–2": P.vadeye <= 2}
    rows = []
    for col in ("vix3", "son3", "gun"):
        for g, z in P.groupby(col):
            rows.append(_grp(f"{col}={g}", z))
    for nm, m in flags.items():
        rows.append(_grp(nm, P[m]))
        rows.append(_grp(f"değil: {nm}", P[~m]))
    out["grup_tablosu"] = rows
    return out


def _grp(nm, z):
    r = {"grup": nm, "n": len(z)}
    for era in ("KESIF", "TEST"):
        q = z[z.donem == era]
        r[era] = {"n": len(q), "ort": round(float(q.net.mean()), 1) if len(q) else None, "kaybeden_%": round(float((q.net < 0).mean() * 100), 1) if len(q) else None}
    return r


# ---------------- B ----------------
def part_b(T: dict) -> dict:
    ern = set(earnings())
    out = {}
    for f, P in T.items():
        m = P.d.isin(ern)
        rec = {}
        for era in ("KESIF", "TEST", "TUM"):
            z = P if era == "TUM" else P[P.donem == era]
            mm = z.d.isin(ern)
            a, b = z[mm].net.values, z[~mm].net.values
            rec[era] = {"n_bilanco": int(mm.sum()), "bilanco": round(float(a.mean()), 1) if len(a) else None,
                        "bilancosuz": round(float(b.mean()), 1), "fark": round(float(a.mean() - b.mean()), 1) if len(a) else None,
                        "P_fark_arti": round(boot_diff(a, z[mm].d.values, b), 3) if len(a) > 5 else None}
        out[f] = rec
        print("B", f, rec, flush=True)
    sgn = [np.sign(out[f][e]["fark"]) for f in ("MT5_NAS100", "DUKA_NDX") for e in ("KESIF", "TEST")]
    p = out["MT5_NAS100"]["TUM"]["P_fark_arti"]
    kor = [np.sign(out[f]["TUM"]["fark"]) for f in BLIND]
    ok = len(set(sgn)) == 1 and (p >= 0.95 or p <= 0.05) and sum(k == sgn[0] for k in kor) >= 2
    out["hukum"] = "B" if ok else ("C" if len(set(sgn)) == 1 else "X")
    return out


# ---------------- C ----------------
def cond_exit(P: pd.DataFrame, chk: str, k: int, side: str) -> np.ndarray:
    pnl = (P[CHECK[chk]] / P.ask - 1) * 1e4
    hit = (pnl <= -k) if side == "kes" else (pnl >= k)
    hit = hit.fillna(False).values
    return np.where(hit, pnl.values + P.fin.values, P.net.values)


def part_c(T: dict) -> dict:
    out = {"hucreler": {}}
    K = T["MT5_NAS100"][T["MT5_NAS100"].donem == "KESIF"]
    for chk in CHECK:
        for k in KS:
            for side in ("kes", "kar_al"):
                v = cond_exit(K, chk, k, side)
                out["hucreler"][f"{side}|{chk}|{k}"] = {"kesif_fark": round(float(v.mean() - K.net.mean()), 2),
                                                       "tetik_%": round(float((v != K.net.values).mean() * 100), 1)}
    best = sorted(out["hucreler"], key=lambda c: out["hucreler"][c]["kesif_fark"], reverse=True)[:2]
    out["secilen"] = best
    print("C KEŞİF en iyi:", [(c, out["hucreler"][c]) for c in best], "| en kötü:",
          sorted(out["hucreler"].items(), key=lambda x: x[1]["kesif_fark"])[:2], flush=True)
    for c in best:
        side, chk, k = c.split("|")
        rec = {}
        for f, P in T.items():
            z = P[P.donem == "TEST"] if f in ("MT5_NAS100", "DUKA_NDX") else P
            v = cond_exit(z, chk, int(k), side)
            rec[f] = {"n": len(z), "taban": round(float(z.net.mean()), 2), "kural": round(float(v.mean()), 2),
                      "fark": round(float(v.mean() - z.net.mean()), 2),
                      "P": round(boot_diff(v - z.net.values, z.d.values, np.zeros(1)), 3),
                      "sharpe": {"taban": sharpe(z, "net"), "kural": sharpe(z.assign(_v=v), "_v")}}
        kor = sum(1 for f in BLIND if rec[f]["fark"] > 0)
        ok = all(rec[f]["fark"] > 0 and rec[f]["P"] >= 0.975 for f in ("MT5_NAS100", "DUKA_NDX")) and kor >= 2 and \
            all(rec[f]["sharpe"]["kural"] > rec[f]["sharpe"]["taban"] for f in ("MT5_NAS100", "DUKA_NDX"))
        rec["kor"], rec["hukum"] = f"{kor}/3", "B" if ok else "X"
        out[c] = rec
        print("C", c, {f: (rec[f]["fark"], rec[f]["P"], rec[f]["sharpe"]) for f in FEEDS}, "→", rec["hukum"], flush=True)
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    Oy.kl.ay.NYSE_HOLIDAYS = set(Oy.kl.ay.NYSE_HOLIDAYS) | Oy.holidays()
    T = {f: path_table(f) for f in FEEDS}
    chk = T["MT5_NAS100"]
    seg_sum = chk.AH + chk.ASYA + chk.AVRUPA + chk.VERI + chk.fin
    print("dilim toplamı ≈ net: medyan |fark|", round(float((seg_sum - chk.net).abs().median()), 3), "bp", flush=True)
    res = {"A": part_a(T)}
    print("A dilim ort:", res["A"]["dilim_ort"], "\nA kaybeden en eksi dilim:", res["A"]["kaybeden_en_eksi_dilim_payi"],
          "\nA kaybeden tipleri:", res["A"]["kaybeden_tipleri"], flush=True)
    for r in res["A"]["grup_tablosu"]:
        print("   ", r["grup"], r["KESIF"], r["TEST"])
    res["B"] = part_b(T)
    print("B hüküm:", res["B"]["hukum"])
    res["C"] = part_c(T)
    (RES / "derin.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
