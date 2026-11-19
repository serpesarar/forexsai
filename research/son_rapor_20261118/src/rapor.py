"""rapor.py — bu sohbette onaylanabilir (B/B−) bulunan tüm kapıların uçtan uca yeniden sınaması.

Kapılar (defter):
  T  K1 korku gecesi (taban kural, §2.71) — 16:00 ≤ TWAP −%0,5 ∧ son saat aşağı → 16:00 AL → ertesi 16:00
  G1 YK-08  korku ertesi seansı: K1 günü → ertesi gün 09:30 AL → 16:00 (gece riski yok)
  G2 GN-05  art arda korku dozu: K1(d) ∧ (K1(d−1) ∨ d−1 nakit seansı ≤ −%1) → lot ×1,5
  G3 ZA-04  olay günü vetosu: K1 günü CPI/NFP/FOMC/Jackson Hole → açma
  G4 KC-01  XP çıkışı: ilk yükselen 16:00 kapanışında çık (en geç 5 gün)
  G5 SV-01  OPEX korku vetosu: aylık OPEX'e 0–2 işlem günü kala korku alımı açma (K1, ES, C3b)
  G6 MX-04  vade sonrası dozu: son OPEX'ten 3.–7. işlem günü korku alımı ×1,5 (K1, C3b)
  G7 GX-05  KSG OPEX vetosu: canlı KSG'yi OPEX'e 0–2 gün kala açma
python rapor.py test | kos
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/vade_mantik_20261118/src", "research/son4_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import vm  # noqa: E402
import ox  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

G, V = ox.G, ox.V
NY = "America/New_York"
FIN = V.FIN
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
EVENTS = ("CPI", "NFP", "FOMC", "JH")
# Olay takviminin kapsam sonu. 2026-11-19 (E148): takvim FOMC'de 2026-06-17'de bitiyordu (07-29 ve 09-16 kaçıyordu);
# FOMC/CPI/NFP/JH tamamlandı, kapsam research/korku_golge_20261119/olay_takvimi.csv ile aynı.
CAL_END = pd.Timestamp("2027-07-31")


# ---------------- takvim ----------------
def trading_calendar() -> pd.DatetimeIndex:
    """Geçmiş: veri günleri. Gelecek: NYSE iş günleri (vade takvimi önceden bilinir; canlıda da böyle üretilmeli)."""
    past = set(V.ohlc("QQQ").index) | set(V.ndx_frame().index)
    last = max(past)
    fut = [d for d in pd.bdate_range(last + pd.Timedelta(days=1), "2027-12-31") if G.nyse_ok(d.date())]
    return pd.DatetimeIndex(sorted(past | set(fut)))


def cycle(cal: pd.DatetimeIndex) -> tuple[pd.Series, pd.Series]:
    ex = vm.expiries(cal, "fri3")
    k = pd.Series(vm.days_to(cal, ex), index=cal)
    pos = np.array([cal.get_loc(e) for e in ex])
    i = np.arange(len(cal))
    j = np.searchsorted(pos, i, side="right") - 1
    a = pd.Series(np.where(j >= 0, i - pos[np.maximum(j, 0)], -1), index=cal)
    return k, a


def event_days() -> set:
    c = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    return set(pd.to_datetime(c[c.event.isin(EVENTS)].date).dt.normalize())


# ---------------- işlemler ----------------
def k1_table(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [570, 900, 960], step)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    rows = []
    for i in range(len(days) - 1):
        a, c = days[i], days[i + 1]
        pc, p60, s, po = dp.loc[a, "o960"], dp.loc[a, "o900"], dp.loc[a, "s960"], dp.loc[a, "o570"]
        k1 = bool((pc / tw.get(a, np.nan) - 1) <= -0.005 and pc < p60)
        sess = pc / po - 1 if np.isfinite(po) else np.nan
        night = (dp.loc[c, "o960"] / (pc + s) - 1) * 1e4 - FIN * (c - a).days
        es = np.nan
        if np.isfinite(dp.loc[c, "o570"]):
            es = (dp.loc[c, "o960"] / (dp.loc[c, "o570"] + dp.loc[c, "s570"]) - 1) * 1e4
        # XP: ilk yükselen 16:00 kapanışı (en geç 5 gün)
        xp, prev, hold = np.nan, pc, 0
        for j in range(i + 1, min(i + 6, len(days))):
            pj = dp.loc[days[j], "o960"]
            hold = j - i
            if not np.isfinite(pj):
                break
            if pj > prev or j == min(i + 5, len(days) - 1):
                xp = (pj / (pc + s) - 1) * 1e4 - FIN * (days[j] - a).days
                break
            prev = pj
        rows.append({"d": pd.Timestamp(a), "K1": k1, "sess": sess, "gece": night, "es": es, "xp": xp, "xp_gun": hold})
    t = pd.DataFrame(rows)
    t["K1_dun"] = t.K1.shift(1).fillna(False).astype(bool)
    t["sess_dun"] = t.sess.shift(1)
    return t


def c3b_book() -> pd.DataFrame:
    t = pd.read_parquet(ROOT / "research/ndx_10y_1m_20261116/results/a_trades.parquet")
    t = t[t.rule == "C3B"].copy()
    t["d"] = pd.to_datetime(t.d)
    return t[["d", "net_bp"]].rename(columns={"net_bp": "net"}).reset_index(drop=True)


def ksg_trades(b: pd.DataFrame) -> pd.DataFrame:
    t = KD.ksg_m30(b).rename(columns={"net_bp": "net"})
    t["d"] = pd.to_datetime(t.d)
    return t[["d", "net"]]


# ---------------- ölçüler ----------------
def metrics(d: pd.Series, net: np.ndarray, w: np.ndarray) -> dict:
    m = w > 0
    v = net[m] * w[m]
    if m.sum() == 0:
        return {"n": 0}
    dd = pd.Series(v, index=pd.to_datetime(d[m].values)).sort_index()
    eq = dd.cumsum()
    mdd = float((eq - eq.cummax()).min())
    yr = dd.groupby(dd.index.year).sum()
    years = max((dd.index.max() - dd.index.min()).days / 365.25, 0.5)
    q10 = np.quantile(v, 0.10)
    return {"islem": int(m.sum()), "yilda": round(float(m.sum() / years), 1), "isabet_%": round(float((v > 0).mean() * 100), 1),
            "ort_bp": round(float(v.mean()), 1), "medyan_bp": round(float(np.median(v)), 1), "toplam_bp": round(float(v.sum()), 0),
            "en_kotu_bp": round(float(v.min()), 1), "en_kotu_%10_ort_bp": round(float(v[v <= q10].mean()), 1),
            "en_iyi_bp": round(float(v.max()), 1), "maks_dusus_bp": round(mdd, 0), "en_kotu_yil_bp": round(float(yr.min()), 0),
            "islem_basi_kalite": round(float(v.mean() / v.std()), 3), "arti_yil": f"{int((yr > 0).sum())}/{len(yr)}", "yil_sharpe": round(float(yr.mean() / yr.std()), 2) if len(yr) > 2 else None}


def gate_p(net: np.ndarray, removed: np.ndarray, seed: int = 0) -> float:
    """Veto için: vetolanan işlemlerin ortalaması kalanlardan küçük mü (bootstrap P)."""
    a, b = net[removed], net[~removed]
    if len(a) < 5:
        return float("nan")
    r = np.random.default_rng(seed)
    return float((r.choice(a, (5000, len(a))).mean(1) < r.choice(b, (5000, len(b))).mean(1)).mean())


# ---------------- testler ----------------
def unit_tests() -> dict:
    cal = trading_calendar()
    k, a = cycle(cal)
    ex = set(vm.expiries(cal, "fri3"))
    checks = {
        "OPEX_2026_11_20": pd.Timestamp("2026-11-20") in ex,
        "OPEX_2025_12_19": pd.Timestamp("2025-12-19") in ex,
        "OPEX_2024_03_15": pd.Timestamp("2024-03-15") in ex,
        "OPEX_IyiCuma_2022_04_14": pd.Timestamp("2022-04-14") in ex and pd.Timestamp("2022-04-15") not in ex,
        "k_2026_11_18_eq_2": int(k.get(pd.Timestamp("2026-11-18"), -1)) == 2,
        "k_2026_11_19_eq_1": int(k.get(pd.Timestamp("2026-11-19"), -1)) == 1,
        "k_2026_11_20_eq_0": int(k.get(pd.Timestamp("2026-11-20"), -1)) == 0,
        "a_2025_12_24_eq_3": int(a.get(pd.Timestamp("2025-12-24"), -1)) == 3,
        "a_2026_10_21_eq_3": int(a.get(pd.Timestamp("2026-10-21"), -1)) == 3,
        "olay_2024_09_18_FOMC": pd.Timestamp("2024-09-18") in event_days(),
    }
    # sızıntı: kapı kararları yalnız takvimden (önceden bilinir) ve dünkü veriden; kesilmiş takvimle aynı olmalı
    cut = pd.Timestamp("2023-06-30")
    k2, a2 = cycle(cal[cal <= pd.Timestamp("2023-07-31")])
    same = (k2[k2.index <= cut - pd.Timedelta(days=40)] == k[k2.index[k2.index <= cut - pd.Timedelta(days=40)]]).all()
    checks["sizinti_takvim_kesme_ayni"] = bool(same)
    return {"gecti": all(checks.values()), "kontroller": checks}


def run_feed(nm: str, b: pd.DataFrame, step: int, k: pd.Series, a: pd.Series, ev: set) -> dict:
    t = k1_table(b, step)
    t["k"] = k.reindex(t.d).values
    t["a"] = a.reindex(t.d).values
    t["olay"] = t.d.isin(ev)
    kk = t[t.K1].reset_index(drop=True)
    veto = np.isin(kk.k.values, [0, 1, 2])
    dose_after = np.isin(kk.a.values, range(3, 8))
    ard = (kk.K1_dun | (kk.sess_dun <= -0.01)).values
    olay = kk.olay.values
    one = np.ones(len(kk))
    out = {"K1_taban": metrics(kk.d, kk.gece.values, one)}
    out["G1_ertesi_seans"] = metrics(kk.d, kk.es.values, np.isfinite(kk.es.values).astype(float))
    out["G2_ardisik_doz"] = metrics(kk.d, kk.gece.values, np.where(ard, 1.5, 1.0))
    out["G2_ardisik_ic_ort"] = round(float(kk.gece[ard].mean()), 1)
    out["G2_ardisik_dis_ort"] = round(float(kk.gece[~ard].mean()), 1)
    w3 = np.where(olay & (kk.d <= CAL_END).values, 0.0, 1.0)
    out["G3_olay_vetosu"] = metrics(kk.d, kk.gece.values, w3)
    out["G3_vetolanan_ort"] = round(float(kk.gece[(w3 == 0)].mean()), 1) if (w3 == 0).any() else None
    out["G3_P"] = round(gate_p(kk.gece.values, w3 == 0, 1), 4)
    out["G4_XP_cikis"] = metrics(kk.d, kk.xp.values, np.isfinite(kk.xp.values).astype(float))
    out["G4_ort_tutus_gun"] = round(float(kk.xp_gun.mean()), 2)
    w5 = np.where(veto, 0.0, 1.0)
    out["G5_OPEX_veto_K1"] = metrics(kk.d, kk.gece.values, w5)
    out["G5_vetolanan_ort"] = round(float(kk.gece[veto].mean()), 1)
    out["G5_P"] = round(gate_p(kk.gece.values, veto, 2), 4)
    es_ok = np.isfinite(kk.es.values)
    out["G5_OPEX_veto_ES"] = metrics(kk.d[es_ok], kk.es.values[es_ok], np.where(veto[es_ok], 0.0, 1.0))
    out["G6_vade_sonrasi_doz_K1"] = metrics(kk.d, kk.gece.values, np.where(dose_after, 1.5, 1.0) * w5)
    out["G6_doz_icinde_ort"] = round(float(kk.gece[dose_after].mean()), 1)
    w_all = w5 * w3 * np.where(ard, 1.5, 1.0) * np.where(dose_after, 1.5, 1.0)
    w_all = np.where(w_all > 0, np.minimum(w_all, 2.0), 0.0)
    out["K1_TUM_KAPILAR"] = metrics(kk.d, kk.gece.values, w_all)
    ks = ksg_trades(b)
    ks["k"] = k.reindex(ks.d).values
    kv = np.isin(ks.k.values, [0, 1, 2])
    out["KSG_taban"] = metrics(ks.d, ks.net.values, np.ones(len(ks)))
    out["G7_KSG_OPEX_veto"] = metrics(ks.d, ks.net.values, np.where(kv, 0.0, 1.0))
    out["G7_vetolanan_ort"] = round(float(ks.net[kv].mean()), 1)
    out["G7_P"] = round(gate_p(ks.net.values, kv, 3), 4)
    return out


def kos() -> None:
    RES.mkdir(exist_ok=True)
    cal = trading_calendar()
    k, a = cycle(cal)
    ev = event_days()
    out = {"birim_testleri": unit_tests()}
    print("BİRİM TESTLERİ:", out["birim_testleri"])
    out["DUKA_NDX_2018_2026"] = run_feed("DUKA", G.ndx_bars(), 60, k, a, ev)
    out["MT5_NAS100_2018_2026"] = run_feed("MT5", KD.mt5_m30("NAS100"), 1800, k, a, ev)
    c3 = c3b_book()
    c3["k"] = k.reindex(c3.d).values
    c3["a"] = a.reindex(c3.d).values
    v = np.isin(c3.k.values, [0, 1, 2])
    da = np.isin(c3.a.values, range(3, 8))
    out["C3b_DUKA"] = {"taban": metrics(c3.d, c3.net.values, np.ones(len(c3))),
                       "G5_OPEX_veto": metrics(c3.d, c3.net.values, np.where(v, 0.0, 1.0)),
                       "G5_vetolanan_ort": round(float(c3.net[v].mean()), 1), "G5_P": round(gate_p(c3.net.values, v, 4), 4),
                       "G5_G6_veto_doz": metrics(c3.d, c3.net.values, np.where(v, 0.0, np.where(da, 1.5, 1.0)))}
    (RES / "son_rapor.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for feed in ("DUKA_NDX_2018_2026", "MT5_NAS100_2018_2026"):
        print("\n=====", feed)
        for kname, val in out[feed].items():
            print(f"  {kname}: {val}")
    print("\n===== C3b_DUKA")
    for kname, val in out["C3b_DUKA"].items():
        print(f"  {kname}: {val}")


if __name__ == "__main__":
    {"test": lambda: print(unit_tests()), "kos": kos}[sys.argv[1]]()
