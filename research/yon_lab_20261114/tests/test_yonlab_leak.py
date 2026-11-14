"""Yön Lab — referans ve ek durum hesaplarının sızıntı (kesme eşdeğerliği + gelecek bozma) testi."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / 'src'))
sys.path.insert(0, str(H.parents[1] / 'backend'))
import core as C  # noqa: E402
import extras as X  # noqa: E402
import refs as R  # noqa: E402
from tests.test_nom_features import synth_bars  # noqa: E402


def _same(a: pd.DataFrame, b: pd.DataFrame) -> list[str]:
    bad = []
    for c in a.columns:
        x, y = a[c].to_numpy(float), b[c].to_numpy(float)
        if not ((np.isnan(x) & np.isnan(y)) | np.isclose(x, y, rtol=1e-6, atol=1e-6)).all():
            bad.append(c)
    return bad


def test_refs_extras_truncation_and_perturbation():
    b = synth_bars(days=70, seed=11)
    td, i1 = C.grid(b)
    pick = np.sort(np.random.default_rng(0).choice(np.arange(len(td) // 2, len(td) - 10), 6, replace=False))
    Rf, Xf = R.build_refs(b, td[pick], i1[pick]), X.build_extras(b, td[pick])
    for k, j in enumerate(pick):
        cut = b[b.t < td[j]].reset_index(drop=True)
        tt, ii = np.array([td[j]]), np.array([len(cut) - 1])
        assert not _same(Rf.iloc[[k]].reset_index(drop=True), R.build_refs(cut, tt, ii)), 'refs kesme'
        assert not _same(Xf.iloc[[k]].reset_index(drop=True).drop(columns=[c for c in Xf if c.startswith('_')], errors='ignore'),
                         X.build_extras(cut, tt).drop(columns=[c for c in Xf if c.startswith('_')], errors='ignore')), 'extras kesme'
        pb = b.copy()
        fut = pb.t >= td[j]
        pb.loc[fut, ['open', 'high', 'low', 'close']] += 77.0
        assert not _same(Rf.iloc[[k]].reset_index(drop=True), R.build_refs(pb, tt, np.array([i1[j]]))), 'refs gelecek bozma'
