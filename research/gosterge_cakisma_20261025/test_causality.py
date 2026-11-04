"""Prefix + gelecek pertürbasyonu testi (defter §3.9, E1/E16/E74).

Tam seride hesaplanan durumlar ile (a) son K bar kesilmiş, (b) son K barı rastgele bozulmuş seride hesaplanan
durumlar, ortak geçmiş barlarda birebir aynı olmalı. Aynı değilse gösterge geleceğe bakıyordur.
Kullanım: python test_causality.py NDX 1h
"""
import sys

import numpy as np

import data
import indicators

K = 300


def main(sym: str = "NDX", tf: str = "1h", n_tail: int = 6000) -> int:
    d = data.load(sym, tf).iloc[-n_tail:].reset_index(drop=True)
    full = indicators.compute(d, tf)
    cut = indicators.compute(d.iloc[:-K].reset_index(drop=True), tf)
    pert = d.copy()
    rng = np.random.default_rng(1)
    noise = 1 + rng.normal(0, 0.01, K)
    for col in ("open", "high", "low", "close"):
        pert.loc[pert.index[-K:], col] = pert[col].values[-K:] * noise
    pert["high"] = pert[["open", "high", "low", "close"]].max(axis=1)
    pert["low"] = pert[["open", "high", "low", "close"]].min(axis=1)
    pt = indicators.compute(pert, tf)
    m = len(d) - K
    bad = [k for k in full.states if not (np.array_equal(full.states[k][:m], cut.states[k][:m])
                                         and np.array_equal(full.states[k][:m], pt.states[k][:m]))]
    badf = [k for k in full.feats if not np.allclose(np.nan_to_num(full.feats[k][:m]), np.nan_to_num(pt.feats[k][:m]),
                                                      rtol=1e-4, atol=1e-6)]
    print(f"{len(full.states)} durum, {len(full.feats)} özellik; geleceğe bakan durum: {bad or 'YOK'}; özellik: {badf or 'YOK'}")
    return 1 if (bad or badf) else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
