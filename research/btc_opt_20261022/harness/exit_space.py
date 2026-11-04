"""Çıkış uzayı: aile ufuk sınıfına göre (scalp / intraday / swing) ön-tanımlı spec ızgaraları.

Her spec'te sunucu SL'si zorunlu (R paydası). Ufuk sınıfları:
- scalp    : ≤ 4 sa tutuş, her zaman rollover−2'de zorunlu kapanış (force_ro)
- intraday : 1 sa … 24 sa; varsayılan force_ro (ATR1h ölçekli long'da tek gece swap'ı ≈ 0,05R — E50/X11), bilgi için
             force_ro'suz 24 sa ve UTC gün sonu da var
- swing    : 1 … 20 gün; aile özgün bitişi (`orig`) ve UTC gün sonu
`orig_spec()` ailenin özgün geometrisini (sl_orig, tp_orig, end_orig) tek spec olarak verir (yeniden üretim için).
"""
from __future__ import annotations

import itertools

import numpy as np

from exits import NAN, ExitSpec

RR = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, NAN]


def _sl(kind, *a):
    if kind == "atr":
        tf, mult, floor = (a + (0.0,))[:3]
        return dict(sl_kind="atr", sl_tf=tf, sl_mult=float(mult), sl_floor_bp=float(floor))
    return dict(sl_kind="bp", sl_bp=float(a[0]))


CLASSES = {
    "scalp": dict(
        sl=[_sl("atr", "5m", 1.1, 19), _sl("atr", "5m", 2, 19), _sl("atr", "5m", 3, 19),
            _sl("atr", "15m", 1), _sl("atr", "15m", 1.5), _sl("atr", "15m", 2),
            _sl("atr", "1h", 0.5), _sl("atr", "1h", 1),
            _sl("bp", 19), _sl("bp", 28), _sl("bp", 40), _sl("bp", 60)],
        ends=[dict(time_min=t, force_ro=True) for t in (15, 30, 60, 120, 240)],
        pd_sl=[0, 1, 3, 7], pd_ends=[dict(time_min=60, force_ro=True), dict(time_min=240, force_ro=True)],
        trail_tf=["5m", "15m"], trail_k=[1, 2], trail_sl=[1, 4]),
    "intraday": dict(
        sl=[_sl("atr", "15m", 1), _sl("atr", "15m", 2), _sl("atr", "15m", 3),
            _sl("atr", "1h", 0.5), _sl("atr", "1h", 1), _sl("atr", "1h", 1.5), _sl("atr", "1h", 2),
            _sl("atr", "1h", 3), _sl("atr", "4h", 0.5), _sl("atr", "4h", 1),
            _sl("bp", 30), _sl("bp", 60), _sl("bp", 100), _sl("bp", 200)],
        ends=[dict(time_min=60, force_ro=True), dict(time_min=240, force_ro=True), dict(time_min=720, force_ro=True),
              dict(struct="ro"), dict(time_min=1440), dict(struct="day")],
        pd_sl=[4, 5, 6, 9], pd_ends=[dict(time_min=240, force_ro=True), dict(struct="ro"), dict(time_min=1440)],
        trail_tf=["15m", "1h"], trail_k=[1, 2, 3], trail_sl=[5, 6]),
    "swing": dict(
        sl=[_sl("atr", "1h", 1), _sl("atr", "1h", 2), _sl("atr", "1h", 3),
            _sl("atr", "4h", 1), _sl("atr", "4h", 1.5), _sl("atr", "4h", 2), _sl("atr", "4h", 3),
            _sl("atr", "1d", 0.5), _sl("atr", "1d", 1), _sl("atr", "1d", 1.5), _sl("atr", "1d", 2),
            _sl("atr", "1d", 3),
            _sl("bp", 100), _sl("bp", 200), _sl("bp", 400), _sl("bp", 800)],
        ends=[dict(time_min=1440), dict(time_min=2880), dict(time_min=7200), dict(time_min=14400),
              dict(time_min=28800), dict(struct="day"), dict(struct="orig")],
        pd_sl=[5, 6, 8, 9], pd_ends=[dict(time_min=2880), dict(time_min=7200), dict(time_min=28800)],
        trail_tf=["4h", "1d"], trail_k=[1, 2, 3], trail_sl=[5, 8]),
}


def build_space(cls: str, include_pathdep: bool = True, include_opp: bool = False) -> list[ExitSpec]:
    C = CLASSES[cls]
    ends = list(C["ends"]) + ([dict(struct="opp")] if include_opp else [])
    out = []
    for sl, rr, en in itertools.product(C["sl"], RR, ends):
        out.append(ExitSpec(**sl, tp_rr=rr, **en))
    if include_pathdep:
        for si, be, rr, en in itertools.product(C["pd_sl"], (0.5, 1.0), (1.5, 2.0, 3.0, NAN), C["pd_ends"]):
            out.append(ExitSpec(**C["sl"][si], be_R=be, tp_rr=rr, **en))
        for si, r1, r2, en in itertools.product(C["pd_sl"], (0.75, 1.0), (2.0, NAN), C["pd_ends"]):
            out.append(ExitSpec(**C["sl"][si], part_frac=0.5, part_rr1=r1, tp_rr=r2, part_be=True, **en))
        for si, tf, k, act, en in itertools.product(C["trail_sl"], C["trail_tf"], C["trail_k"], (0.0, 0.5, 1.0),
                                                    C["pd_ends"][-2:]):
            out.append(ExitSpec(**C["sl"][si], trail_tf=tf, trail_k=float(k), trail_act_R=act, **en))
    seen, uniq = set(), []
    for s in out:
        if s.key() not in seen:
            seen.add(s.key())
            uniq.append(s)
    return uniq


def orig_spec(has_tp: bool) -> ExitSpec:
    return ExitSpec(sl_kind="orig", tp_rr=-1.0 if has_tp else NAN, struct="orig")


def random_spec(cls: str, rng: np.random.Generator) -> ExitSpec:
    """BTC'ye özgü optimize edici modu için sürekli uzaydan örnek (eğitim penceresi İÇİNDE kullanılır)."""
    tfs = {"scalp": ["5m", "15m", "1h"], "intraday": ["15m", "1h", "4h"], "swing": ["1h", "4h", "1d"]}[cls]
    tmin = {"scalp": (10, 240), "intraday": (60, 1440), "swing": (1440, 28800)}[cls]
    tf = str(rng.choice(tfs))
    mult = float(np.round(np.exp(rng.uniform(np.log(0.4), np.log(5.0))), 2))
    rr = float(np.round(np.exp(rng.uniform(np.log(0.5), np.log(4.0))), 2)) if rng.random() < 0.8 else NAN
    t = int(np.round(np.exp(rng.uniform(np.log(tmin[0]), np.log(tmin[1])))))
    force = cls != "swing" and (cls == "scalp" or rng.random() < 0.7)
    base = dict(sl_kind="atr", sl_tf=tf, sl_mult=mult, sl_floor_bp=19.0 if cls == "scalp" else 0.0,
                tp_rr=rr, time_min=t, force_ro=force)
    u = rng.random()
    if u < 0.15:
        base["be_R"] = float(np.round(rng.uniform(0.3, 1.5), 2))
    elif u < 0.25:
        base["trail_tf"] = str(rng.choice(tfs))
        base["trail_k"] = float(np.round(rng.uniform(0.5, 4.0), 2))
        base["trail_act_R"] = float(rng.choice([0.0, 0.5, 1.0]))
    return ExitSpec(**base)
