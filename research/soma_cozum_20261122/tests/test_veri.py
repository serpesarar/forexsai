"""Entegrasyon: bar bütünlüğü, saat ekseni hizalaması, kopya sadakati, kasa kilidi. Gerçek veri gerekir (data/ gitignore)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import sc_degerlendir as D  # noqa: E402
import sc_veri as V  # noqa: E402

pytestmark = pytest.mark.skipif(not V.POZ.exists(), reason="sağlayıcı verisi yok")


def test_bar_butunlugu():
    b = V.barlar()
    assert (np.diff(b.t) > 0).all() and (b.s > 0).all() and (b.h >= b.l).all()


@pytest.mark.parametrize("hesap,esik", [("2268766", 0.95), ("2347514", 0.85)])
def test_saat_ekseni(hesap, esik):
    p = V.islemler(hesap, sessiz=True)
    assert p.attrs["saat_modeli"] == "ny7" and p.attrs["hizalama"] >= esik


def test_kopya_sadakati():
    import sc01_ayristirma as A
    H = A.Hazir()
    p = V.islemler("2268766", sessiz=True)
    p = p[p["bar_var"]].reset_index(drop=True)
    t0 = p["t_giris"].to_numpy() // 60 * 60 + 60
    t1 = p["t_cikis"].to_numpy() // 60 * 60 + 60
    r = A.bacak_sim(H, t0, np.maximum(t1 - t0, 60), p["yon"].to_numpy().astype(np.int32), p["volume"].to_numpy(),
                    np.arange(len(p)))
    kendi = p["bp_kendi"].to_numpy()[r["sinyal"].to_numpy()]
    assert np.corrcoef(kendi, r["bp"])[0, 1] >= 0.95


def test_kasa_kilidi():
    os.environ.pop("SC_KASA_ACIK", None)
    with pytest.raises(PermissionError):
        D.donem_maske(np.array([D.ts("2012-01-01")]), "KASA", "SC-99")
    os.environ["SC_KASA_ACIK"] = "SC-99"
    with pytest.raises(PermissionError):  # ön kayıtlı aday değil
        D.donem_maske(np.array([D.ts("2012-01-01")]), "KASA", "SC-99")
    os.environ.pop("SC_KASA_ACIK", None)


def test_sinyal_birimi():
    p = V.islemler("2268766", sessiz=True)
    g = p.groupby("sinyal")
    assert (g["yon"].nunique() == 1).all()
    assert ((g["t_giris"].max() - g["t_giris"].min()) >= 0).all()
