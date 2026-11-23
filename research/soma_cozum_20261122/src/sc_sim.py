"""SC — pozisyon simülatörü. C çekirdeği (sc_kernel.c) + aynı kuralların saf Python referansı (testler ikisini eşitler).

Kullanım:
    emir = Emir.yeni(n)                  # varsayılanlar: stop/TP/iz/başabaş yok, zaman çıkışı yok
    emir.i0[:] = bar.idx(t_karar + 60)    # dolum barı = karar anından SONRA açılan ilk bar (E7)
    sonuc = simule(bar, emir)            # DataFrame: j, giris, cikis, neden, bp_brut, bp, mfe_bp, mae_bp

Kurallar sc_kernel.c başlığında. bp = brüt (spread dahil) − komisyon. Komisyon sc_veri.KOMISYON_USD_OZ (gidiş-dönüş).
"""
from __future__ import annotations

import ctypes
import subprocess
from dataclasses import dataclass, field, fields
from pathlib import Path

import numpy as np
import pandas as pd

import sc_veri as V

SRC = Path(__file__).resolve().parent
_C, _SO = SRC / "sc_kernel.c", SRC / "sc_kernel.dylib"
NEDEN = {0: "STOP", 1: "TP", 2: "IZ", 3: "ZAMAN", 4: "SON"}
YOK = np.inf
T_YOK = np.iinfo(np.int64).max


def _derle() -> ctypes.CDLL:
    if not _SO.exists() or _SO.stat().st_mtime < _C.stat().st_mtime:
        subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", str(_SO), str(_C)], check=True)
    lib = ctypes.CDLL(str(_SO))
    lib.sc_yol.restype = None
    return lib


_LIB = _derle()


@dataclass
class Emir:
    i0: np.ndarray
    yon: np.ndarray
    sl_d: np.ndarray
    tp_d: np.ndarray
    iz_akt: np.ndarray
    iz_d: np.ndarray
    be_akt: np.ndarray
    be_off: np.ndarray
    t_cik: np.ndarray
    etiket: dict = field(default_factory=dict)  # ek kolonlar (sinyal kimliği vb.), sonuca aynen geçer

    @classmethod
    def yeni(cls, n: int) -> "Emir":
        f = lambda v, dt=float: np.full(n, v, dtype=dt)  # noqa: E731
        return cls(f(0, np.int64), f(1, np.int32), f(YOK), f(YOK), f(YOK), f(0.0), f(YOK), f(0.0), f(T_YOK, np.int64))

    def dogrula(self, bar: V.Bar) -> None:
        n = len(self.i0)
        for fl in fields(self):
            if fl.name != "etiket" and len(getattr(self, fl.name)) != n:
                raise ValueError(f"Emir.{fl.name} uzunluğu {len(getattr(self, fl.name))} ≠ {n}")
        if n and (self.i0.min() < 0 or self.i0.max() >= len(bar)):
            raise ValueError("i0 bar aralığı dışında")
        if not np.isin(self.yon, (-1, 1)).all():
            raise ValueError("yon yalnız ±1")
        for ad in ("sl_d", "tp_d", "iz_d"):
            if (getattr(self, ad) < 0).any() or np.isnan(getattr(self, ad)).any():
                raise ValueError(f"{ad} negatif/NaN")
        if (np.isfinite(self.iz_akt) & ~(self.iz_d > 0)).any():
            raise ValueError("iz süren stop etkinse iz_d > 0 olmalı")

    def secim(self, m: np.ndarray) -> "Emir":
        return Emir(*(getattr(self, f.name)[m] for f in fields(self) if f.name != "etiket"),
                    etiket={k: np.asarray(v)[m] for k, v in self.etiket.items()})


def _p(a: np.ndarray, tip):
    return np.ascontiguousarray(a, dtype=tip).ctypes.data_as(ctypes.POINTER(ctypes.c_int64 if tip is np.int64 else
                                                                            ctypes.c_int32 if tip is np.int32 else
                                                                            ctypes.c_double))


def _cekirdek(bar: V.Bar, e: Emir, sk: float) -> tuple[np.ndarray, ...]:
    n = len(e.i0)
    j, px, gir, mfe, mae = (np.empty(n, np.int64), np.empty(n), np.empty(n), np.empty(n), np.empty(n))
    ned = np.empty(n, np.int32)
    tut = [np.ascontiguousarray(x, dtype=d) for x, d in (
        (bar.t, np.int64), (bar.o, float), (bar.h, float), (bar.l, float), (bar.c, float), (bar.s, float),
        (e.i0, np.int64), (e.yon, np.int32), (e.sl_d, float), (e.tp_d, float), (e.iz_akt, float), (e.iz_d, float),
        (e.be_akt, float), (e.be_off, float), (e.t_cik, np.int64))]
    ptr = [_p(x, x.dtype.type) for x in tut]
    _LIB.sc_yol(*ptr[:6], ctypes.c_int64(len(bar)), ctypes.c_int64(n), *ptr[6:], ctypes.c_double(sk),
                _p(j, np.int64), _p(px, float), _p(gir, float), _p(ned, np.int32), _p(mfe, float), _p(mae, float))
    return j, px, gir, ned, mfe, mae


def referans(bar: V.Bar, e: Emir, sk: float = 1.0) -> tuple[np.ndarray, ...]:
    """Çekirdeğin saf Python ikizi — yalnız testlerde (yavaş)."""
    n = len(e.i0)
    out = [np.empty(n, np.int64), np.empty(n), np.empty(n), np.empty(n, np.int32), np.empty(n), np.empty(n)]
    for k in range(n):
        i, y = int(e.i0[k]), int(e.yon[k])
        E = bar.o[i] + sk * bar.s[i] if y > 0 else bar.o[i]
        S = E - y * e.sl_d[k]
        T = E + y * e.tp_d[k]
        tas, mfe, mae, sonuc = False, 0.0, 0.0, None
        for j in range(i, len(bar)):
            sj = sk * bar.s[j]
            ao, ah, al = (bar.o[j], bar.h[j], bar.l[j]) if y > 0 else (bar.o[j] + sj, bar.h[j] + sj, bar.l[j] + sj)
            if j > i and bar.t[j] >= e.t_cik[k]:
                sonuc = (j, ao, 3)
                break
            if y > 0:
                if ao <= S: sonuc = (j, ao, 2 if tas else 0); break  # noqa: E701,E702
                if ao >= T: sonuc = (j, ao, 1); break  # noqa: E701,E702
                if al <= S: sonuc = (j, S, 2 if tas else 0); break  # noqa: E701,E702
                if ah >= T: sonuc = (j, T, 1); break  # noqa: E701,E702
                fav, adv = ah - E, E - al
            else:
                if ao >= S: sonuc = (j, ao, 2 if tas else 0); break  # noqa: E701,E702
                if ao <= T: sonuc = (j, ao, 1); break  # noqa: E701,E702
                if ah >= S: sonuc = (j, S, 2 if tas else 0); break  # noqa: E701,E702
                if al <= T: sonuc = (j, T, 1); break  # noqa: E701,E702
                fav, adv = E - al, ah - E
            mfe, mae = max(mfe, fav), max(mae, adv)
            for akt, ns in ((e.iz_akt[k], (ah - e.iz_d[k]) if y > 0 else (al + e.iz_d[k])),
                            (e.be_akt[k], E + y * e.be_off[k])):
                if fav >= akt and (ns - S) * y > 0:
                    S, tas = ns, True
        if sonuc is None:
            j = len(bar) - 1
            sonuc = (j, bar.c[j] if y > 0 else bar.c[j] + sk * bar.s[j], 4)
        for a, v in zip(out, (sonuc[0], sonuc[1], E, sonuc[2], mfe, mae)):
            a[k] = v
    return tuple(out)


def simule(bar: V.Bar, e: Emir, sk: float = 1.0, komisyon_usd: float = V.KOMISYON_USD_OZ) -> pd.DataFrame:
    """sk: spread çarpanı (stres 1,5). bp = yön × (çıkış − giriş) / bid_açılış × 1e4 − komisyon bp."""
    e.dogrula(bar)
    j, px, gir, ned, mfe, mae = _cekirdek(bar, e, sk)
    ref = bar.o[e.i0]
    yon = e.yon.astype(float)
    brut = yon * (px - gir) / ref * 1e4
    df = pd.DataFrame({"i0": e.i0, "t0": bar.t[e.i0], "j": j, "t1": bar.t[j], "yon": e.yon, "giris": gir, "cikis": px,
                       "neden": pd.Categorical.from_codes(ned, list(NEDEN.values())),
                       "bp_brut": brut, "bp": brut - komisyon_usd / ref * 1e4,
                       "mfe_bp": mfe / ref * 1e4, "mae_bp": mae / ref * 1e4,
                       "R": np.where(np.isfinite(e.sl_d), (brut - komisyon_usd / ref * 1e4) / (e.sl_d / ref * 1e4), np.nan)})
    for k, v in e.etiket.items():
        df[k] = v
    return df
