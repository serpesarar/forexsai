"""Kombo madencisinin doğrulamayı geçen adaylarının çapraz tekrarı (EK-P8).

Her aday (val_ok) aynı tanımla — script durumları "aktif"/"taze", h bar susturma, aynı yön — şu pencerelerde
TEK BLOK ölçülür: aynı pencerenin diğer 3 sembolü ve (koşu varsa) tf_15m'de aynı + diğer semboller.
MIX (karışım kovası) içeren adaylar sembole/TF'ye özgü kantil kovası olduğundan atlanır ve sayısı yazılır.
Çıktı: results_kombo/<kaynak pencere>/tekrar.csv
CLI: python kombo_tekrar.py recent [tf_15m ...]
"""
from __future__ import annotations

import gzip
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gosterge_cakisma_20261025"))
sys.path.insert(0, str(HERE))
import config as GC  # noqa: E402
import data  # noqa: E402
import engine as E  # noqa: E402
import eval_scripts as EV  # noqa: E402
import kombo_madenci as KM  # noqa: E402

SYMS = ("NDX", "DAX", "XAU", "USOIL")


def _parse(kosullar: str):
    """'A:sid|durum & T:sid|durum' → [(etiket, sid, durum)]; MIX varsa None."""
    out = []
    for part in re.split(r" & (?=(?:A|T|MIX):)", kosullar):     # durum adları da " & " içerebilir
        tag, rest = part.split(":", 1)
        if tag == "MIX":
            return None
        sid, state = rest.split("|", 1)
        out.append((tag, sid, state))
    return out


def _states(window: str, sym: str, n: int, need: set) -> dict:
    out = {}
    for p in sorted((HERE / "data/runs" / window).glob("part_*.pkl.gz")):
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                if r["sid"] not in need:
                    continue
                v = r["per_sym"].get(sym)
                if v and v["status"] == "ok":
                    for k, b in v["states"].items():
                        out[(r["sid"], k)] = np.unpackbits(np.frombuffer(b, np.uint8))[:n].astype(bool)
    return out


def _measure(conds, states, d, tf, h, dsg, cost):
    cols = []
    for tag, sid, st in conds:
        if (sid, st) not in states:
            return None
        S = states[(sid, st)][:, None]
        cols.append(S[:, 0] if tag == "A" else KM._fresh(S)[:, 0])
    X = np.logical_and.reduce(cols)[:, None]
    T = KM.events(X, h)[:, 0]
    d2 = d.copy()
    d2["split"] = 0
    L = E.labels(d2, data.bucket(d2, tf), h, cost)
    vec = E.weights(L)[np.flatnonzero(T)].sum(axis=0)
    out = E.directional(E.split_stats(vec, 0), np.array(dsg), L["cost"][0])
    return {k: float(np.asarray(out[k]).ravel()[0]) for k in ("n", "z", "hit", "base", "lift", "ret_bp", "cost_bp")}


def main(src: str, targets: list[str]):
    cand = pd.concat([pd.read_csv(p) for p in sorted((HERE / "results_kombo" / src).glob("*/adaylar.csv"))])
    cand = cand[cand.val_ok].copy()
    cand["conds"] = cand.kosullar.map(_parse)
    print(f"{src}: {len(cand)} doğrulama-geçen aday, MIX'li atlanan {int(cand.conds.isna().sum())}", flush=True)
    cand = cand[cand.conds.notna()]
    need = {sid for cs in cand.conds for _, sid, _ in cs}
    rows = []
    for win in [src] + targets:
        if not (HERE / "data/runs" / win).exists():
            continue
        tf = EV.window_tf(win)
        for sym in SYMS:
            own = cand[cand.sym != sym] if win == src else cand
            if own.empty:
                continue
            d = EV.window_frame(sym, win)
            states = _states(win, sym, len(d), need)
            for c in own.itertuples():
                m = _measure(c.conds, states, d, tf, int(c.h), 1.0 if c.dir == "BUY" else -1.0, GC.SPREAD[sym])
                if m is None:
                    continue
                rows.append(dict(kombo_id=c.kombo_id, src_sym=c.sym, h=c.h, dir=c.dir, kanitli=c.kanitli,
                                 window=win, sym=sym, ayni_sembol=sym == c.sym, **m,
                                 n_ok=m["n"] >= GC.N_MIN[tf] / 4))
            print(f"  {win} {sym} ölçüldü", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "results_kombo" / src / "tekrar.csv", index=False)
    o = out[out.n_ok]
    for (win, same), g in o.groupby(["window", "ayni_sembol"]):
        print(f"{win} {'aynı sembol' if same else 'diğer semboller'}: {len(g)} ölçüm, aynı yön z≥1,645 "
              f"{int((g.z >= GC.Z_PASS).sum())}, ters {int((g.z <= -GC.Z_PASS).sum())}, ort z {g.z.mean():+.2f}")
    k = o[o.kanitli]
    if len(k):
        print("kanıtlılar:")
        print(k[["kombo_id", "window", "sym", "n", "z", "lift", "ret_bp", "cost_bp"]].to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
