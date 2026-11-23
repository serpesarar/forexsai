"""Özellik/sinyal nedenselliği: k'dan sonraki barlar rastgele bozulunca k ve öncesindeki özellik ve sinyaller değişmez."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import sc_ozellik as F  # noqa: E402
import sc_veri as V  # noqa: E402
from test_sim import rastgele_bar  # noqa: E402


def test_ozellik_ve_sinyal_nedensel():
    rng = np.random.default_rng(3)
    b = rastgele_bar(rng, 5000)
    oz = F.hesapla(b)
    k_tum, y_tum = F.itki_sinyal(b, oz, a=1.0, atr_oran_min=0.0, konum_min=0.5)
    assert len(k_tum) > 5
    for kes in (2500, 3300, 4100):
        b2 = V.Bar(b.t, b.o.copy(), b.h.copy(), b.l.copy(), b.c.copy(), b.s.copy())
        for a in (b2.o, b2.h, b2.l, b2.c):
            a[kes + 1:] += rng.normal(0, 3, len(a) - kes - 1)
        b2.h[:] = np.maximum.reduce([b2.h, b2.o, b2.c])
        b2.l[:] = np.minimum.reduce([b2.l, b2.o, b2.c])
        oz2 = F.hesapla(b2)
        for ad in oz.__dataclass_fields__:
            x, z = getattr(oz, ad)[: kes + 1], getattr(oz2, ad)[: kes + 1]
            assert np.allclose(x, z, equal_nan=True), ad
        k2, y2 = F.itki_sinyal(b2, oz2, a=1.0, atr_oran_min=0.0, konum_min=0.5)
        assert np.array_equal(k_tum[k_tum <= kes], k2[k2 <= kes])
