"""Çıkış/TP/SL geometri motoru — olay × çıkış-spec ızgarasını vektörel çözer (MT5 tarzı maliyet, lib_st konvansiyonu).

Konvansiyonlar (research/btc_scalp_20261021/strateji/lib_st.py ile birebir; prereg §2):
- Karar anı `ts_dec` (sinyal barı kapanışı) → giriş = T ≥ ts_dec olan ilk 1m barın açılışı (≤10 dk gecikme, yoksa geçersiz).
  Giriş fiyatı E = O ± h (long ask = mid + h); h = yarım spread (base 1,85 bp RT; stress 2,775; abs 15 $ RT; opt: E = sinyal
  kapanışı, h = 0, kayma 0).
- Stop tetikleri bid/ask yolunda (long: low − h ≤ seviye); dolum boşluk-duyarlı (long min(seviye, O − h)) − kayma
  (1 bp; |1m log getiri| > dondurulmuş DISC p99 = 29,30 bp olan "sıcak" dakikada 5 bp; kayma × seviye).
- TP limit: tetik long high − h ≥ TP; dolum = TP (kayma yok). **Aynı barda TP ve stop → stop** (kötümser; E57).
- Zaman çıkışı: T < end olan son barın kapanışı ∓ h. Swap: (giriş, çıkış) aralığındaki her NY 17:00 rollover'ında
  long −%14/365, short +%2/365 × E. R = net PnL / SL mesafesi; bp = net PnL / E × 1e4.
- 2023-03-24 11:28–14:00 aralığıyla kesişen işlem geçersiz; çıkışı veri sonunu aşan işlem geçersiz (lib_st gibi).
- Yola-bağlı çıkışlar: BE / kısmi / iz stopları yalnız ÖNCEKİ barlarda bilinen MFE/tepe ile aktifleşir (aktivasyon barında
  yeni stop yoktur; fam_capraz_cikis `mfe_prev` konvansiyonu). Aktivasyon barında eski stop ve TP geçerlidir.

Tasarım: aynı SL tanımını paylaşan spec'ler için ilk-dokunuş sorguları **en uzun bitişle bir kez** yapılır (binary
lifting, `data.Path1m.first`); kısa zaman stopları/yapısal bitişler "j ≤ e" karşılaştırmasıyla bedavaya çözülür.
İz stopları (trail/chandelier) matris yolu (olay partisi × pencere) ile çözülür.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

import config as K
import data as Dt

NAN = float("nan")
MAX_HOLD_MIN = 30 * 1440          # her bitiş giriş + 30 gün ile tavanlanır (seyrek tablo sınırı 45 gün)
BIG = np.iinfo(np.int64).max // 4
TYP = {"sl": 0, "tp": 1, "time": 2, "be": 3, "trail": 4}


def _isnan(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


@dataclass(frozen=True)
class ExitSpec:
    """Tek çıkış yapılandırması. R paydası daima SL mesafesi (her spec'te SL zorunlu: sunucu SL'si)."""
    sl_kind: str = "atr"        # atr | bp | orig (ailenin özgün stopu)
    sl_tf: str = "1h"           # atr için: 5m 15m 1h 4h 1d
    sl_mult: float = 1.0
    sl_bp: float = NAN          # bp için
    sl_floor_bp: float = 0.0    # atr için alt sınır (ör. scalp 19 bp)
    tp_rr: float = NAN          # TP = rr × SL (NaN = TP yok; −1 = ailenin özgün TP mesafesi tp_orig); kısmi: runner hedefi
    time_min: int = 0           # zaman stopu (dk, girişten); 0 = yalnız yapısal bitiş
    struct: str = ""            # "" | day (UTC gün sonu) | ro (sonraki rollover−2) | opp (karşı sinyal) | orig (aile bitişi)
    force_ro: bool = False      # gün-içi: her durumda sonraki rollover−2 dk'da kapat
    be_R: float = NAN           # MFE ≥ be_R × SL → stop = giriş (BE)
    trail_tf: str = ""          # iz stopu ATR'si
    trail_k: float = NAN        # stop = tepe − k × ATR(trail_tf)
    trail_act_R: float = NAN    # aktivasyon (MFE ≥ act × SL); NaN/≤0 = girişten itibaren (chandelier)
    part_frac: float = NAN      # kısmi kâr al oranı
    part_rr1: float = NAN       # kısmi TP1 = rr1 × SL
    part_be: bool = True        # TP1 sonrası runner stopu girişe

    @property
    def kind(self) -> str:
        if not _isnan(self.trail_k):
            return "trail"
        if not _isnan(self.part_frac):
            return "partial"
        if not _isnan(self.be_R):
            return "be"
        return "bracket"

    def sl_key(self) -> str:
        if self.sl_kind == "atr":
            return f"atr{self.sl_tf}x{self.sl_mult:g}" + (f"f{self.sl_floor_bp:g}" if self.sl_floor_bp else "")
        if self.sl_kind == "bp":
            return f"bp{self.sl_bp:g}"
        return "orig"

    def end_key(self) -> str:
        return f"t{self.time_min}{self.struct}{'R' if self.force_ro else ''}"

    def key(self) -> str:
        s = f"{self.sl_key()}|tp{self.tp_rr:g}|{self.end_key()}"
        if self.kind == "be":
            s += f"|be{self.be_R:g}"
        elif self.kind == "partial":
            s += f"|pt{self.part_frac:g}@{self.part_rr1:g}{'b' if self.part_be else ''}"
        elif self.kind == "trail":
            s += f"|tr{self.trail_tf}x{self.trail_k:g}a{self.trail_act_R:g}"
        return s

    def to_dict(self) -> dict:
        d = asdict(self)
        d["key"] = self.key()
        d["kind"] = self.kind
        return d

    @staticmethod
    def from_dict(d: dict) -> "ExitSpec":
        f = {k: v for k, v in d.items() if k in ExitSpec.__dataclass_fields__}
        for k in ("sl_mult", "sl_bp", "sl_floor_bp", "tp_rr", "be_R", "trail_k", "trail_act_R", "part_frac",
                  "part_rr1"):
            if k in f:
                f[k] = NAN if f[k] is None else float(f[k])
        if "time_min" in f:
            f["time_min"] = int(f["time_min"])
        return ExitSpec(**f)


# ════════════════════════════════════════════════════════════════════════════
class ExitEngine:
    """events: DataFrame[ts_dec, dir, price_dec, atr_5m…atr_1d, (sl_orig, end_orig, end_opp)]."""

    def __init__(self, data: str = "main") -> None:
        self.data = data
        self.P = Dt.path(data)          # 'indep' holdout kilidine tabi
        self.RO = self.P.RO
        self.hot = self.P.hot

    # ------------------------------------------------------------------ olay hazırlığı
    def prepare(self, ev: pd.DataFrame, mode: str = "base") -> dict:
        P = self.P
        ts = ev["ts_dec"].to_numpy(np.int64)
        d = ev["dir"].to_numpy(np.int64)
        k = P.row_at_or_after(ts)
        kc = np.minimum(k, P.N - 1)
        ok = (k < P.N) & ((P.T[kc] - ts) <= K.MAX_DELAY) & np.isin(d, (1, -1))
        O0 = P.O[kc]
        if mode == "opt":
            h = np.zeros(len(ts))
            E = ev["price_dec"].to_numpy(float)
            ok &= np.isfinite(E)
        else:
            if mode == "abs":
                h = np.full(len(ts), K.SPREAD_ABS / 2.0)
            else:
                h = O0 * K.SPREAD[mode] / 2.0
            E = O0 + d * h
        nro = self.RO[np.searchsorted(self.RO, ts, side="right")]
        return dict(ts=ts, d=d, k=kc, ok=ok, h=h, E=E, O0=O0, nro=nro, n=len(ts), mode=mode)

    def sl_dist(self, ev: pd.DataFrame, pr: dict, s: ExitSpec) -> np.ndarray:
        if s.sl_kind == "atr":
            a = s.sl_mult * ev[f"atr_{s.sl_tf}"].to_numpy(float)
            if s.sl_floor_bp:
                a = np.maximum(a, s.sl_floor_bp * 1e-4 * pr["O0"])
            return a
        if s.sl_kind == "bp":
            return np.full(pr["n"], s.sl_bp * 1e-4) * pr["O0"]
        return ev["sl_orig"].to_numpy(float)

    def end_time(self, ev: pd.DataFrame, pr: dict, s: ExitSpec) -> np.ndarray:
        ts = pr["ts"]
        end = np.full(pr["n"], BIG, np.int64)
        if s.time_min > 0:
            end = np.minimum(end, ts + s.time_min)
        if s.struct == "day":
            end = np.minimum(end, (ts // 1440 + 1) * 1440)
        elif s.struct == "ro":
            end = np.minimum(end, pr["nro"] - 2)
        elif s.struct == "opp":
            end = np.minimum(end, np.nan_to_num(ev["end_opp"].to_numpy(float), nan=BIG).astype(np.int64))
        elif s.struct == "orig":
            end = np.minimum(end, np.nan_to_num(ev["end_orig"].to_numpy(float), nan=BIG).astype(np.int64))
        if s.force_ro:
            end = np.minimum(end, pr["nro"] - 2)
        if s.time_min <= 0 and s.struct == "":
            raise ValueError(f"spec bitişsiz: {s.key()}")
        return np.minimum(end, ts + MAX_HOLD_MIN)

    # ------------------------------------------------------------------ yardımcılar
    def _first_dir(self, k, e, lev, d, h, kind: str) -> np.ndarray:
        """kind: 'adverse' (stop: long low−h ≤ lev) | 'favor' (TP/aktivasyon: long high−h ≥ lev)."""
        out = np.full(len(k), BIG, np.int64)
        for sg in (1, -1):
            s = d == sg
            if not s.any():
                continue
            if kind == "adverse":
                thr = lev[s] + h[s] if sg == 1 else lev[s] - h[s]
                out[s] = self.P.first(k[s], e[s], thr, below=(sg == 1))
            else:
                thr = lev[s] + h[s] if sg == 1 else lev[s] - h[s]
                out[s] = self.P.first(k[s], e[s], thr, below=(sg == -1))
        return out

    def _stop_fill(self, j, lev, d, h, slip: bool) -> np.ndarray:
        P = self.P
        jj = np.clip(j, 0, P.N - 1)
        gap = np.where(d == 1, np.minimum(lev, P.O[jj] - h), np.maximum(lev, P.O[jj] + h))
        if slip:
            sp = np.where(self.hot[jj], K.SLIP_HOT_BP, K.SLIP_BP) * 1e-4 * lev
            gap = gap - d * sp
        return gap

    def _finish(self, out, col, idx, pr, d, E, X, jx_time, is_time, sl_d, nights_extra=None, swap_override=None):
        P = self.P
        k = pr["k"][idx]
        ext = np.where(is_time, P.T[np.clip(jx_time, 0, P.N - 1)] + 1.0,
                       P.T[np.clip(jx_time, 0, P.N - 1)] + 0.5)
        et = P.T[k]
        if swap_override is None:
            nights = np.searchsorted(self.RO, ext, "left") - np.searchsorted(self.RO, et, "right")
            swap = nights * np.where(d == 1, K.SWAP_LONG, K.SWAP_SHORT) * E
        else:
            swap = swap_override
        pnl = d * (X - E) + swap
        bad = np.zeros(len(idx), bool)
        if P.excl is not None:
            bad = (et < P.excl[1]) & (ext > P.excl[0])
        R = pnl / sl_d
        R[bad] = np.nan
        out["R"][idx, col] = R
        out["bp"][idx, col] = np.where(bad, np.nan, pnl / E * 1e4)
        out["ext"][idx, col] = np.where(bad, np.nan, ext)
        return ext

    # ------------------------------------------------------------------ ana giriş
    def run(self, ev: pd.DataFrame, specs: list[ExitSpec], mode: str = "base", slip: bool | None = None) -> dict:
        """Dönüş: R, bp, ext (çıkış epoch dk, float), typ (int8), same (aynı-bar TP+stop), sl_d — hepsi (n × m)."""
        if slip is None:
            slip = mode != "opt"
        pr = self.prepare(ev, mode)
        n, m = pr["n"], len(specs)
        out = {"R": np.full((n, m), np.nan, np.float64), "bp": np.full((n, m), np.nan, np.float64),
               "ext": np.full((n, m), np.nan, np.float64), "typ": np.full((n, m), -1, np.int8),
               "same": np.zeros((n, m), bool), "sl_d": np.full((n, m), np.nan, np.float64)}
        groups: dict[str, list[int]] = {}
        for j, s in enumerate(specs):
            if s.kind == "trail":
                self._run_trail(ev, pr, s, j, out, slip)
            else:
                groups.setdefault(s.sl_key(), []).append(j)
        for _, cols in groups.items():
            self._run_group(ev, pr, [specs[c] for c in cols], cols, out, slip)
        return out

    # ------------------------------------------------------------------ bracket / BE / kısmi (aynı SL grubu)
    def _run_group(self, ev, pr, gspecs, cols, out, slip):
        P = self.P
        sl_all = self.sl_dist(ev, pr, gspecs[0])
        ends = np.stack([self.end_time(ev, pr, s) for s in gspecs], axis=1)  # n × g
        endmax = ends.max(axis=1)
        okg = pr["ok"] & np.isfinite(sl_all) & (sl_all > 0)
        e_max = P.last_row_before(endmax)
        okg &= e_max >= pr["k"]
        idx = np.where(okg)[0]
        if len(idx) == 0:
            return
        k, d, h, E = pr["k"][idx], pr["d"][idx], pr["h"][idx], pr["E"][idx]
        sl = sl_all[idx]
        em = e_max[idx]
        SL0 = E - d * sl
        jsl = self._first_dir(k, em, SL0, d, h, "adverse")
        cache_tp: dict[float, np.ndarray] = {}

        rr_orig = (ev["tp_orig"].to_numpy(float)[idx] / sl) if "tp_orig" in ev.columns else np.full(len(idx), NAN)

        def rr_arr(rr):
            return rr_orig if rr == -1 else rr

        def jtp_of(rr):
            if rr not in cache_tp:
                lev = E + d * rr_arr(rr) * sl
                j = self._first_dir(k, em, np.where(np.isfinite(lev), lev, np.inf * d), d, h, "favor")
                cache_tp[rr] = np.where(np.isfinite(lev), j, BIG)
            return cache_tp[rr]

        cache_be: dict = {}
        for gi, (s, col) in enumerate(zip(gspecs, cols)):
            end = ends[idx, gi]
            e1 = P.last_row_before(end)
            valid = (e1 >= k) & ~(end > P.T[-1] + 1)
            vi = np.where(valid)[0]
            if len(vi) == 0:
                continue
            ii = idx[vi]
            out["sl_d"][ii, col] = sl[vi]
            kv, dv, hv, Ev, slv, e1v, jslv = k[vi], d[vi], h[vi], E[vi], sl[vi], e1[vi], jsl[vi]
            SL0v = SL0[vi]
            hsl = jslv <= e1v
            tp = s.tp_rr
            if s.kind in ("bracket", "be"):
                jtp = jtp_of(tp)[vi] if not _isnan(tp) else np.full(len(vi), BIG, np.int64)
                htp = jtp <= e1v
            if s.kind == "bracket":
                slf = hsl & (~htp | (jslv <= jtp))
                tpf = htp & ~slf
                tim = ~slf & ~tpf
                X = np.empty(len(vi))
                X[slf] = self._stop_fill(jslv[slf], SL0v[slf], dv[slf], hv[slf], slip)
                TPv = Ev + dv * (rr_arr(tp)[vi] if tp == -1 else tp) * slv if not _isnan(tp) else Ev
                X[tpf] = TPv[tpf]
                X[tim] = P.C[e1v[tim]] - dv[tim] * hv[tim]
                jx = np.where(slf, jslv, np.where(tpf, jtp, e1v))
                self._finish(out, col, ii, pr, dv, Ev, X, jx, tim, slv)
                out["typ"][ii, col] = np.where(slf, 0, np.where(tpf, 1, 2))
                out["same"][ii, col] = hsl & htp & (jslv == jtp)
            elif s.kind == "be":
                bkey = ("be", s.be_R)
                if bkey not in cache_be:
                    act_lev = E + d * s.be_R * sl
                    jact = self._first_dir(k, em, act_lev, d, h, "favor")
                    st = np.minimum(jact + 1, em + 1)
                    jbe = self._first_dir(st, em, E, d, h, "adverse")
                    jbe = np.where(jact + 1 <= em, jbe, BIG)
                    cache_be[bkey] = (jact, jbe)
                jact, jbe = cache_be[bkey]
                jact, jbe = jact[vi], jbe[vi]
                hact = jact <= e1v
                c_sl = hsl & (jslv <= jtp) & (jslv <= jact)
                c_tp = ~c_sl & htp & (jtp <= jact)
                c_act = ~c_sl & ~c_tp & hact
                hbe = c_act & (jbe <= e1v)
                c_be = hbe & (jbe <= jtp)
                c_tp2 = c_act & ~c_be & htp
                tpf = c_tp | c_tp2
                tim = ~c_sl & ~tpf & ~c_be
                X = np.empty(len(vi))
                X[c_sl] = self._stop_fill(jslv[c_sl], SL0v[c_sl], dv[c_sl], hv[c_sl], slip)
                X[c_be] = self._stop_fill(jbe[c_be], Ev[c_be], dv[c_be], hv[c_be], slip)
                TPv = Ev + dv * (rr_arr(tp)[vi] if tp == -1 else tp) * slv if not _isnan(tp) else Ev
                X[tpf] = TPv[tpf]
                X[tim] = P.C[e1v[tim]] - dv[tim] * hv[tim]
                jx = np.where(c_sl, jslv, np.where(c_be, jbe, np.where(tpf, jtp, e1v)))
                self._finish(out, col, ii, pr, dv, Ev, X, jx, tim, slv)
                out["typ"][ii, col] = np.where(c_sl, 0, np.where(c_be, 3, np.where(tpf, 1, 2)))
                out["same"][ii, col] = (hsl & htp & (jslv == jtp)) | (c_act & hbe & (jbe == jtp))
            else:  # partial
                f, r1, r2 = s.part_frac, s.part_rr1, s.tp_rr
                jt1 = jtp_of(r1)[vi]
                ht1 = jt1 <= e1v
                c_sl = hsl & (jslv <= jt1)
                c_p = ~c_sl & ht1
                tim_full = ~c_sl & ~c_p
                pkey = ("pt", r1, s.part_be)
                if pkey not in cache_be:
                    jt1f = jtp_of(r1)
                    st = np.minimum(jt1f + 1, em + 1)
                    if s.part_be:
                        jr = self._first_dir(st, em, E, d, h, "adverse")
                        jr = np.where(jt1f + 1 <= em, jr, BIG)
                    else:
                        jr = jsl  # SL0 zaten t1'den sonra (c_p dalında)
                    cache_be[pkey] = jr
                jr = cache_be[pkey][vi]
                tkey = ("pt2", r1, r2)
                if _isnan(r2):
                    jt2 = np.full(len(vi), BIG, np.int64)
                else:
                    if tkey not in cache_be:
                        jt1f = jtp_of(r1)
                        st = np.minimum(jt1f, em + 1)
                        lev2 = E + d * r2 * sl
                        cache_be[tkey] = np.where(jt1f <= em, self._first_dir(st, em, lev2, d, h, "favor"), BIG)
                    jt2 = cache_be[tkey][vi]
                rlev = Ev if s.part_be else SL0v
                r_stop = c_p & (jr <= e1v) & (jr <= jt2)
                r_tp = c_p & ~r_stop & (jt2 <= e1v)
                r_tim = c_p & ~r_stop & ~r_tp
                Xr = np.full(len(vi), np.nan)
                Xr[r_stop] = self._stop_fill(jr[r_stop], rlev[r_stop], dv[r_stop], hv[r_stop], slip)
                if not _isnan(r2):
                    Xr[r_tp] = (Ev + dv * r2 * slv)[r_tp]
                Xr[r_tim] = P.C[e1v[r_tim]] - dv[r_tim] * hv[r_tim]
                X1 = Ev + dv * r1 * slv
                # tam pozisyon dalları
                Xf = np.full(len(vi), np.nan)
                Xf[c_sl] = self._stop_fill(jslv[c_sl], SL0v[c_sl], dv[c_sl], hv[c_sl], slip)
                Xf[tim_full] = P.C[e1v[tim_full]] - dv[tim_full] * hv[tim_full]
                X = np.where(c_p, f * X1 + (1 - f) * Xr, Xf)
                jx = np.where(c_sl, jslv, np.where(r_stop, jr, np.where(r_tp, jt2, e1v)))
                is_time = tim_full | r_tim
                # swap: kısmi bacak t1'de, kalan son çıkışta
                Tn = P.T
                ext = np.where(is_time, Tn[np.clip(jx, 0, P.N - 1)] + 1.0, Tn[np.clip(jx, 0, P.N - 1)] + 0.5)
                et = Tn[kv]
                rate = np.where(dv == 1, K.SWAP_LONG, K.SWAP_SHORT) * Ev
                n_all = np.searchsorted(self.RO, ext, "left") - np.searchsorted(self.RO, et, "right")
                ext1 = Tn[np.clip(jt1, 0, P.N - 1)] + 0.5
                n1 = np.searchsorted(self.RO, ext1, "left") - np.searchsorted(self.RO, et, "right")
                swap = np.where(c_p, rate * (f * n1 + (1 - f) * n_all), rate * n_all)
                self._finish(out, col, ii, pr, dv, Ev, X, jx, is_time, slv, swap_override=swap)
                out["typ"][ii, col] = np.where(c_sl, 0, np.where(r_stop, 3, np.where(r_tp, 1, 2)))
                out["same"][ii, col] = hsl & ht1 & (jslv == jt1)

    # ------------------------------------------------------------------ iz stopu (matris)
    def _run_trail(self, ev, pr, s: ExitSpec, col, out, slip, cells: int = 3_000_000):
        P = self.P
        sl_all = self.sl_dist(ev, pr, s)
        end = self.end_time(ev, pr, s)
        e1 = P.last_row_before(end)
        A_all = s.trail_k * ev[f"atr_{s.trail_tf}"].to_numpy(float)
        ok = pr["ok"] & np.isfinite(sl_all) & (sl_all > 0) & np.isfinite(A_all) & (e1 >= pr["k"]) \
            & ~(end > P.T[-1] + 1)
        idx = np.where(ok)[0]
        if len(idx) == 0:
            return
        act = s.trail_act_R
        always = _isnan(act) or act <= 0
        L_all = (e1 - pr["k"] + 1)
        order = idx[np.argsort(L_all[idx])]
        pos = 0
        while pos < len(order):
            B = max(1, cells // max(int(L_all[order[pos]]), 1))
            while True:  # sıralı: partinin W'si son elemanınki; B×W ≤ cells olana dek küçült
                bi = order[pos:pos + B]
                W = int(L_all[bi[-1]])
                if B == 1 or len(bi) * W <= cells:
                    break
                B = max(1, cells // W)
            pos += len(bi)
            k, d, h, E = pr["k"][bi], pr["d"][bi], pr["h"][bi], pr["E"][bi]
            sl, A, ee = sl_all[bi], A_all[bi], e1[bi]
            ar = np.arange(W)
            rows = k[:, None] + ar[None, :]
            msk = rows <= ee[:, None]
            rows = np.minimum(rows, P.N - 1)
            dd = d[:, None]
            hh = h[:, None]
            fav = np.where(dd == 1, P.H[rows] - hh, -(P.L[rows] + hh))      # lehte uç (işaretli)
            adv = np.where(dd == 1, P.L[rows] - hh, -(P.H[rows] + hh))      # aleyhte uç (işaretli)
            fav = np.where(msk, fav, -np.inf)
            p0 = np.where(d == 1, P.O[k] - h, -(P.O[k] + h))[:, None]
            cm = np.maximum.accumulate(fav, axis=1)
            peak_prev = np.concatenate([p0, np.maximum(p0, cm[:, :-1])], axis=1)
            Es = (d * E)[:, None]
            sl0s = Es - sl[:, None]                                          # işaretli SL0
            trailed = peak_prev - A[:, None]
            if always:
                actv = np.ones_like(msk)
            else:
                actv = (peak_prev - Es) >= act * sl[:, None]
            stop = np.where(actv, np.maximum(sl0s, trailed), sl0s)
            hit_s = msk & (adv <= stop)
            js = np.where(hit_s.any(1), hit_s.argmax(1), BIG)
            if not _isnan(s.tp_rr):
                tps = Es + s.tp_rr * sl[:, None]
                hit_t = msk & (fav >= tps)
                jt = np.where(hit_t.any(1), hit_t.argmax(1), BIG)
            else:
                jt = np.full(len(bi), BIG)
            sf = js <= jt
            sf &= js < BIG
            tf = ~sf & (jt < BIG)
            tm = ~sf & ~tf
            r_ = np.arange(len(bi))
            jsc = np.minimum(js, W - 1)
            lev_s = d * stop[r_, jsc]                                       # fiyat seviyesi
            jabs = k + jsc
            X = np.empty(len(bi))
            X[sf] = self._stop_fill(jabs[sf], lev_s[sf], d[sf], h[sf], slip)
            if not _isnan(s.tp_rr):
                X[tf] = (E + d * s.tp_rr * sl)[tf]
            X[tm] = P.C[ee[tm]] - d[tm] * h[tm]
            jx = np.where(sf, jabs, np.where(tf, k + np.minimum(jt, W - 1), ee))
            self._finish(out, col, bi, pr, d, E, X, jx, tm, sl)
            trailed_hit = sf & (np.abs(lev_s - (E - d * sl)) > 1e-9)
            out["typ"][bi, col] = np.where(sf, np.where(trailed_hit, 4, 0), np.where(tf, 1, 2))
            out["same"][bi, col] = sf & (jt == js)
            out["sl_d"][bi, col] = sl


def simulate_frame(ev: pd.DataFrame, specs: list[ExitSpec], data: str = "main", mode: str = "base",
                   engine: ExitEngine | None = None) -> dict:
    eng = engine or ExitEngine(data)
    return eng.run(ev, specs, mode=mode)
