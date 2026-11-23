"""veri.py — canlı NAS100 kurallarının bacak (leg) listeleri: Duka ana kitap + MT5 yarı bağımsız kontrol kitabı.

Bacak: rule, fam (korku ailesi mi), d (giriş günü), t_in, t_out (UTC epoch), side, px_in, lot0 (canlı lot), bp (net, maliyet dahil).
python veri.py → kendi kontrolünü yazdırır (kaynak n / ort bp yeniden üretimi).
"""
from __future__ import annotations

import pickle
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
R = ROOT / "research"
sys.path.insert(0, str(R / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

FAM = {"C3B", "KSG", "KORKU", "CAPREV", "ORBVIX"}
ORDER = ["C3B", "CAPREV", "ORBVIX", "CEKIC", "KSG", "AYSONU_SON", "AYSONU_E2", "KORKU"]
LOT = {"C3B": 2.0, "CAPREV": 0.2, "ORBVIX": 0.75, "CEKIC": 0.5, "KSG": 0.5, "AYSONU_SON": 1.0, "AYSONU_E2": 0.75, "KORKU": 0.75}
CAP_STOP_K, CAP_MAXC, CAP_H = 3.0, 5, 0.5          # KQ-06 E2_U0_h0.5 (canlı)
FIN = lib.FIN_BP_PER_DAY
COLS = ["rule", "d", "t_in", "t_out", "side", "px_in", "lot0", "bp", "src"]


def opex_week(d: date) -> bool:
    """c3b_live.opex_week ile aynı: ayın 3. Cuması ve önceki 4 gün."""
    first = date(d.year, d.month, 1)
    fri3 = first.toordinal() + (4 - first.weekday()) % 7 + 14
    return fri3 - 4 <= d.toordinal() <= fri3


def _a_trades() -> pd.DataFrame:
    a = pd.read_parquet(R / "ndx_10y_1m_20261116/results/a_trades.parquet")
    a["d"] = pd.to_datetime(a.d).dt.date
    return a


def _ksg(a: pd.DataFrame, feed: str) -> pd.DataFrame:
    g = pd.read_csv(R / f"ksg_opex_canli_20261119/results/ksg_geceler_{feed}.csv")
    g["d"] = pd.to_datetime(g.d).dt.date
    g = g[~g.veto.astype(bool)].copy()
    g["lot0"] = np.where(g.vix_prev >= 25.0, 1.0, 0.5)
    return g


def duka_legs() -> tuple[pd.DataFrame, dict]:
    a = _a_trades()
    chk: dict = {}
    rows = []
    for rule in ("C3B", "CEKIC", "AYSONU_SON", "AYSONU_E2"):
        t = a[a.rule == rule]
        chk[rule] = (len(t), float(t.net_bp.mean()))
        for x in t.itertuples():
            lot = LOT[rule] * (0.5 if rule == "C3B" and opex_week(x.d) else 1.0)
            rows.append((rule, x.d, int(x.t_in), int(x.t_out), int(x.side), float(x.px_in), lot, float(x.net_bp), "duka"))
    o = pd.read_parquet(R / "ndx_10y_1m_20261116/results/orb_tp3_trades.parquet")
    o["d"] = pd.to_datetime(o.d).dt.date
    chk["ORBVIX"] = (len(o), float(o.R.mean()), float(o.net_bp.mean()))
    for x in o.itertuples():
        rows.append(("ORBVIX", x.d, int(x.t_in), int(x.t_out), int(x.side), float(x.px_in), LOT["ORBVIX"], float(x.net_bp), "duka"))
    k = a[a.rule == "KSG"].set_index("d")
    g = _ksg(a, "DUKA_NDX")
    chk["KSG_kaynak"] = (len(k), float(k.net_bp.mean()))
    miss = 0
    for x in g.itertuples():
        if x.d not in k.index:
            miss += 1
            continue
        y = k.loc[x.d]
        rows.append(("KSG", x.d, int(y.t_in), int(y.t_out), 1, float(y.px_in), float(x.lot0), float(y.net_bp), "duka"))
    chk["KSG_vetosuz"] = (len(g), float(g.net.mean()), miss)
    rows += korku_rows("DUKA_NDX", chk)
    rows += caprev_rows("DUKA_NDX", a, chk)
    L = pd.DataFrame(rows, columns=COLS)
    return _finish(L), chk


def mt5_legs(duka: pd.DataFrame, m1: lib.M1) -> tuple[pd.DataFrame, dict]:
    """KORKU, KSG, CAPREV MT5'ten; diğerleri Duka'dan (aynı bacaklar)."""
    chk: dict = {}
    keep = duka[~duka.rule.isin(["KORKU", "KSG", "CAPREV"])][COLS]
    rows = korku_rows("MT5_NAS100", chk)
    g = _ksg(_a_trades(), "MT5_NAS100")
    days = lib.trading_days(m1)
    nxt = {d: days[i + 1] for i, d in enumerate(days[:-1])}
    D = lib.daily_table(m1).set_index("d")
    for x in g.itertuples():
        if x.d not in nxt or x.d not in D.index:
            continue
        rows.append(("KSG", x.d, lib.utc(x.d, 960), lib.utc(nxt[x.d], 570), 1, float(D.loc[x.d, "c1600"]), float(x.lot0), float(x.net), "mt5"))
    chk["KSG_mt5"] = (len(g), float(g.net.mean()))
    rows += caprev_rows("MT5_NAS100", _a_trades(), chk)
    L = pd.concat([keep, pd.DataFrame(rows, columns=COLS)], ignore_index=True)
    return _finish(L), chk


def korku_rows(feed: str, chk: dict) -> list[tuple]:
    t = pd.read_csv(R / f"korku_evren_20261119/results/t30_islemler_{feed}.csv")
    chk[f"KORKU_{feed}"] = (len(t), float(t.net.mean()))
    out = []
    for x in t.itertuples():
        d, c = pd.Timestamp(x.d).date(), pd.Timestamp(x.cikis).date()
        out.append(("KORKU", d, lib.utc(d, 960), lib.utc(c, 960), 1, float(x.giris), LOT["KORKU"], float(x.net), feed.lower()[:4]))
    return out


# ───────── CAPREV: KQ-06 E2_U0_h0.5 yürüyüşü (kq6_analiz._walk'un feed kolu, birebir) ─────────
def _cal_days(ev: dict, s: int) -> float:
    return ((ev["cl"][s] / ev["E"] - 1) * 1e4 - ev["res"][s]) / FIN if FIN else 0.0


def _walk(ev: dict, E: float, start: int, first_check: int, h: float) -> tuple[float, int]:
    dv, lo, op, dd, seg, cl, fac = ev["dvol"], ev["lo"], ev["op"], ev["dd"], ev["seg"], ev["cl"], ev["fac"]
    S = E * (1 - CAP_STOP_K * dv)
    n = len(cl)
    locked, w, pos = 0.0, 1.0, start
    for s in range(first_check, n):
        end = seg[s]
        seg_lo, seg_op = lo[pos:end], op[pos:end]
        hit = np.flatnonzero(seg_lo <= S)
        if hit.size:
            j = pos + int(hit[0])
            fill = min(S, seg_op[int(hit[0])]) * fac
            return locked + w * ((fill / E - 1) * 1e4 - FIN * dd[j]), s
        pos = end
        r = (cl[s] / E - 1) * 1e4 - FIN * _cal_days(ev, s)
        if cl[s] >= E or s - first_check >= CAP_MAXC or s == n - 1:
            return locked + w * r, s
        if s == first_check and h < 1.0:
            locked += (1 - h) * r
            w = h
    return locked, n - 1


def caprev_rows(feed: str, a: pd.DataFrame, chk: dict) -> list[tuple]:
    P = pickle.load(open(R / "caprev_kuyruk_20261121/cache/yollar2.pkl", "rb"))
    P = [e for e in P if e["feed"] == feed]
    tin = {x.d: int(x.t_in) for x in a[a.rule == "CAPREV"].itertuples()}
    cal = None
    out, tot = [], []
    for ev in P:
        d0 = pd.Timestamp(ev["d"]).date()
        sp = ev.get("sp_bp", 0.0) / 1e4
        c0_ask = ev["cl"][0] * (1 + sp)
        ra, sa = _walk(ev, ev["E"], 0, 0, CAP_H)
        rb, sb = _walk(ev, c0_ask, ev["seg"][0], 1, CAP_H)
        tot.append(0.5 * ra + 0.5 * rb)
        if cal is None:
            cal = _cal()
        k0 = cal.index(d0) if d0 in cal else None
        if k0 is None:
            continue
        ta = tin.get(d0, lib.utc(d0, 900))
        out.append(("CAPREV", d0, ta, lib.utc(cal[k0 + sa], 960), 1, float(ev["E"]), LOT["CAPREV"], float(ra), feed.lower()[:4]))
        out.append(("CAPREV", d0, lib.utc(d0, 960), lib.utc(cal[k0 + sb], 960), 1, float(c0_ask), LOT["CAPREV"], float(rb), feed.lower()[:4]))
    chk[f"CAPREV_{feed}"] = (len(P), float(np.mean(tot)))
    return out


_CAL: list | None = None


def _cal() -> list:
    """NYSE işlem günleri (korku_live takvimiyle aynı kaynak: son_rapor trading_calendar)."""
    global _CAL
    if _CAL is None:
        sys.path.insert(0, str(R / "son_rapor_20261118/src"))
        import rapor  # noqa: E402
        _CAL = [x.date() for x in rapor.trading_calendar()]
    return _CAL


def _finish(L: pd.DataFrame) -> pd.DataFrame:
    L["fam"] = L.rule.isin(FAM)
    L["ord"] = L.rule.map({r: i for i, r in enumerate(ORDER)})
    L["usd0"] = L.lot0 * L.px_in * L.bp / 1e4          # canlı lotta işlem $
    return L.sort_values(["t_in", "ord"]).reset_index(drop=True)


if __name__ == "__main__":
    L, c = duka_legs()
    for k, v in c.items():
        print(k, v)
    print(L.groupby("rule").agg(n=("bp", "size"), ort_bp=("bp", "mean"), usd=("usd0", "sum")))
