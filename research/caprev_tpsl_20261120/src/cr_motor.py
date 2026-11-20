"""motor.py — CAPREV (canlı kural, dondurulmuş) her beslemede + S/H/T hücreleri + E özellikleri (PROTOCOL.md).

İşlem başına satır: taban (stop 1,0, D0 kapanışı) + her hücrenin net bp'si (sabit lot, spread + finansman) + özellikler.
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
for p in ("research/ksg_tpsl_20261119/src", "research/ndx_10y_1m_20261116/src", "yeni deneme"):
    sys.path.insert(0, str(ROOT / p))
import lib  # noqa: E402

FIN = lib.FIN_BP_PER_DAY
STRESS_R1, STRESS_R5, VIX_MIN = -0.015, -0.04, 18.4
S_K = (0.5, 0.75, 1.5, 2.0, None)            # None = stopsuz (acil %7)
EMERG = 0.07
T_K = (0.5, 1.0, 2.0)
MAX_HOLD = 5
KESIF_SON = date(2021, 10, 31)
VIX_PATH = ROOT / "research/qs03_akis_takvim_20261111/data/VIX.parquet"

PROF = {
    "NDX": {"tz": "America/New_York", "dip": 540, "close": 960, "need_from": 570, "win": (180, 900), "open": 570, "last_h": 900},
    "DAX": {"tz": "Europe/Berlin", "dip": 540, "close": 1080, "need_from": 540, "win": (480, 990), "open": 540, "last_h": 1020},
}
MARKET = {"DUKA_DAX": "DAX", "MT5_GER40": "DAX"}


def vix_close() -> pd.Series:
    v = pd.read_parquet(VIX_PATH)
    s = v["Close"].squeeze() if "Close" in v else v.iloc[:, 3]
    s.index = pd.to_datetime(s.index).tz_localize(None).date
    return s.dropna()


VIX = vix_close()
_VD, _VV = np.array(list(VIX.index)), VIX.values


def vix_prev(d: date) -> float | None:
    k = int(np.searchsorted(_VD, d)) - 1
    return float(_VV[k]) if k >= 0 else None


def vix_prev2(d: date) -> float | None:
    k = int(np.searchsorted(_VD, d)) - 2
    return float(_VV[k]) if k >= 0 else None


# ───────────────────────── besleme ─────────────────────────
def load(name: str) -> tuple[pd.DataFrame, int]:
    if name == "DUKA_DAX":
        d = pd.read_parquet(ROOT / "research/fibo_altin_bolge_20261116/cache/DAX_1m_raw.parquet").sort_values("t").drop_duplicates("t")
        return pd.DataFrame({"t": d.t.values.astype(np.int64), "o": d.open.values, "h": d.high.values, "l": d.low.values,
                             "c": d.close.values, "sp": np.full(len(d), 1.0)}), 60
    if name == "MT5_GER40":
        d = pd.read_csv(ROOT / "research/c1_turev_20261105/data/mt5/GER40_M30.csv.gz")
        d = d[d.t >= pd.Timestamp("2016-01-01", tz="UTC").timestamp()].sort_values("t").drop_duplicates("t")
        return pd.DataFrame({"t": d.t.values.astype(np.int64), "o": d.o.values, "h": d.h.values, "l": d.l.values,
                             "c": d.c.values, "sp": np.full(len(d), 1.0)}), 1800
    if name == "MT5_LONG1H":
        d = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_1h_utc.parquet")
        t = (d.ts.astype("int64") // 10 ** 9).values
        return pd.DataFrame({"t": t, "o": d.open.values, "h": d.high.values, "l": d.low.values, "c": d.close.values,
                             "sp": np.full(len(d), 1.0)}), 3600
    import motor as K                                  # KSG besleme katmanı (Duka NDX, MT5, EET30, NQ, U1 M30)
    return K.load(name)


class Feed:
    def __init__(self, name: str):
        b, st = load(name)
        self.name, self.step = name, st
        self.mk = MARKET.get(name, "NDX")
        self.P = PROF[self.mk]
        self.t = b.t.values.astype(np.int64)
        self.o, self.h, self.l, self.c, self.sp = (b[x].values.astype(float) for x in ("o", "h", "l", "c", "sp"))
        loc = pd.to_datetime(self.t, unit="s", utc=True).tz_convert(self.P["tz"])
        self.d = np.array(loc.date)
        self.m = (loc.hour * 60 + loc.minute).values.astype(np.int32)
        self.tol = max(self.step, 300)
        self.D = self._daily()

    # zaman
    def u(self, d: date, minute: int) -> int:
        return int(pd.Timestamp(datetime(d.year, d.month, d.day, minute // 60, minute % 60), tz=self.P["tz"]).timestamp())

    def px_at(self, uu: int) -> tuple[int, float] | None:
        """uu'da açılan mumun açılışı (bid); yoksa uu'dan önce biten son mumun kapanışı (≤ 15 dk)."""
        i = int(np.searchsorted(self.t, uu))
        if i < len(self.t) and self.t[i] - uu <= self.tol:
            return i, self.o[i]
        j = i - 1
        if j >= 0 and uu - (self.t[j] + self.step) <= 900:
            return i, self.c[j]
        return None

    def _daily(self) -> pd.DataFrame:
        P = self.P
        df = pd.DataFrame({"d": self.d, "m": self.m, "o": self.o, "l": self.l, "c": self.c})
        end = df.m + self.step // 60
        rth = df[(df.m >= P["dip"]) & (end <= P["close"])]
        need = rth[rth.m >= P["need_from"]].groupby("d").size()
        exp = (P["close"] - P["need_from"]) / (self.step / 60)
        low = rth.groupby("d").l.min()
        last = rth[end.loc[rth.index] == P["close"]].groupby("d").c.last()
        oh = df[df.m == P["last_h"]].groupby("d").o.first()
        D = pd.DataFrame({"low": low, "n": need, "close": last, "o_last_h": oh})
        D = D[D.n >= 0.8 * exp].dropna(subset=["close"])
        D.index = pd.Index(list(D.index))
        D = D[[x.weekday() < 5 for x in D.index]]
        if self.mk == "NDX":
            D["early"] = [lib.nyse.is_early_close(x) for x in D.index]
            D = D[~D.early]
        return D

    # ───────── işlemler ─────────
    def events(self) -> list[dict]:
        D, P = self.D, self.P
        days = list(D.index)
        cl = D.close.values
        out = []
        for k in range(22, len(days)):
            d = days[k]
            if d.weekday() > 3 or (d - days[k - 1]).days > 4:
                continue
            c = cl[:k]
            rets = c[1:] / c[:-1] - 1
            r1, r5, dvol = rets[-1], c[-1] / c[-6] - 1, float(np.std(rets[-20:], ddof=1))
            v = vix_prev(d)
            if v is None or v < VIX_MIN or not (r1 <= STRESS_R1 or r5 <= STRESS_R5):
                continue
            pdl = D.low.iloc[k - 1]
            trig = None
            for h0 in range(P["win"][0], P["win"][1], 60):
                if h0 + 60 > P["win"][1]:
                    break
                a, b = np.searchsorted(self.t, self.u(d, h0)), np.searchsorted(self.t, self.u(d, h0 + 60))
                if b - a < max(1, 1800 // self.step) or (b - a) * self.step < 1800:
                    continue
                if self.c[b - 1] < pdl:
                    trig = (h0, self.c[b - 1], self.u(d, h0 + 60))
                    break
            if trig is None:
                continue
            got = self.px_at(trig[2])                 # tetik bitişinde açılan mum; yoksa ≤15 dk önceki kapanış (veri boşluğu)
            if got is None or got[0] >= len(self.t):
                continue
            i0 = got[0]
            ask = got[1] + self.sp[min(i0, len(self.t) - 1)]
            prev = D.iloc[k - 1]
            hi20 = cl[max(0, k - 20):k].max()
            out.append({"d": d, "k": k, "i0": i0, "E": ask, "dvol": dvol, "r1": r1, "r5": r5, "vix": v,
                        "vix_chg": (v / vix_prev2(d) - 1) if vix_prev2(d) else np.nan, "trig_h": trig[0],
                        "pre_open": trig[0] + 60 <= P["open"], "depth": (pdl - trig[1]) / (ask * dvol),
                        "from_close": (ask / c[-1] - 1) / dvol, "from_hi20": (ask / hi20 - 1) / dvol,
                        "last_hour": (prev.close / prev.o_last_h - 1) if np.isfinite(prev.o_last_h) else np.nan,
                        "wd": d.weekday(), "opex": _opex(d)})
        return out

    def checkpoints(self, ev: dict) -> list[tuple[str, int, date]]:
        days = list(self.D.index)
        k = ev["k"]
        cps = [("D0c", self.u(days[k], self.P["close"]), days[k])]
        for j in range(1, MAX_HOLD + 1):
            if k + j >= len(days) or (days[k + j] - days[k + j - 1]).days > 5:
                break
            cps.append((f"D{j}o", self.u(days[k + j], self.P["open"]), days[k + j]))
            cps.append((f"D{j}c", self.u(days[k + j], self.P["close"]), days[k + j]))
        return cps

    def trade_row(self, ev: dict) -> dict | None:
        cps = self.checkpoints(ev)
        if len(cps) < 3:
            return None
        i0, E, dv, d0 = ev["i0"], ev["E"], ev["dvol"], ev["d"]
        px = {}
        for lab, uu, dd in cps:
            r = self.px_at(uu)
            if r is None:                          # veri boşluğu: sonraki kontrol noktaları kesilir
                break
            px[lab] = (r[0], r[1], dd)
        if not {"D0c", "D1o", "D1c"} <= px.keys():
            return None
        cps = [c for c in cps if c[0] in px]
        iend = px[cps[-1][0]][0]
        lo, hi, op = self.l[i0:iend], self.h[i0:iend], self.o[i0:iend]

        def first(mask: np.ndarray) -> int:
            return int(np.argmax(mask)) if mask.any() else 10 ** 9

        def outcome(stop_k, tp_k, exit_lab: str) -> tuple[float, str]:
            """Sabit lot net bp: [i0, çıkış) içinde stop/TP, yoksa çıkış noktası."""
            ie, pe, de = px[exit_lab]
            n = ie - i0
            sl = E * (1 - (stop_k * dv if stop_k is not None else EMERG))
            js = first(lo[:n] <= sl)
            jt = first(hi[:n] >= E * (1 + tp_k * dv)) if tp_k is not None else 10 ** 9
            if js < 10 ** 9 and js <= jt:
                fill, why, dd = min(sl, op[js]), "stop", self.d[i0 + js]
            elif jt < 10 ** 9:
                fill, why, dd = E * (1 + tp_k * dv), "tp", self.d[i0 + jt]
            else:
                fill, why, dd = pe, "time", de
            return (fill / E - 1) * 1e4 - FIN * (dd - d0).days, why

        r = {k: ev[k] for k in ev if k not in ("k", "i0")} | {"feed": self.name}
        base, why = outcome(1.0, None, "D0c")
        r |= {"base": base, "why": why, "R": base / 1e4 / dv}
        r["cls"] = "SL" if why == "stop" else ("TP" if base > 0 else "ZK")
        for k in S_K:
            r[f"S_{k}"] = outcome(k, None, "D0c")[0]
        for k in T_K:
            r[f"T_{k}"] = outcome(1.0, k, "D0c")[0]
        d0c_bid = px["D0c"][1]
        closes = [lab for lab, _, _ in cps if lab.endswith("c")]
        xp = "D0c"
        if d0c_bid < E:
            xp = closes[-1]
            for a, b in zip(closes[:-1], closes[1:]):
                if px[b][1] > px[a][1]:
                    xp = b
                    break
        r0 = "D0c" if d0c_bid >= E else "D1c"
        for nm, stop_k in (("st", 1.0), ("ns", None)):
            r[f"H_D1o_{nm}"] = outcome(stop_k, None, "D1o")[0]
            r[f"H_D1c_{nm}"] = outcome(stop_k, None, "D1c")[0]
            r[f"H_XP_{nm}"] = outcome(stop_k, None, xp)[0]
            r[f"H_R0_{nm}"] = outcome(stop_k, None, r0)[0]
        r["mae_d0"] = (lo[:px["D0c"][0] - i0].min() / E - 1) * 1e4 if px["D0c"][0] > i0 else np.nan
        r["d0c_bp_nostop"] = (d0c_bid / E - 1) * 1e4
        r["d1c_bp_nostop"] = (px["D1c"][1] / E - 1) * 1e4 - FIN * (px["D1c"][2] - d0).days
        return r

    def table(self) -> pd.DataFrame:
        rows = [self.trade_row(e) for e in self.events()]
        T = pd.DataFrame([r for r in rows if r is not None])
        if len(T):
            T["d"] = pd.to_datetime(T.d)
        return T


def _opex(d: date) -> int | None:
    try:
        import korku_live as kl
        return kl.days_to_opex(d)
    except Exception:
        return None


S_CELLS = [f"S_{k}" for k in S_K]
H_CELLS = [f"H_{x}_{s}" for s in ("st", "ns") for x in ("D1o", "D1c", "XP", "R0")]
T_CELLS = [f"T_{k}" for k in T_K]
