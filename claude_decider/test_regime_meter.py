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


# ── rejim-tetikli kapı: gergin VIX'te NDX SELL ──────────────────────────────
def _rg(vix):
    return rm.measure(_fx(vix=vix, dxy=100.0, atr=175.0, level=25000.0), "NDX.INDX")


def test_vix_kapisi_gergin_rejimde_tetiklenir(monkeypatch):
    monkeypatch.setattr(rm, "VIX_SELL_GATE_BLOCKS", True)
    dec = {"action": "OPEN", "direction": "SELL", "size_factor": 0.6, "reason": "x"}
    out, info = rm.vix_sell_gate("NDX.INDX", dec, _rg(19.0))
    assert out["action"] == "WAIT" and out["size_factor"] == 0.0
    assert out["vix_regime_blocked"] and info["kural"] == "vix_sell_gate"


def test_vix_kapisi_golgede_karari_degistirmez(monkeypatch):
    monkeypatch.setattr(rm, "VIX_SELL_GATE_BLOCKS", False)
    dec = {"action": "OPEN", "direction": "SELL", "size_factor": 0.6}
    out, info = rm.vix_sell_gate("NDX.INDX", dec, _rg(19.0))
    assert out["action"] == "OPEN" and info["would_block"] is True


def test_vix_kapisi_sakin_rejimde_tetiklenmez(monkeypatch):
    monkeypatch.setattr(rm, "VIX_SELL_GATE_BLOCKS", True)
    dec = {"action": "OPEN", "direction": "SELL", "size_factor": 0.6}
    out, info = rm.vix_sell_gate("NDX.INDX", dec, _rg(17.0))
    assert out is dec and info is None


def test_vix_kapisi_BUY_a_dokunmaz(monkeypatch):
    """Kanıt SELL tarafındaydı; BUY gergin bantta DAHA İYİ (%70) — engellenmemeli."""
    monkeypatch.setattr(rm, "VIX_SELL_GATE_BLOCKS", True)
    dec = {"action": "OPEN", "direction": "BUY", "size_factor": 0.6}
    out, info = rm.vix_sell_gate("NDX.INDX", dec, _rg(19.0))
    assert out is dec and info is None


def test_vix_kapisi_kapsam_disi_sembole_dokunmaz(monkeypatch):
    """USOIL gergin bantta SELL'de +0.113R (TERSİ) — kapsam dışı kalmalı."""
    monkeypatch.setattr(rm, "VIX_SELL_GATE_BLOCKS", True)
    dec = {"action": "OPEN", "direction": "SELL", "size_factor": 0.6}
    out, info = rm.vix_sell_gate("USOIL.FOREX", dec, _rg(19.0))
    assert out is dec and info is None


def test_vix_kapisi_rejim_yoksa_fail_open():
    dec = {"action": "OPEN", "direction": "SELL", "size_factor": 0.6}
    out, info = rm.vix_sell_gate("NDX.INDX", dec, None)
    assert out is dec and info is None
