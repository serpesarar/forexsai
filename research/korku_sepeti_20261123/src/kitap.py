"""kitap.py — PROTOCOL.md: canlı NAS100 kitabı, tavan adayları (A0, A1-T, A2, A3), kontrol K, betimleme, KR-03 senaryosu.

python kitap.py → results/ozet.json, results/gunluk_A0.parquet, results/atlanan_A0.csv
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime

import numpy as np
import pandas as pd

import veri as V
from veri import lib

RES = V.HERE / "results"
SYM_CAP = 4.5
MIN_LOT = 0.10
CANDS = {"A0": ("A0", None), "A1_2.5": ("A1", 2.5), "A1_3.0": ("A1", 3.0), "A1_3.5": ("A1", 3.5), "A2": ("A2", None), "A3": ("A3", 3.0)}
MONTHS = pd.period_range("2018-01", "2026-11", freq="M")


# ───────── tavan politikası (yalnız o ana kadar açık pozisyonlarla) ─────────
def _trim(x: float) -> float:
    return math.floor(x * 100 + 1e-9) / 100


def assign(L: pd.DataFrame, kind: str, T: float | None) -> np.ndarray:
    lots = np.zeros(len(L))
    open_: list[tuple[int, float, bool]] = []
    for i, x in enumerate(L.itertuples()):
        open_ = [p for p in open_ if p[0] > x.t_in]          # aynı dakikada çıkış girişten önce
        tot = sum(p[1] for p in open_)
        fam = sum(p[1] for p in open_ if p[2])
        lot = x.lot0
        if x.fam and kind in ("A2", "A3") and fam > 0:
            lot = round(lot / 2, 2)
        if x.fam and kind in ("A1", "A3"):
            lot = min(lot, _trim(T - fam))
            if lot < MIN_LOT:
                lot = 0.0
        if lot > 0 and tot + lot > SYM_CAP + 1e-9:
            lot = 0.0
        lots[i] = lot
        if lot > 0:
            open_.append((x.t_out, lot, bool(x.fam)))
    return lots


# ───────── günlük $ (işaretli ya da gerçekleşen) ─────────
class Marker:
    def __init__(self, m1: lib.M1):
        self.m1 = m1
        dd = m1.d
        self.ends = np.r_[np.where(dd[1:] != dd[:-1])[0], len(dd) - 1]
        self.end_d = np.array([pd.Timestamp(dd[k]).date() for k in self.ends])

    def ny_date(self, t: int) -> date:
        i = min(int(np.searchsorted(self.m1.t, t, side="right")) - 1, len(self.m1.t) - 1)
        return pd.Timestamp(self.m1.d[max(i, 0)]).date()

    def legs_daily(self, L: pd.DataFrame, lots: np.ndarray, marked: bool = True) -> pd.DataFrame:
        m1, rows = self.m1, []
        for x, lot in zip(L.itertuples(), lots):
            if lot <= 0:
                continue
            usd = lot * x.px_in * x.bp / 1e4
            d_out = self.ny_date(x.t_out)
            if not marked:
                rows.append((d_out, x.rule, usd))
                continue
            i_in, i_out = int(np.searchsorted(m1.t, x.t_in)), int(np.searchsorted(m1.t, x.t_out))
            a, b = int(np.searchsorted(self.ends, i_in)), int(np.searchsorted(self.ends, i_out))
            prev, acc = x.px_in, 0.0
            for k in range(a, b):
                e = self.ends[k]
                if self.end_d[k] >= d_out:
                    break
                mark = m1.c[e] if x.side > 0 else m1.c[e] + m1.spr[e]
                v = lot * x.side * (mark - prev)
                rows.append((self.end_d[k], x.rule, v))
                acc += v
                prev = mark
            rows.append((d_out, x.rule, usd - acc))
        return pd.DataFrame(rows, columns=["d", "rule", "pnl"])


# ───────── ölçüler ─────────
def series(daily: pd.DataFrame, days: list[date]) -> pd.Series:
    s = daily.groupby("d").pnl.sum()
    return s.reindex(sorted(set(days) | set(s.index)), fill_value=0.0)


def stats(s: pd.Series) -> dict:
    eq = s.cumsum()
    dd = eq - eq.cummax()
    mo = s.groupby(pd.to_datetime(pd.Index(s.index)).to_period("M")).sum()
    mo = mo.reindex(MONTHS[(MONTHS >= mo.index.min()) & (MONTHS <= mo.index.max())], fill_value=0.0)
    srt = np.sort(s.values)
    n1 = max(1, int(round(0.01 * (s != 0).sum())))
    tot, mdd = float(s.sum()), float(dd.min())
    return {"toplam": tot, "maks_dusus": mdd, "maks_dusus_tarih": str(dd.idxmin()),
            "en_kotu_gun": float(s.min()), "en_kotu_gun_tarih": str(s.idxmin()), "en_kotu_10": float(srt[:10].sum()),
            "cvar1": float(srt[:n1].mean()), "calmar": tot / abs(mdd) if mdd < 0 else np.nan,
            "aylik_sharpe": float(mo.mean() / mo.std() * math.sqrt(12)) if mo.std() > 0 else np.nan}


def monthly(s: pd.Series) -> pd.Series:
    mo = s.groupby(pd.to_datetime(pd.Index(s.index)).to_period("M")).sum()
    return mo.reindex(MONTHS, fill_value=0.0)


def boot_sharpe(a: pd.Series, b: pd.Series, n: int = 4000, seed: int = 5) -> float:
    rng = np.random.default_rng(seed)
    A, B = monthly(a).values, monthly(b).values
    ix = rng.integers(0, len(A), (n, len(A)))
    return float((A[ix].mean(1) / A[ix].std(1) > B[ix].mean(1) / B[ix].std(1)).mean())


def halves(s: pd.Series) -> dict:
    idx = pd.Index(s.index)
    return {"ESKI": stats(s[idx <= lib.ESKI_END]), "YENI": stats(s[idx > lib.ESKI_END])}


# ───────── betimleme ─────────
def overlap_table(L: pd.DataFrame, lots: np.ndarray, s: pd.Series, mk: Marker) -> dict:
    """Gün sonunda açık korku kuralı sayısı → gün sayısı, ort $, toplam zarar payı."""
    m1 = mk.m1
    fam_open: dict[date, set] = {}
    for x, lot in zip(L.itertuples(), lots):
        if lot <= 0 or not x.fam:
            continue
        i_in, i_out = int(np.searchsorted(m1.t, x.t_in)), int(np.searchsorted(m1.t, x.t_out))
        a, b = int(np.searchsorted(mk.ends, i_in)), int(np.searchsorted(mk.ends, i_out))
        for k in range(a, b):
            fam_open.setdefault(mk.end_d[k], set()).add(x.rule)
        fam_open.setdefault(mk.ny_date(x.t_out), set()).add(x.rule)   # çıkış günü de riskte
    cnt = pd.Series({d: len(fam_open.get(d, ())) for d in s.index})
    loss = s.clip(upper=0)
    out = {}
    for c in sorted(cnt.unique()):
        m = cnt == c
        out[str(int(c))] = {"gun": int(m.sum()), "ort": float(s[m].mean()), "toplam": float(s[m].sum()),
                            "zarar_payi": float(loss[m].sum() / loss.sum()), "en_kotu": float(s[m].min())}
    top10 = s.nsmallest(10).index
    out["en_kotu_10_gun_ort_acik_korku"] = float(cnt.loc[top10].mean())
    out["en_kotu_10_gun_ikiplus_payi"] = float((cnt.loc[top10] >= 2).mean())
    return out


def composition(daily: pd.DataFrame, s: pd.Series) -> dict:
    top = s.nsmallest(10)
    by = daily[daily.d.isin(top.index)].groupby(["d", "rule"]).pnl.sum().unstack(fill_value=0.0)
    eq = s.cumsum()
    trough = eq.idxmin() if False else (eq - eq.cummax()).idxmin()
    peak = eq.loc[:trough].idxmax()
    win = daily[(daily.d > peak) & (daily.d <= trough)].groupby("rule").pnl.sum()
    return {"en_kotu_10": {str(d): {r: round(float(v), 1) for r, v in by.loc[d].items() if abs(v) > 0.5} for d in top.index},
            "maks_dusus_penceresi": {"tepe": str(peak), "dip": str(trough), "kural": {r: round(float(v), 1) for r, v in win.sort_values().items()}}}


def kr03_legs(L: pd.DataFrame, m1: lib.M1) -> pd.DataFrame:
    """KR-03: KORKU D1 16:00 zararı ≥ 50 bp → +0,75 lot D1 16:00 ask → KORKU çıkışı."""
    days = V._cal()
    nxt = {d: days[i + 1] for i, d in enumerate(days[:-1])}
    rows = []
    for x in L[L.rule == "KORKU"].itertuples():
        d1 = nxt.get(x.d)
        if d1 is None:
            continue
        t1 = lib.utc(d1, 960)
        if t1 >= x.t_out:
            continue
        i1, px1 = lib.entry_ix(m1, t1)
        if i1 is None:
            continue
        bid1 = px1 - m1.spr[i1]
        if (bid1 / x.px_in - 1) * 1e4 > -50:
            continue
        _, pxo = lib.exit_px(m1, x.t_out, 1)
        nights = (datetime.utcfromtimestamp(x.t_out).date() - d1).days
        bp = (pxo / px1 - 1) * 1e4 - V.FIN * nights
        rows.append(("KORKU_EK", d1, t1, int(x.t_out), 1, float(px1), 0.75, float(bp), "duka"))
    E = pd.DataFrame(rows, columns=V.COLS)
    E["fam"], E["ord"] = True, 8
    E["usd0"] = E.lot0 * E.px_in * E.bp / 1e4
    return E


def run_book(L: pd.DataFrame, mk: Marker, days: list[date], marked: bool) -> dict:
    out = {}
    for name, (kind, T) in CANDS.items():
        lots = assign(L, kind, T)
        dl = mk.legs_daily(L, lots, marked)
        s = series(dl, days)
        out[name] = {"lots": lots, "daily": dl, "s": s}
    return out


def verdict(r: dict, a0: dict, rh: dict, a0h: dict, rm: dict, a0m: dict) -> dict:
    c1 = r["maks_dusus"] >= 0.70 * a0["maks_dusus"] and r["en_kotu_10"] >= 0.70 * a0["en_kotu_10"]
    c2 = r["calmar"] >= 1.10 * a0["calmar"] and r["aylik_sharpe"] >= a0["aylik_sharpe"]
    c3 = all(rh[h]["calmar"] >= a0h[h]["calmar"] and rh[h]["aylik_sharpe"] >= a0h[h]["aylik_sharpe"] for h in ("ESKI", "YENI")) and \
        rm["calmar"] >= a0m["calmar"] and rm["aylik_sharpe"] >= a0m["aylik_sharpe"]
    h = "B" if c1 and c2 and c3 else ("C" if (c1 and c2) or (c2 and c3) else "X")
    return {"kuyruk": bool(c1), "risk_basina_kar": bool(c2), "dayaniklilik": bool(c3), "hukum": h}


def main() -> None:
    RES.mkdir(exist_ok=True)
    m1 = lib.load_m1()
    mk = Marker(m1)
    days = [d for d in V._cal() if date(2018, 1, 2) <= d <= date(2026, 11, 13)]
    L, chk = V.duka_legs()
    M, chk_m = V.mt5_legs(L, m1)
    out: dict = {"kontrol_kaynak": {k: list(v) for k, v in (chk | chk_m).items()}, "n_bacak": {"duka": len(L), "mt5": len(M)}}

    D = run_book(L, mk, days, True)
    Dr = run_book(L, mk, days, False)
    Mr = run_book(M, mk, days, False)
    a0, a0h, a0m = stats(D["A0"]["s"]), halves(D["A0"]["s"]), stats(Mr["A0"]["s"])
    tab = {}
    for name in CANDS:
        s = D[name]["s"]
        r, rh, rm = stats(s), halves(s), stats(Mr[name]["s"])
        lots = D[name]["lots"]
        tab[name] = {"duka_isaretli": r, "yarilar": rh, "duka_gerceklesen": stats(Dr[name]["s"]), "mt5_gerceklesen": rm,
                     "mt5_yarilar": halves(Mr[name]["s"]),
                     "P_sharpe_gt_A0": boot_sharpe(s, D["A0"]["s"]) if name != "A0" else None,
                     "lot_toplami_korku": float(lots[L.fam.values].sum()), "atlanan": int(((lots == 0)).sum()),
                     "kirpilan": int(((lots > 0) & (lots < L.lot0.values - 1e-9)).sum())}
        if name != "A0":
            tab[name]["olcut"] = verdict(r, a0, rh, a0h, rm, a0m)
            f = r["maks_dusus"] / a0["maks_dusus"]
            tab[name]["K_kontrol"] = {"f": f, "toplam_K": f * a0["toplam"], "en_kotu_10_K": f * a0["en_kotu_10"],
                                      "aday_toplam_fark": r["toplam"] - f * a0["toplam"]}
    out["adaylar"] = tab

    # betimleme (A0)
    lots0 = D["A0"]["lots"]
    s0, d0 = D["A0"]["s"], D["A0"]["daily"]
    out["cakisma"] = overlap_table(L, lots0, s0, mk)
    out["bilesim"] = composition(d0, s0)
    sk = L[lots0 == 0]
    sk.assign(usd=sk.usd0).to_csv(RES / "atlanan_A0.csv", index=False)
    out["atlanan_A0"] = {"n": len(sk), "kural": sk.rule.value_counts().to_dict(), "usd": float(sk.usd0.sum()),
                         "ort_bp": float(sk.bp.mean()) if len(sk) else None}
    piv = d0.groupby(["d", "rule"]).pnl.sum().unstack(fill_value=0.0).reindex(s0.index, fill_value=0.0)
    out["korelasyon"] = piv.corr().round(3).to_dict()
    out["kural_katki_A0"] = {r: float(v) for r, v in d0.groupby("rule").pnl.sum().items()}
    yil = s0.groupby(pd.to_datetime(pd.Index(s0.index)).year).sum()
    out["yil_A0"] = {int(k): float(v) for k, v in yil.items()}
    s0.to_frame("pnl").to_parquet(RES / "gunluk_A0.parquet")

    # KR-03 senaryosu (betimleyici)
    E = kr03_legs(L, m1)
    LE = pd.concat([L, E], ignore_index=True).sort_values(["t_in", "ord"]).reset_index(drop=True)
    lots_e = assign(LE, "A0", None)
    se = series(mk.legs_daily(LE, lots_e, True), days)
    out["KR03"] = {"ek_n": len(E), "ek_ort_bp": float(E.bp.mean()) if len(E) else None, "ek_acilan": int((lots_e[LE.rule.values == "KORKU_EK"] > 0).sum()),
                   "A0_arti_KR03": stats(se), "yarilar": halves(se)}

    (RES / "ozet.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    pr = ["toplam", "maks_dusus", "en_kotu_gun", "en_kotu_10", "calmar", "aylik_sharpe"]
    print("aday       " + "  ".join(f"{p:>11}" for p in pr) + "   MT5 calmar/sharpe   hüküm")
    for name, t in tab.items():
        r = t["duka_isaretli"]
        print(f"{name:9}  " + "  ".join(f"{r[p]:11.2f}" for p in pr),
              f"  {t['mt5_gerceklesen']['calmar']:6.2f}/{t['mt5_gerceklesen']['aylik_sharpe']:5.2f}", t.get("olcut", {}).get("hukum", ""))
    print(json.dumps({k: out[k] for k in ("cakisma", "atlanan_A0", "KR03")}, indent=1, ensure_ascii=False, default=str)[:4000])


if __name__ == "__main__":
    main()
