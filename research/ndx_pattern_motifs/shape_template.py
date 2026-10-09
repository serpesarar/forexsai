"""shape_template.py — şablonun ÇİZGİ (kapanış yolu) düzeyinde benzerleri, ölçekten bağımsız.

Mum-mum aramanın tamamlayıcısı: mum boyları tutmasa da aynı rotayı çizen anlar.
Yol: p = 100·(C/ort(C) − 1); aday en küçük kareler ölçeğiyle (0.1 ≤ a ≤ 10) şablona
oturtulur; mumların ≥ %90'ı ±(rel × şablon yüksekliği) içinde → eşleşme.
Plasebo: getiri işaretleri rastgele (büyüklükler aynı) seri.

Çıktı: results/shape_templates.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine import greedy_nonoverlap, sign_surrogate, template_scan  # noqa: E402
from run_seq import DEFAULT_TEMPLATES, TF  # noqa: E402

RELS = [0.10, 0.15, 0.20]
VIOL_FRAC = 0.10
TOP = 12


def windows(close: np.ndarray, seg: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(close)
    starts = np.arange(0, n - k + 1)
    starts = starts[seg[starts] == seg[starts + k - 1]]
    w = np.lib.stride_tricks.sliding_window_view(close, k)[starts]
    P = 100.0 * (w / w.mean(axis=1, keepdims=True) - 1.0)
    return starts, P.astype(np.float32)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", nargs=4, action="append", metavar=("TF", "BAŞ", "SON", "AD"),
                    help="saatler MT5 sunucu saati (NY+7); verilmezse run_seq varsayılanları")
    a = ap.parse_args()
    tfs = {tf: TF(tf) for tf in ("30m", "15m", "5m", "1m")}
    out = []
    for tf_t, b, e, label in (a.template or DEFAULT_TEMPLATES):
        S = tfs[tf_t]
        s0, s1 = S.pos_of_server(b), S.pos_of_server(e)
        k = s1 - s0 + 1
        Tc = S.c[s0:s1 + 1]
        T = (100.0 * (Tc / Tc.mean() - 1.0)).astype(np.float32)
        H_T = float(T.max() - T.min())
        maxv = int(VIOL_FRAC * k)
        rec = {"label": label, "k": k, "height": round(H_T, 3), "rows": []}
        for tf, X in tfs.items():
            st, P = windows(X.c, X.seg, k)
            _, Ps = windows(sign_surrogate(X.c, X.seg), X.seg, k)
            if tf == tf_t:
                keep = np.abs(st - s0) >= k
            else:
                keep = np.ones(len(st), bool)
            for rel in RELS:
                tol = np.float32(rel * H_T)
                v, rms, sc, cr = template_scan(P, T, tol, maxv, 1)
                vs, rs, _, _ = template_scan(Ps, T, tol, maxv, 1)
                idx = np.where((v <= maxv) & keep)[0]
                pk = greedy_nonoverlap(st, idx, rms[idx], [], k)
                idx_s = np.where((vs <= maxv) & keep)[0]
                n_s = len(greedy_nonoverlap(st, idx_s, rs[idx_s], [], k))
                pk = sorted(pk, key=lambda w: rms[w])
                ends = [int(st[w]) + k - 1 for w in pk]
                fw = X.fwd[ends] if ends else np.array([])
                fw = fw[~np.isnan(fw)]
                rec["rows"].append({
                    "tf": tf, "rel": rel, "count": len(pk), "placebo": n_s,
                    "fwd_up": round(float((fw > 0).mean()), 3) if len(fw) else None,
                    "fwd_n": int(len(fw)),
                    "matches": [{**X.occ(int(st[w]), k), "corr": round(float(cr[w]), 3),
                                 "scale": round(float(sc[w]), 2)} for w in pk[:TOP]],
                    "show": [{**X.candles(int(st[w]), k, ctx=3), "start": X.srv[int(st[w])],
                              "corr": round(float(cr[w]), 2)} for w in pk[:4]],
                })
                print(f"{label[:24]:24} {tf:>4} rel {rel:.2f}: {len(pk):>4} (plasebo {n_s})", flush=True)
        out.append(rec)
    (HERE / "results" / "shape_templates.json").write_text(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
