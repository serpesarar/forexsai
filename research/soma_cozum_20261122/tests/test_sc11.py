"""SC-11 tik katmanı: ayrıştırma, bütünlük, özelliklerin nedenselliği ve yavaş referansla eşitliği."""
from __future__ import annotations

import lzma
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import sc08_ozellik as F  # noqa: E402
import sc11_tik_ozellik as O  # noqa: E402
import sc_tick as TK  # noqa: E402


def test_ayristirma(tmp_path, monkeypatch):
    monkeypatch.setattr(TK, "TK", tmp_path)
    TK.saat.cache_clear()
    h = 1_735_689_600
    r = np.zeros(3, dtype=TK.KAYIT)
    r["ms"], r["ask"], r["bid"], r["av"], r["bv"] = [5, 1500, 3_599_999], [2_650_500, 2_650_600, 2_651_000], \
        [2_650_200, 2_650_300, 2_650_700], [0.1, 0.2, 0.3], [0.4, 0.5, 0.6]
    TK.yol(h).write_bytes(lzma.compress(r.tobytes(), format=lzma.FORMAT_ALONE))
    t, bid, ask, v = TK.saat(h)
    assert list(t) == [h * 1000 + 5, h * 1000 + 1500, h * 1000 + 3_599_999]
    assert np.allclose(bid, [2650.2, 2650.3, 2650.7]) and np.allclose(ask, [2650.5, 2650.6, 2651.0])
    assert np.allclose(v, [0.5, 0.7, 0.9], atol=1e-6)
    TK.yol(h + 3600).write_bytes(b"")
    assert len(TK.saat(h + 3600)[0]) == 0
    t2 = TK.aralik(h + 1, h + 3600 + 100)[0]
    assert list(t2) == [h * 1000 + 1500, h * 1000 + 3_599_999]
    TK.saat.cache_clear()


def _ornek_saat() -> int | None:
    dosya = sorted(TK.TK.glob("*.bi5")) if TK.TK.exists() else []
    for f in dosya:
        if f.stat().st_size > 20_000:
            h = int(pd.Timestamp(f.stem[:8] + " " + f.stem[8:] + ":00", tz="UTC").timestamp())
            if TK.yol(h - 3600).exists() and TK.yol(h - 3600).stat().st_size > 0:
                return h
    return None


@pytest.fixture(scope="module")
def ortam():
    h = _ornek_saat()
    if h is None:
        pytest.skip("tik verisi yok")
    return h, F.yukle("2024-06-01")


def test_butunluk(ortam):
    h, _ = ortam
    r = TK.denetle([h - 3600, h])
    assert r["esit_pay"] >= 0.99 and r["dakika"] > 30


def test_nedensellik(ortam, monkeypatch):
    h, M = ortam
    a, b, c = h + 600, h + 1500, h + 1000
    gercek = TK.aralik
    X0 = O.pencere(M, a, b, 1)

    def bozuk(x, z):
        t, bid, ask, v = gercek(x, z)
        sonra = t >= (c + 1) * 1000
        rng = np.random.default_rng(1)
        bid = np.where(sonra, bid + rng.normal(0, 5, len(t)), bid)
        return t, bid, bid + 0.3, v

    monkeypatch.setattr(TK, "aralik", bozuk)
    X1 = O.pencere(M, a, b, 1)
    m = X0["s"] <= c
    kol = [k for k in O.OZELLIKLER if k != "spread"]   # spread ask'a bağlı; bozukta ask değişti
    pd.testing.assert_frame_equal(X0.loc[m, kol].reset_index(drop=True), X1.loc[m, kol].reset_index(drop=True))
    assert not X0.loc[~m, "r30"].equals(X1.loc[~m, "r30"])


@pytest.mark.parametrize("y", [1, -1])
def test_referans(ortam, y):
    """Saf döngüyle yazılmış referans ile vektörel özellikler aynı."""
    h, M = ortam
    a, b = h + 300, h + 3000
    X = O.pencere(M, a, b, y).set_index("s")
    t, bid, ask, vol = TK.aralik(a - O.GERI, b + 1)
    sv = O._seviye(M, np.arange(a, b + 1), y)
    rng = np.random.default_rng(7)
    for s in rng.choice(np.arange(a, b + 1), 40, replace=False):
        i = s - a
        m = t < (s + 1) * 1000
        tb = bid[m]
        p = tb[-1]
        atr1 = sv["atr1"][i]
        onc = bid[t < (s - 30 + 1) * 1000][-1]
        assert X.at[s, "r30"] == pytest.approx((p - onc) * y / atr1)
        n30 = int(((t >= (s - 30 + 1) * 1000) & m).sum())
        n3600 = int(((t >= (s - 3600 + 1) * 1000) & m).sum())
        assert X.at[s, "tk30"] == pytest.approx(n30 / (30 * n3600 / 3600))
        d = np.sign(np.diff(tb))
        d = d[d != 0]
        run = 0
        if len(d):
            run = 1
            while run < len(d) and d[-run - 1] == d[-1]:
                run += 1
            run *= d[-1]
        assert X.at[s, "ardisik"] == pytest.approx(run * y)
        ext = sv["ext_H4"][i]
        if (p - ext) * y > 0:
            alt = np.flatnonzero((tb - ext) * y <= 0)
            bek = min(s - t[m][alt[-1]] // 1000, O.YOK_SN) if len(alt) else O.YOK_SN
            assert X.at[s, "gecis_H4"] == pytest.approx(bek)
        else:
            assert X.at[s, "gecis_H4"] == -1
        assert X.at[s, "d_H4"] == pytest.approx((p - ext) * y / sv["atr_H4"][i])
