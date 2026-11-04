"""dv_0_hazirlik.py — SINAMA ÖNCESİ hazırlık (PROTOCOL.md §2 hizalama, §3 keşif etkileri, §5 keşif plasebosu).

Sınama verisinde (NDX ≥ 2025-12-01, DAX, QQQ) HİÇBİR getiri/hipotez istatistiği hesaplamaz ya da basmaz:
yalnız saat ekseni denetimleri (bar aralığı profili, nakit kapanışıyla std, kaynaklar arası OHLC eşleşmesi) ve
geçerli gece SAYILARI. Keşif sayıları (ts < 2025-12-01) aynı çekirdekle birebir yeniden üretilir.
Çıktı: results/hazirlik.json (+ stdout).
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dv_core import (B15, B1M, BER, DAX1H, DAX30, HOLD, NY, RES, Px, Z_ALPHA, Z_POWER, agg_15m_to_1h,  # noqa: E402
                     boot_specs, boot_summary, dax_nights, describe, fix_dax_axis, load_long1h, ny_calendar,
                     ndx_nights, qqq_nights, xetra_days)

OUT: dict = {}


def p(*a) -> None:
    print(*a, flush=True)


# ───────── 1. keşif yeniden üretimi + etkiler ─────────
def exploration(cal: pd.DataFrame) -> None:
    d = load_long1h(before=HOLD)
    px = Px(d.ts, d.close.to_numpy(), 60)
    E = ndx_nights(cal, px, date(2016, 1, 1), date(2025, 11, 30))
    r = describe(E)
    dn, up = (E.rl < 0).to_numpy(), (E.rl > 0).to_numpy()
    bs = boot_specs(E.i.to_numpy(), {"pts": (dn, up, E.on.to_numpy()), "pct": (dn, up, E.onp.to_numpy()),
                                     "up": (dn, up, (E.on > 0).to_numpy(float) * 100)})
    r["boot"] = {k: boot_summary(v) for k, v in bs.items()}
    hedef = dict(n=2334, up_asagi=60.75174825174825, up_yukari=55.21008403361345, pts_asagi=13.612062937062893,
                 pts_yukari=0.4984033613444808)
    eslesme = all(abs(r[k] - v) < 1e-6 for k, v in hedef.items())
    r["kesif_ek_tanimsal_ile_birebir"] = bool(eslesme)
    p("KEŞİF yeniden üretim:", json.dumps({k: r[k] for k in ["n", "n_asagi", "up_asagi", "up_yukari", "pts_asagi",
                                                             "pts_yukari", "pct_asagi", "pct_yukari", "pct_fark",
                                                             "up_fark", "sd_pct_tum"]}), "birebir:", eslesme)
    p("  boot P:", {k: round(v["P"], 4) for k, v in r["boot"].items()}, "sd:", {k: round(v["sd_boot"], 5) for k, v in r["boot"].items()})
    if not eslesme:
        raise SystemExit("keşif sayıları birebir üretilemedi — DUR")
    # çağlar
    era = {}
    for nm, a, b in (("2016-2020", date(2016, 1, 1), date(2020, 12, 31)), ("2021-2025", date(2021, 1, 1), date(2025, 11, 30))):
        S = E[(E.D >= a) & (E.D <= b)]
        q = describe(S)
        era[nm] = {k: q[k] for k in ["n", "pct_asagi", "pct_yukari", "pct_fark", "up_asagi", "up_yukari", "up_fark",
                                     "pts_fark", "up_kosulsuz", "pct_kosulsuz"]}
    r["cag"] = era
    p("  çağlar:", json.dumps(era))
    # plasebo (keşif, bağlam)
    P_ = E[np.isfinite(E.rp) & (E.rp != 0)].reset_index(drop=True)
    q = describe(P_, "rp")
    q_main = describe(P_)
    dnp, upp = (P_.rp < 0).to_numpy(), (P_.rp > 0).to_numpy()
    dnm, upm = (P_.rl < 0).to_numpy(), (P_.rl > 0).to_numpy()
    b2 = boot_specs(P_.i.to_numpy(), {"plc": (dnp, upp, P_.onp.to_numpy()), "main": (dnm, upm, P_.onp.to_numpy())})
    r["plasebo_kesif"] = dict(n=q["n"], pct_fark=q["pct_fark"], up_fark=q["up_fark"], P_plc=float(np.mean(b2["plc"] > 0)),
                              main_pct_fark_ayni_geceler=q_main["pct_fark"],
                              P_main_eksi_plc=float(np.mean(b2["main"] - b2["plc"] > 0)))
    p("  plasebo (11→12 NY) keşif:", json.dumps(r["plasebo_kesif"]))
    # duyarlılık: 2017-11-05 → 2018-02-26 eksen düzeltmesi
    dfx = d.copy()
    nyd = dfx.ts.dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    m = (nyd >= "2017-11-05") & (nyd <= "2018-02-26")
    dfx.loc[m, "ts"] = dfx.ts[m] - pd.Timedelta(minutes=60)
    dfx = dfx.sort_values("ts").drop_duplicates("ts", keep="first")
    Ex = ndx_nights(cal, Px(dfx.ts, dfx.close.to_numpy(), 60), date(2016, 1, 1), date(2025, 11, 30))
    qx = describe(Ex)
    r["duyarlilik_eksen_fix"] = {k: qx[k] for k in ["n", "pct_fark", "up_fark", "pts_fark"]}
    p("  eksen-düzeltmeli keşif (bağlam):", json.dumps(r["duyarlilik_eksen_fix"]))
    OUT["kesif"] = r
    # eşikler
    E_pct, E_up = r["pct_fark"], r["up_fark"]
    d_E = E_pct / r["sd_pct_tum"]
    OUT["esikler"] = dict(E_pct=E_pct, E_up=E_up, E_pts=r["pts_fark"], sd_pct_kesif=r["sd_pct_tum"], d_E=d_E,
                          esik_pct_NDX=0.5 * E_pct, esik_up=0.5 * E_up, esik_d_DAX=0.5 * d_E)
    p("EŞİKLER:", json.dumps(OUT["esikler"]))


# ───────── 2. NDX hizalama ─────────
def ndx_alignment(cal: pd.DataFrame) -> None:
    h1 = load_long1h()
    d15 = pd.read_parquet(B15)
    a1 = agg_15m_to_1h(d15)
    res = {}
    for nm, a, b in (("2025-11-17..21", "2025-11-17", "2025-11-22"), ("2026-07-06..10", "2026-07-06", "2026-07-11")):
        x = h1[(h1.ts >= pd.Timestamp(a, tz="UTC")) & (h1.ts < pd.Timestamp(b, tz="UTC"))].merge(a1, on="ts", suffixes=("", "_a"))
        x = x[x.n == 4]
        ok = (np.abs(x.high - x.high_a) <= 0.5) & (np.abs(x.low - x.low_a) <= 0.5) & (np.abs(x.close - x.close_a) <= 0.5)
        res[nm] = dict(n_bar=int(len(x)), pay_eslesen=float(ok.mean()), maks_dC=float(np.abs(x.close - x.close_a).max()))
    p("15m→1h vs long_1h:", json.dumps(res))
    OUT["hiza_15m_1h"] = res
    # 1m → 15m (2026-07-15 sonrası bağımsız kaynak)
    m1 = pd.read_parquet(B1M)
    m1 = m1[m1.ts >= pd.Timestamp("2026-07-15", tz="UTC")].copy()
    m1["b"] = m1.ts.dt.floor("15min")
    m1["last"] = m1.ts.dt.minute % 15 == 14
    g = m1.groupby("b").agg(c=("close", "last"), hi=("high", "max"), lo=("low", "min"), lastok=("last", "max"),
                            n=("ts", "size")).reset_index()
    g = g[g.lastok & (g.n >= 12)]
    x15 = d15[d15.ts >= pd.Timestamp("2026-07-15", tz="UTC")][["ts", "close", "high", "low"]]
    res2 = {}
    for s in (-60, -15, 0, 15, 60):
        y = x15.assign(k=x15.ts + pd.Timedelta(minutes=s)).merge(g, left_on="k", right_on="b")
        res2[s] = dict(n=int(len(y)), pay_dC_le2=float((np.abs(y.close - y.c) <= 2).mean()),
                       medyan_dC=float(np.median(np.abs(y.close - y.c))))
    p("15m (≥07-15) vs 1m→15m, kayma dk:", json.dumps(res2))
    OUT["hiza_15m_1m"] = res2
    # aylık: 16:00 NY kapanışı vs NDXCASH_close std (bp), kayma −60/0/+60
    cash = cal.set_index("d").NDXCASH_close

    def std_check(px_fn, months: list[str]) -> dict:
        out = {}
        for mo in months:
            ds = [dd for dd in cal.d if str(dd)[:7] == mo]
            row = {}
            for s in (-60, 0, 60):
                hh, mm = divmod(16 * 60 + s, 60)
                e = [(px_fn(t_ns_(dd, hh, mm, NY)) - cash[dd]) / cash[dd] * 1e4 for dd in ds]
                e = np.array([v for v in e if np.isfinite(v)])
                row[s] = (round(float(e.std(ddof=1)), 2) if len(e) > 2 else None, int(len(e)))
            best = min((k for k in row if row[k][0] is not None), key=lambda k: row[k][0], default=None)
            out[mo] = dict(std_bp={k: v[0] for k, v in row.items()}, n={k: v[1] for k, v in row.items()}, en_iyi=best)
        return out

    from dv_core import t_ns as t_ns_
    px1h = Px(h1.ts, h1.close.to_numpy(), 60)
    px15 = Px(d15.ts, d15.close.to_numpy(), 15)
    mo_h = [f"2025-{m:02d}" for m in (12,)] + [f"2026-{m:02d}" for m in range(1, 8)]
    mo_x = ["2026-07", "2026-08", "2026-09"]
    sc1 = std_check(px1h, mo_h)
    sc2 = std_check(px15, mo_x)
    p("long_1h holdout ayları en iyi kayma:", {k: v["en_iyi"] for k, v in sc1.items()})
    p("15m uzatma ayları en iyi kayma:", {k: v["en_iyi"] for k, v in sc2.items()})
    OUT["hiza_nakit_std_long1h"] = sc1
    OUT["hiza_nakit_std_15m"] = sc2
    # açılış tepe profili
    def peak(d: pd.DataFrame, a: str, b: str) -> dict:
        x = d[(d.ts >= pd.Timestamp(a, tz="UTC")) & (d.ts < pd.Timestamp(b, tz="UTC"))].copy()
        ny = x.ts.dt.tz_convert("America/New_York")
        x = x[ny.dt.weekday < 5]
        ny = x.ts.dt.tz_convert("America/New_York")
        x["mo"] = ny.dt.strftime("%Y-%m").values
        x["slot"] = ny.dt.strftime("%H:%M").values
        x["r"] = x.high - x.low
        g = x.groupby(["mo", "slot"]).r.median().reset_index()
        return {mo: gg.loc[gg.r.idxmax(), "slot"] for mo, gg in g.groupby("mo")}
    pk15 = peak(d15, "2026-07-01", "2026-10-03")
    pk1h = peak(h1, "2025-12-01", "2026-07-15")
    p("15m tepe dilimi (NY):", pk15, "| long_1h tepe dilimi (NY):", pk1h)
    OUT["tepe_15m"] = pk15
    OUT["tepe_1h"] = pk1h


# ───────── 3. DAX eksen ─────────
def dax_alignment() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw30, raw1h = pd.read_parquet(DAX30), pd.read_parquet(DAX1H)
    f30, f1h = fix_dax_axis(raw30), fix_dax_axis(raw1h)

    def prof(d: pd.DataFrame, since: str) -> dict:
        x = d[d.ts >= pd.Timestamp(since, tz="UTC")].copy()
        be = x.ts.dt.tz_convert("Europe/Berlin")
        nyl = x.ts.dt.tz_convert("America/New_York")
        x = x[be.dt.weekday.values < 5]
        be = x.ts.dt.tz_convert("Europe/Berlin")
        nyl = x.ts.dt.tz_convert("America/New_York")
        ber_dst = ((be.dt.tz_localize(None) - x.ts.dt.tz_localize(None)) / pd.Timedelta(hours=1) == 2).to_numpy()
        ny_dst = ((nyl.dt.tz_localize(None) - x.ts.dt.tz_localize(None)) / pd.Timedelta(hours=1) == -4).to_numpy()
        cls = np.where(ny_dst & ber_dst, "ikisi_yaz", np.where(~ny_dst & ~ber_dst, "ikisi_kis", "omuz"))
        x["k"] = be.dt.year.astype(str).values + "|" + cls
        x["slot"] = be.dt.strftime("%H:%M").values
        x["r"] = x.high - x.low
        g = x.groupby(["k", "slot"]).r.median().reset_index()
        pk = {k: gg.loc[gg.r.idxmax(), "slot"] for k, gg in g.groupby("k")}
        return dict(pay_0900=float(np.mean([v == "09:00" for v in pk.values()])), n_grup=len(pk), tepe=pk)

    r = {"30m_ham": prof(raw30, "2021-03-17"), "30m_fix": prof(f30, "2021-03-17"),
         "1h_ham": prof(raw1h, "2020-01-01"), "1h_fix": prof(f1h, "2020-01-01")}
    p("DAX tepe = 09:00 Berlin payı:", {k: (round(v["pay_0900"], 3), v["n_grup"]) for k, v in r.items()})
    for k in ("30m_fix", "1h_fix"):
        bad = {g: s for g, s in r[k]["tepe"].items() if s != "09:00"}
        p(f"  {k} 09:00 olmayan gruplar:", bad)
    # 1h fix vs 30m fix toplamı
    m = f30.copy()
    m["h"] = m.ts.dt.floor("h")
    agg = m.groupby("h").agg(hi=("high", "max"), lo=("low", "min"), c=("close", "last"), n=("ts", "size"))
    agg = agg[agg.n == 2]
    x = f1h.merge(agg, left_on="ts", right_index=True)
    ok = np.isclose(x.high, x.hi, atol=0.05) & np.isclose(x.low, x.lo, atol=0.05) & np.isclose(x.close, x.c, atol=0.05)
    r["1h_fix_vs_30m_fix_eslesme"] = dict(n=int(len(x)), pay=float(ok.mean()))
    p("DAX 1h_fix vs 30m_fix toplamı eşleşme:", r["1h_fix_vs_30m_fix_eslesme"])
    OUT["dax_eksen"] = {k: (v if not isinstance(v, dict) or "tepe" not in v else {kk: vv for kk, vv in v.items()})
                        for k, v in r.items()}
    return f30, f1h


# ───────── 4. gece SAYILARI (istatistik yok) ─────────
def counts(cal: pd.DataFrame, f30: pd.DataFrame, f1h: pd.DataFrame) -> None:
    h1 = load_long1h()
    d15 = pd.read_parquet(B15)
    a1 = agg_15m_to_1h(d15)
    c = {}
    H = ndx_nights(cal, Px(h1.ts, h1.close.to_numpy(), 60), date(2025, 12, 1), date(2026, 7, 13))
    X = ndx_nights(cal, Px(a1.ts, a1.close.to_numpy(), 60, a1.last45.to_numpy()), date(2026, 7, 14), date(2026, 12, 31))
    xd30 = xetra_days(f30.ts.min().tz_convert(BER).date(), f30.ts.max().tz_convert(BER).date())
    xd1h = xetra_days(date(2020, 1, 1), f1h.ts.max().tz_convert(BER).date())
    D30 = dax_nights(xd30, Px(f30.ts, f30.close.to_numpy(), 30), date(2021, 3, 17), date(2026, 12, 31), (16, 30), (17, 30))
    D1 = dax_nights(xd1h, Px(f1h.ts, f1h.close.to_numpy(), 60), date(2020, 1, 1), date(2026, 12, 31), (17, 0), (18, 0))
    Q = qqq_nights(cal, date(2015, 1, 1), date(2026, 12, 31))
    for nm, T in (("N-H", H), ("N-X", X), ("D-30", D30), ("D-1h", D1), ("Q-D", Q)):
        c[nm] = dict(n_aday=int(T.attrs.get("n_aday", len(T))), n_gecerli=int(len(T)),
                     ilk=str(T.D.min()) if len(T) else None, son=str(T.D.max()) if len(T) else None)
    c["takvim_son_gun"] = str(cal.d.max())
    c["takvim_kapanis_vs_ohlc_0728e_kadar_ayni"] = bool(cal[cal.date <= "2026-07-28"].ohlc_ok.all())
    c["holdout_erken_gunler"] = [str(x) for x in cal.d[cal.early & (cal.date >= "2025-12-01")]]
    p("GECE SAYILARI (yalnız sayım):", json.dumps(c))
    OUT["sayim"] = c
    # a-priori MDE (keşif bootstrap sd'sinden ölçekli)
    k = OUT["kesif"]
    nE = k["n"]
    n_hx = c["N-H"]["n_gecerli"] + c["N-X"]["n_gecerli"]
    sc = np.sqrt(nE / n_hx)
    mde = {u: (Z_ALPHA + Z_POWER) * k["boot"][u]["sd_boot"] * sc for u in ("pct", "up", "pts")}
    nd = c["D-30"]["n_gecerli"]
    mde_d = (Z_ALPHA + Z_POWER) * (k["boot"]["pct"]["sd_boot"] / k["sd_pct_tum"]) * np.sqrt(nE / nd)
    OUT["apriori_MDE"] = dict(N_HX_n=n_hx, N_HX_pct=mde["pct"], N_HX_up=mde["up"], N_HX_pts_kesif_olcegi=mde["pts"],
                              D30_n=nd, D30_d=mde_d)
    p("A-PRIORI MDE80:", json.dumps(OUT["apriori_MDE"]))
    # DAX: tatillerde bar var mı (bilgi)
    be = f30.ts.dt.tz_convert("Europe/Berlin")
    bd = pd.Series(be.dt.date.values)
    hol_bars = {}
    for y in range(2021, 2027):
        from dv_core import easter
        from datetime import timedelta
        e = easter(y)
        for nm, dd in (("KutsalCuma", e - timedelta(days=2)), ("PaskPzt", e + timedelta(days=1)), ("1May", date(y, 5, 1)),
                       ("PfingstPzt", e + timedelta(days=50)), ("3Ekim", date(y, 10, 3)), ("24Ara", date(y, 12, 24)),
                       ("31Ara", date(y, 12, 31))):
            if dd.weekday() < 5:
                hol_bars[f"{y}-{nm}"] = int((bd == dd).sum())
    OUT["dax_tatil_bar_sayisi"] = hol_bars
    p("DAX 30m tatil günlerinde bar sayısı (bilgi):", hol_bars)


def main() -> None:
    RES.mkdir(exist_ok=True)
    cal = ny_calendar()
    exploration(cal)
    ndx_alignment(cal)
    f30, f1h = dax_alignment()
    counts(cal, f30, f1h)
    json.dump(OUT, open(RES / "hazirlik.json", "w"), indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
