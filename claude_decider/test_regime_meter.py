"""regime_meter testleri — ölçüm doğru, zarf uyarısı çalışıyor, hiçbir şeyi bloklamıyor."""
import regime_meter as rm


def _fx(vix=17.0, dxy=100.0, atr=50.0, level=25000.0, adx4=25.0, vol4=1.0,
        trends=("yukari", "yukari", "yatay", "asagi")):
    t5, t30, t1h, t4h = trends
    return {"tfs": {
        "5m": {"trend": t5}, "30m": {"trend": t30},
        "1h": {"trend": t1h, "adx": 20.0},
        "4h": {"trend": t4h, "adx": adx4, "vol_ratio": vol4, "atr": atr,
               "sr": {"res": {"level": level}}},
    }, "macro": {"vix": vix, "dxy": dxy}}


def test_veri_yoksa_none():
    assert rm.measure(None, "NDX.INDX") is None


def test_temel_olcum():
    r = rm.measure(_fx(vix=17.0, atr=50.0, level=25000.0), "NDX.INDX")
    assert r["vix_band"] == "normal"
    assert r["atrp_4h"] == 0.2       # 100*50/25000
    assert r["tf_yatay"] == 1
    assert r["disarida"]             # 0.2 NDX zarfinin (0.48-0.97) disinda


def test_vix_bantlari():
    assert rm.measure(_fx(vix=14.0), "NDX.INDX")["vix_band"] == "cok_sakin"
    assert rm.measure(_fx(vix=16.0), "NDX.INDX")["vix_band"] == "sakin"
    assert rm.measure(_fx(vix=17.5), "NDX.INDX")["vix_band"] == "normal"
    assert rm.measure(_fx(vix=20.0), "NDX.INDX")["vix_band"] == "gergin"
    assert rm.measure(_fx(vix=30.0), "NDX.INDX")["vix_band"] == "kriz"


def test_zarf_disi_uyarisi():
    """VIX 28 gözlenen 15.1-19.6 zarfının dışında → kapı kanıtı gecersiz uyarisi."""
    r = rm.measure(_fx(vix=28.0), "NDX.INDX")
    assert any("vix" in d for d in r["disarida"])
    assert "DOĞRULANMADI" in r["uyari"]


def test_zarf_icinde_uyari_yok():
    # NDX zarfi 0.48-0.97 → atr/level = 100*175/25000 = 0.7
    r = rm.measure(_fx(vix=17.0, dxy=100.0, atr=175.0, level=25000.0), "NDX.INDX")
    assert r["disarida"] == [] and "uyari" not in r


def test_tf_uyum_hesabi():
    r = rm.measure(_fx(trends=("yukari", "yukari", "yukari", "asagi")), "NDX.INDX")
    assert r["tf_uyum"] == 0.75 and r["tf_yatay"] == 0


def test_hepsi_yatay_uyum_none():
    r = rm.measure(_fx(trends=("yatay",)*4), "NDX.INDX")
    assert r["tf_uyum"] is None and r["tf_yatay"] == 4


def test_bilinmeyen_sembol_atr_zarfi_atlanir():
    r = rm.measure(_fx(vix=17.0, dxy=100.0), "BILINMEYEN")
    assert all("atrp_4h" not in d for d in r["disarida"])
