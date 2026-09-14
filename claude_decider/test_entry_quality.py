"""entry_quality kapısının regresyon testleri — doğrulanmış eşikler kilitli."""
import entry_quality as eq


def _fx(channel_z=None, vol_ratio=None):
    return {"tfs": {"5m": {"channel_z": channel_z, "vol_ratio": vol_ratio}}, "macro": {}}


def test_esikler_kanitla_uyumlu():
    """OOS'ta doğrulanan eşikler — değişirse kanıt geçersiz olur."""
    assert eq.KNIFE_CHZ_MAX == 2.0
    assert eq.VOL_SPIKE_MAX == 1.5


def test_buy_kanal_dibinde_bicak_yakalama():
    # BUY + channel_z=-2.3 → chz_dir=+2.3 ≥ 2.0 → elenir
    q = eq.assess(_fx(channel_z=-2.3, vol_ratio=1.0), "BUY")
    assert q["blocked"] and q["chz_dir"] == 2.3
    assert any("bicak_yakalama" in r for r in q["reasons"])


def test_sell_kanal_tepesinde_bicak_yakalama():
    # SELL + channel_z=+2.3 → chz_dir=+2.3 → elenir (simetrik)
    q = eq.assess(_fx(channel_z=2.3, vol_ratio=1.0), "SELL")
    assert q["blocked"] and q["chz_dir"] == 2.3


def test_yon_isareti_ters_tarafta_elemez():
    # BUY + channel_z=+2.3 (kanal TEPESİNDE alım) → chz_dir=-2.3 → bu koşul tetiklenmez
    q = eq.assess(_fx(channel_z=2.3, vol_ratio=1.0), "BUY")
    assert not any("bicak_yakalama" in r for r in q["reasons"])


def test_hacim_patlamasi():
    q = eq.assess(_fx(channel_z=0.0, vol_ratio=1.7), "BUY")
    assert q["blocked"] and any("hacim_patlamasi" in r for r in q["reasons"])


def test_temiz_kurulum_gecer():
    q = eq.assess(_fx(channel_z=-0.8, vol_ratio=1.0), "BUY")
    assert not q["blocked"] and q["score"] == 100


def test_skor_derinlikle_duser():
    sig = eq.assess(_fx(channel_z=-1.5, vol_ratio=1.0), "BUY")["score"]
    orta = eq.assess(_fx(channel_z=-2.2, vol_ratio=1.0), "BUY")["score"]
    derin = eq.assess(_fx(channel_z=-3.5, vol_ratio=1.0), "BUY")["score"]
    assert sig > orta > derin and derin == 40


def test_veri_yoksa_fail_open():
    assert eq.assess(None, "BUY")["blocked"] is False
    assert eq.assess(_fx(), "BUY")["blocked"] is False
    assert eq.assess(_fx(channel_z=-3.0), None)["blocked"] is False


def test_golge_modda_karar_degismez(monkeypatch):
    monkeypatch.setattr(eq, "GATE_BLOCKS", False)
    dec = {"action": "OPEN", "direction": "BUY", "size_factor": 0.5}
    out, q = eq.apply_gate("NDX.INDX", dec, _fx(channel_z=-2.5, vol_ratio=1.0))
    assert out["action"] == "OPEN" and out["size_factor"] == 0.5
    assert q["blocked"] and q.get("would_block") is True


def test_blok_modda_open_wait_olur(monkeypatch):
    monkeypatch.setattr(eq, "GATE_BLOCKS", True)
    dec = {"action": "OPEN", "direction": "BUY", "size_factor": 0.5, "reason": "kanit"}
    out, q = eq.apply_gate("NDX.INDX", dec, _fx(channel_z=-2.5, vol_ratio=1.0))
    assert out["action"] == "WAIT" and out["size_factor"] == 0.0
    assert out["entry_quality_blocked"] and "GİRİŞ-KALİTESİ" in out["reason"]


def test_wait_karari_dokunulmaz(monkeypatch):
    monkeypatch.setattr(eq, "GATE_BLOCKS", True)
    dec = {"action": "WAIT", "direction": "BUY", "size_factor": 0.0}
    out, _ = eq.apply_gate("NDX.INDX", dec, _fx(channel_z=-2.5, vol_ratio=1.0))
    assert out is dec      # salt supresif: WAIT'e dokunmaz


def test_wait_karsi_olgu_yonuyle_olculur(monkeypatch):
    """WAIT'te karar değişmez ama karşı-olgu yönü için kalite ÖLÇÜLÜR (gölge örneklemi)."""
    monkeypatch.setattr(eq, "GATE_BLOCKS", True)
    dec = {"action": "WAIT", "direction": None, "size_factor": 0.0}
    out, q = eq.apply_gate("NDX.INDX", dec, _fx(channel_z=-2.5, vol_ratio=1.0),
                           cf_direction="BUY")
    assert out is dec
    assert q["blocked"] and q["counterfactual_dir"] == "BUY" and q["chz_dir"] == 2.5


def test_yonsuz_wait_bos_blob_yazmaz():
    """Yön de karşı-olgu da yoksa journal'a boş blob yazılmaz (gürültü temizliği)."""
    dec = {"action": "WAIT", "direction": None, "size_factor": 0.0}
    out, q = eq.apply_gate("NDX.INDX", dec, _fx(channel_z=-2.5, vol_ratio=1.0))
    assert out is dec and q is None
