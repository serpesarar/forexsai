"""or5_gece_shadow.py birim testleri + araştırma kodu paritesi (MT5 gerekmez).
Çalıştır:  cd 'yeni deneme' && python3 -m pytest test_or5_gece_shadow.py"""
import ast
from datetime import date
from pathlib import Path

import pytest

import caprev_shadow as cs
import or5_gece_shadow as og

DAY = date(2026, 10, 6)        # Salı, EDT
PREV = date(2026, 10, 5)


def t_at(minute: int, day: date = DAY) -> int:
    return int(cs.local_to_utc(day, minute, "US"))


def bar(minute: int, o, h, l, c, day: date = DAY) -> dict:
    return {"t": t_at(minute, day), "open": o, "high": h, "low": l, "close": c}


def gun(or_yukari: bool = True) -> list[dict]:
    """Dün 18:00 açılış 100; 09:29 kapanış 105 (gece yukarı). OR5 100–106; mum yönü or_yukari."""
    b = [bar(1080, 100, 101, 99, 100.5, PREV), bar(569, 104, 105, 104, 105)]
    o0, c4 = (101, 105) if or_yukari else (105, 101)
    b += [bar(570, o0, 106, 100, 103), bar(571, 103, 104, 102, 103), bar(572, 103, 104, 102, 103),
          bar(573, 103, 104, 102, 103), bar(574, 103, 105, 102, c4)]
    return b


def test_emir_cagrisi_yok():
    tree = ast.parse(Path(og.__file__).read_text(encoding="utf-8"))
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not names & {"order_send", "order_check", "Close", "positions_get"}


def test_gece_yonu_yukari():
    g, bp = og.gece_yonu(og.local_bars(gun()), DAY)
    assert g == 1 and bp == pytest.approx(500.0)


def test_gece_pazartesi_pazar_acilisi():
    mon, sun = date(2026, 10, 12), date(2026, 10, 11)
    b = [bar(1080, 200, 201, 199, 200, sun), bar(569, 190, 191, 189, 190, mon)]
    g, _ = og.gece_yonu(og.local_bars(b), mon)
    assert g == -1


def test_or5_al_tetigi_ve_stop():
    b = gun(True) + [bar(575, 104, 105, 103, 104), bar(576, 104, 107, 104, 106.5), bar(577, 106.5, 108, 106, 107)]
    trig = og.find_or5_trigger(og.local_bars(b), DAY)
    assert trig["m"] == 1 and trig["tepe"] == 106 and trig["dip"] == 100 and trig["stop"] == 100
    assert trig["trig_close"] == 106.5 and trig["entry_open"] == 106.5


def test_or5_sat_tetigi():
    b = gun(False) + [bar(575, 101, 101, 99.5, 99.8), bar(576, 99.8, 100, 99, 99.2)]
    trig = og.find_or5_trigger(og.local_bars(b), DAY)
    assert trig["m"] == -1 and trig["stop"] == 106 and trig["trig_close"] == 99.8


def test_pencere_sonrasi_kirilim_yok():
    b = gun(True) + [bar(575, 104, 105, 103, 104), bar(631, 104, 110, 104, 109)]
    assert og.find_or5_trigger(og.local_bars(b), DAY) is None


def test_walk_stop_ve_zaman():
    ex = t_at(959)
    r, how = og.walk([bar(600, 107, 108, 99, 100)], 106.5, 100, 1, ex)
    assert r == -1.0 and how == "sl"
    r, how = og.walk([bar(600, 107, 110, 105, 109), bar(959, 109, 113, 108, 112)], 106.5, 100, 1, ex)
    assert how == "time" and r == pytest.approx((112 - 106.5) / 6.5, abs=1e-3)
    r, how = og.walk([bar(600, 107, 110, 105, 109)], 106.5, 100, 1, ex)
    assert r is None


def test_summarize_kollar_ve_paket():
    recs = [{"kind": "gece", "day": "2026-10-06", "g": 1},
            {"kind": "result", "status": "done", "arm": "hizali", "R_model": 1.0, "R_fill": 0.9, "day": "2026-10-06"},
            {"kind": "result", "status": "done", "arm": "hizasiz", "R_model": -1.0, "day": "2026-10-07"}]
    s = og.summarize(recs)
    assert s["kollar"]["hizali"]["R_model"] == 1.0 and s["kollar"]["hizasiz"]["n"] == 1


def test_parite_arastirma_kodu():
    """Gerçek Duka günlerinde modül = araştırma (m, stop, giriş, spread'siz R, gece hizası)."""
    import importlib.util
    import numpy as np
    import pandas as pd
    kok = Path(__file__).resolve().parents[1]
    veri = kok / "research/trader_tersine/data/ndx_1m_full.parquet"
    src = kok / "research/trader_tersine/gelistirme/iyilestirme_20261126/src/hucreler.py"
    if not veri.exists() or not src.exists():
        pytest.skip("araştırma verisi yok (kutu)")
    spec = importlib.util.spec_from_file_location("hucreler", src)
    Hc = importlib.util.module_from_spec(spec); spec.loader.exec_module(Hc)
    x = pd.read_parquet(veri).drop_duplicates("t").sort_values("t")
    x = x[(x.t >= pd.Timestamp("2025-02-01").timestamp()) & (x.t < pd.Timestamp("2025-04-01").timestamp())]
    x.index = pd.to_datetime(x.t, unit="s")
    x["spr"] = 0.0
    ny = x.index.tz_localize("UTC").tz_convert("America/New_York")
    x["gun"], x["dk"] = ny.date, ny.hour * 60 + ny.minute
    gt = Hc.gun_tablosu(x)
    p = {"or5_son": 574, "cikis": 959}
    bars = [{"t": int(r.t), "open": r.open, "high": r.high, "low": r.low, "close": r.close} for r in x.itertuples()]
    lb = og.local_bars(bars)
    karsilastirilan = 0
    for gd, g in x[(x.dk >= 570) & (x.dk <= 959)].groupby("gun"):
        g = g.reset_index(drop=True)
        if len(g) < 300:
            continue
        ref = Hc.y1a_gun(g, None, p, gt[gd]["gece_bp"])
        trig = og.find_or5_trigger(lb, gd)
        assert (ref is None) == (trig is None), gd
        if ref is None:
            continue
        gm, _ = og.gece_yonu(lb, gd)
        assert trig["m"] == ref["m"] and int(gm == trig["m"]) == ref["gece_hiza"], gd
        r, _ = og.walk([b for b in lb if b["t"] >= trig["entry_t"]], trig["entry_open"], trig["stop"], trig["m"],
                       cs.local_to_utc(gd, 959, "US"))
        assert r == pytest.approx(ref["R"], abs=1e-4), gd
        karsilastirilan += 1
    assert karsilastirilan >= 20


# ═════════════════════════ DAX kolu (2026-11-27) ═════════════════════════

DDAY, DPREV = date(2026, 10, 6), date(2026, 10, 5)      # Salı, CEST


def dbar(minute: int, o, h, l, c, day: date = DDAY) -> dict:
    return {"t": int(cs.local_to_utc(day, minute, "EU")), "open": o, "high": h, "low": l, "close": c}


def dgun(or_yukari: bool = True) -> list[dict]:
    """Dün 17:35 açılış 100; 08:59 kapanış 105 (gece yukarı). OR5 09:00–09:04."""
    b = [dbar(1055, 100, 101, 99, 100.5, DPREV), dbar(539, 104, 105, 104, 105)]
    o0, c4 = (101, 105) if or_yukari else (105, 101)
    b += [dbar(540, o0, 106, 100, 103), dbar(541, 103, 104, 102, 103), dbar(542, 103, 104, 102, 103),
          dbar(543, 103, 104, 102, 103), dbar(544, 103, 105, 102, c4)]
    return b


def test_dax_gece_ve_tetik():
    lb = og.local_bars(dgun(True) + [dbar(545, 104, 105, 103, 104), dbar(546, 104, 107, 104, 106.5), dbar(547, 106.5, 108, 106, 107)], og.DAX)
    g, bp = og.gece_yonu(lb, DDAY, og.DAX)
    assert g == 1 and bp == pytest.approx(500.0)
    trig = og.find_or5_trigger(lb, DDAY, og.DAX)
    assert trig["m"] == 1 and trig["stop"] == 100 and trig["trig_close"] == 106.5 and trig["entry_open"] == 106.5


def test_dax_pencere_10_00():
    lb = og.local_bars(dgun(True) + [dbar(545, 104, 105, 103, 104), dbar(601, 104, 110, 104, 109)], og.DAX)
    assert og.find_or5_trigger(lb, DDAY, og.DAX) is None


def test_summarize_dax_ayri():
    recs = [{"kind": "result", "status": "done", "arm": "hizali", "R_model": 1.0, "day": "2026-10-06"},
            {"kind": "result", "status": "done", "arm": "hizali", "R_model": -1.0, "day": "2026-10-06", "market": "GDAXI.INDX"}]
    s = og.summarize(recs)
    assert s["kollar"]["hizali"]["n"] == 1 and s["DAX"]["hizali"]["R_model"] == -1.0


def test_parite_dax_arastirma():
    """Duka DAX günlerinde modül = avrupa.py (m, stop, spread'siz R, gece hizası)."""
    import importlib.util
    import numpy as np
    import pandas as pd
    kok = Path(__file__).resolve().parents[1]
    veri = kok / "research/fibo_altin_bolge_20261116/cache/DAX_1m_raw.parquet"
    src = kok / "research/trader_tersine/gelistirme/avrupa_or5_20261127/src/avrupa.py"
    if not veri.exists() or not src.exists():
        pytest.skip("araştırma verisi yok (kutu)")
    spec = importlib.util.spec_from_file_location("avrupa", src); A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    x = pd.read_parquet(veri).drop_duplicates("t").sort_values("t")
    x = x[(x.t >= pd.Timestamp("2025-02-01").timestamp()) & (x.t < pd.Timestamp("2025-04-01").timestamp())]
    x.index = pd.to_datetime(x.t, unit="s"); x = x[["open", "high", "low", "close"]].copy()
    lo = x.index.tz_localize("UTC").tz_convert("Europe/Berlin"); x["gun"], x["dk"] = lo.date, lo.hour * 60 + lo.minute; x["spr"] = 0.0
    gece_ac = x[x.dk >= A.GECE].groupby("gun").open.first(); pre = x[(x.dk >= 480) & (x.dk < A.AC)].groupby("gun").close.last()
    bars = [{"t": int(r.Index.timestamp()), "open": r.open, "high": r.high, "low": r.low, "close": r.close} for r in x.itertuples()]
    lb = og.local_bars(bars, og.DAX)
    rth = {g: d.reset_index(drop=True) for g, d in x[(x.dk >= A.AC) & (x.dk <= A.CIK)].groupby("gun")}
    gunler = sorted(rth); n = 0
    for k, gd in enumerate(gunler):
        g = rth[gd]
        if len(g) < 400 or g.dk.iloc[0] != A.AC or k == 0:
            continue
        onc = gunler[k - 1]
        gb = (pre[gd] / gece_ac[onc] - 1) * 1e4 if (onc in gece_ac.index and gd in pre.index) else np.nan
        ref = A.r0(g, gb); trig = og.find_or5_trigger(lb, gd, og.DAX)
        assert (ref is None) == (trig is None), gd
        if ref is None:
            continue
        gm, _ = og.gece_yonu(lb, gd, og.DAX)
        assert trig["m"] == ref["m"] and int(gm == trig["m"]) == ref["gece_hiza"], gd
        r, _ = og.walk([b for b in lb if b["t"] >= trig["entry_t"]], trig["entry_open"], trig["stop"], trig["m"], cs.local_to_utc(gd, 1049, "EU"))
        assert r == pytest.approx(ref["R"], abs=1e-4), gd
        n += 1
    assert n >= 20
