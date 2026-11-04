"""Doğrulamayı geçen Pine adaylarının tekrarlanma sınaması (PROTOCOL §5 + EK-P1).

1) Aday scriptleri (+ L2b eş scriptlerini) **past** ve **old** pencerelerinde ve **1m/5m/15m/4h/1d** verisinin son 12.000 barında
   yeniden çalıştırır.
2) Her adayın aynı tanımını (script durumu [+ eş]) şu pencerelerin tamamında tek blok ölçer:
   - past (önceki 12.000 bar), old (son pencereden önceki TÜM tarih, EK-P3), recent (diğer semboller),
     tf_<tf> (aynı sembol).
Çıktı: results/tekrar_pine.csv
"""
from __future__ import annotations

import gzip
import pickle
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gosterge_cakisma_20261025"))
sys.path.insert(0, str(HERE))
import config as GC  # noqa: E402
import data  # noqa: E402
import engine as E  # noqa: E402
import indicators  # noqa: E402
import batch  # noqa: E402
import eval_scripts as EV  # noqa: E402

SYMS = ("NDX", "DAX", "XAU", "USOIL")
TF_WINDOWS = ("tf_1m", "tf_5m", "tf_15m", "tf_4h", "tf_1d")      # EK-P1
WORKERS = 7
OLD_TIMEOUT_MULT = 4
FLUSH_EVERY = 500


def candidates() -> pd.DataFrame:
    frames = [pd.read_csv(p) for p in sorted((HERE / "results").glob("*/cells.csv"))]
    c = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return c[c.val_ok] if len(c) else c


def _partner_key(c):
    """L2b eşi → (sid, durum); GÇM eşi / eşsiz → None."""
    if isinstance(c.partner, str) and c.partner.startswith("R:"):
        psid, pst = c.partner[2:].split("|", 1)
        return psid, pst
    return None


def _init_win(window: str):
    if window.startswith("tf_"):
        tf = window[3:]
        batch.TF = tf                                  # _run_one bu modül globalini okur
        for s in SYMS:
            batch._DF[s] = data.load(s, tf).iloc[-batch.N_BARS:].reset_index(drop=True)
    elif window == "old":                                  # EK-P3: son pencereden önceki tüm 1h tarihi
        for s in SYMS:
            d = data.load(s, batch.TF)
            batch._DF[s] = d.iloc[:len(d) - batch.N_BARS].reset_index(drop=True)
        batch.TIMEOUT_S = batch.TIMEOUT_S * OLD_TIMEOUT_MULT     # ~4 kat bar → orantılı süre
    else:
        batch._init(window)


def run_window(window: str, sids: set):
    import pine_src
    run_dir = HERE / "data/runs" / window
    run_dir.mkdir(parents=True, exist_ok=True)
    done = batch.done_sids(run_dir)
    recs = [r for r in pine_src.iter_sources(True) if r["sid"] in sids and r["sid"] not in done]
    if not recs:
        return
    print(f"{window}: {len(recs)} script çalıştırılıyor", flush=True)
    k = len(list(run_dir.glob("part_*.pkl.gz")))
    out = []
    with Pool(WORKERS, initializer=_init_win, initargs=(window,), maxtasksperchild=200) as pool:
        for res in pool.imap_unordered(batch._run_one, recs, chunksize=1):
            out.append(res)
            if len(out) == FLUSH_EVERY:                # tüm-script koşusunda bellek + kesintiye dayanıklılık
                batch._flush(run_dir, k, out)
                k, out = k + 1, []
                print(f"{window}: parça {k}", flush=True)
    if out:
        batch._flush(run_dir, k, out)


def state_arrays(window: str, sym: str, n: int, need: set) -> dict:
    """(sid, durum adı) → bool dizisi (yalnız gereken scriptler için)."""
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


def measure(c, d, tf, states, gbook, cost):
    """Bir aday tanımını bir pencerenin tamamında ölç (tek blok)."""
    key = (c.sid, c.state)
    if key not in states:
        return None
    T = E.thin(EV.onsets(states[key][:, None]), int(c.h))[:, 0]
    if isinstance(c.partner, str) and c.partner.startswith("GCM:"):
        pname = c.partner[4:]
        if pname not in gbook.states:
            return None
        T = T & gbook.states[pname]
    pk = _partner_key(c)
    if pk is not None:
        if pk not in states:
            return None
        on = EV.onsets(states[pk][:, None])[:, 0]
        rec = on.copy()
        for k in range(1, GC.RECENT_W):
            rec[k:] |= on[:-k]
        T = T & rec
    d2 = d.copy()
    d2["split"] = 0
    L = E.labels(d2, data.bucket(d2, tf), int(c.h), cost)
    vec = E.weights(L)[np.flatnonzero(T)].sum(axis=0)
    out = E.directional(E.split_stats(vec, 0), np.array(1.0 if c.dir == "BUY" else -1.0), L["cost"][0])
    return tuple(float(np.asarray(out[k]).ravel()[0]) for k in ("n", "z", "lift", "ret_bp", "cost_bp"))


def main():
    cand = candidates()
    if cand.empty:
        print("aday yok")
        return
    need = set(cand.sid) | {pk[0] for pk in (_partner_key(c) for c in cand.itertuples()) if pk}
    for win in ("past", "old") + TF_WINDOWS:
        run_window(win, need)
    rows = []
    for win in ("past", "old", "recent") + TF_WINDOWS:
        tf = EV.window_tf(win)
        for sym in SYMS:
            own = cand[cand.sym == sym] if win != "recent" else cand[cand.sym != sym]
            if own.empty:
                continue
            d = EV.window_frame(sym, win)
            states = state_arrays(win, sym, len(d), need)
            gbook = indicators.compute(d, tf)
            for c in own.itertuples():
                m = measure(c, d, tf, states, gbook, GC.SPREAD[sym])
                if m is None:
                    continue
                rows.append(dict(src_sym=c.sym, h=c.h, sid=c.sid, script=c.script, state=c.state, partner=c.partner,
                                 dir=c.dir, kanitli=c.kanitli, window=win, tf=tf, sym=sym, bars=len(d), n=m[0], z=m[1],
                                 lift=m[2], ret_bp=m[3], cost_bp=m[4],
                                 n_ok=m[0] >= GC.N_MIN[tf] / 4))
        print(f"{win} ölçüldü", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "results/tekrar_pine.csv", index=False)
    if len(out):
        for win, o in out[out.n_ok].groupby("window"):
            print(win, len(o), "ölçüm; aynı yön z≥1,645:", int((o.z >= GC.Z_PASS).sum()),
                  "ters:", int((o.z <= -GC.Z_PASS).sum()))


if __name__ == "__main__":
    main()
