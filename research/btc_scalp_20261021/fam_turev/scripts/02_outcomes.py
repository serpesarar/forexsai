"""Her giriş dakikası e × yön × r × H için braket sonucu (ilk dokunuş motoru) → cache/out_H{H}.npz

Motor: seyrek tablo + ikili sıçrama (fizibilite lib.first_hit ile aynı algoritma), kaba döngüyle öz-sınama yapılır.
Kurallar prereg.md §3: SL = max(19 bp, 1,1×ATR5m); TP = r×SL; aynı bar → SL (kötümser); SL dolumu boşluk-duyarlı + kayma
1 bp (çıkış dakikası |ln c/o| > DISC p99 ise 5 bp); TP seviyeden; zaman çıkışı son bar kapanışı; rollover'da H kısalır.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

KLEV = 6  # 1+2+...+32 = 63 >= 60
LMAX = 60


def sparse(high, low):
    h = np.where(np.isnan(high), -np.inf, high)
    l = np.where(np.isnan(low), np.inf, low)
    n = len(h)
    MX = np.empty((KLEV, n)); MN = np.empty((KLEV, n))
    MX[0], MN[0] = h, l
    for k in range(1, KLEV):
        s = 1 << (k - 1)
        MX[k] = MX[k - 1]; MN[k] = MN[k - 1]
        MX[k, :n - s] = np.maximum(MX[k - 1, :n - s], MX[k - 1, s:])
        MN[k, :n - s] = np.minimum(MN[k - 1, :n - s], MN[k - 1, s:])
    return MX, MN


def first_hit(T, e, thr, L, up):
    n = T.shape[1]
    pos = e.copy()
    end = np.minimum(e + L, n)
    for k in range(KLEV - 1, -1, -1):
        step = 1 << k
        ok = pos + step <= end
        idx = np.where(ok, pos, 0)
        v = T[k][idx]
        nohit = (v < thr) if up else (v > thr)
        pos = np.where(ok & nohit, pos + step, pos)
    kr = pos - e
    inside = pos < end
    kr[~inside] = L
    return kr.astype(np.int16)


def main() -> None:
    B = np.load(C.CACHE / "base.npz")
    o, h, l, c = B["o"], B["h"], B["l"], B["c"]
    bad, hroll, blocked, a5 = B["bad"], B["hroll"], B["blocked"], B["atr5"]
    absr, p99 = B["absr"], float(B["p99_absr"])
    N = C.N
    MX, MN = sparse(h, l)
    e = np.arange(N, dtype=np.int64)
    s_bp = np.maximum(C.SL_MIN_BP, C.SL_ATR * a5 / c * 1e4)
    s_bp = np.concatenate([[np.nan], s_bp[1:]])  # a5 index e zaten girişten önceki kovalar; c yalnız ölçek (önceki kapanış kullan)
    prev_c = np.concatenate([[np.nan], c[:-1]])
    s_bp = np.maximum(C.SL_MIN_BP, C.SL_ATR * a5 / prev_c * 1e4)
    p0 = o
    base_ok = ~np.isnan(p0) & ~np.isnan(prev_c) & ~np.isnan(s_bp) & ~blocked
    base_ok[0] = False
    cb = np.concatenate([[0], np.cumsum(bad)])
    slip_big = (absr > p99)
    res = {}
    # ilk dokunuşlar L=60 ile bir kez
    k = {}
    for d in (1, -1):
        slv = p0 * (1 - d * s_bp / 1e4)
        k[("sl", d)] = first_hit(MN if d == 1 else MX, e, np.nan_to_num(slv, nan=0 if d == 1 else np.inf), LMAX, up=(d == -1))
        for r in C.RS:
            tpv = p0 * (1 + d * r * s_bp / 1e4)
            k[("tp", d, r)] = first_hit(MX if d == 1 else MN, e, np.nan_to_num(tpv, nan=np.inf if d == 1 else 0), LMAX, up=(d == 1))
    # öz-sınama (kaba döngü)
    rng = np.random.default_rng(1)
    samp = rng.choice(np.where(base_ok)[0][:-100], 2000, replace=False)
    mism = 0
    for i in samp:
        for d in (1, -1):
            slv = p0[i] * (1 - d * s_bp[i] / 1e4)
            hh, ll = h[i:i + LMAX], l[i:i + LMAX]
            w = np.where(ll <= slv)[0] if d == 1 else np.where(hh >= slv)[0]
            mism += int((w[0] if len(w) else LMAX) != k[("sl", d)][i])
            tpv = p0[i] * (1 + d * 2.0 * s_bp[i] / 1e4)
            w = np.where(hh >= tpv)[0] if d == 1 else np.where(ll <= tpv)[0]
            mism += int((w[0] if len(w) else LMAX) != k[("tp", d, 2.0)][i])
    print("öz-sınama uyuşmazlık:", mism, "/ 8000")
    assert mism == 0

    for H in C.HS:
        heff = np.minimum(H, hroll).astype(np.int64)
        hi = np.minimum(e + np.maximum(heff, 0), N)
        valid = base_ok & (heff >= 1) & ((cb[hi] - cb[e]) == 0) & (e + heff <= N)
        valid[1:] &= ~bad[:-1]
        tidx = np.clip(e + heff - 1, 0, N - 1)
        c_time = c[tidx]
        out = {"valid": valid, "s_bp": s_bp.astype(np.float32), "heff": heff.astype(np.int16)}
        for d in (1, -1):
            ksl = k[("sl", d)].astype(np.int64)
            slv = p0 * (1 - d * s_bp / 1e4)
            sl_hit = ksl < heff
            hb_sl = np.clip(e + ksl, 0, N - 1)
            sl_fill = np.minimum(slv, o[hb_sl]) if d == 1 else np.maximum(slv, o[hb_sl])
            for r in C.RS:
                ktp = k[("tp", d, r)].astype(np.int64)
                tpv = p0 * (1 + d * r * s_bp / 1e4)
                tp_hit = ktp < heff
                same = sl_hit & tp_hit & (ksl == ktp)
                sl_first = sl_hit & (~tp_hit | (ksl <= ktp))
                tp_first = tp_hit & ~sl_first
                # kötümser
                px = np.where(sl_first, sl_fill, np.where(tp_first, tpv, c_time))
                gb = d * (px / p0 - 1) * 1e4
                xt = np.where(sl_first, -1, np.where(tp_first, 1, 0)).astype(np.int8)
                xo = np.where(sl_first, ksl, np.where(tp_first, ktp, heff - 1)).astype(np.int16)
                slip = np.where(sl_first, np.where(slip_big[hb_sl], 5.0, 1.0), 0.0).astype(np.float32)
                # iyimser: aynı bar → TP; SL seviyeden, kaymasız; giriş = karar barı kapanışı
                sl_first_o = sl_hit & (~tp_hit | (ksl < ktp))
                tp_first_o = tp_hit & ~sl_first_o
                px_o = np.where(sl_first_o, slv, np.where(tp_first_o, tpv, c_time))
                gb_o = d * (px_o / prev_c - 1) * 1e4
                # OHLC-sezgisel: aynı barda açılış hangi seviyeye yakınsa o önce
                ob = o[np.clip(e + ktp, 0, N - 1)]
                tp_near = np.abs(ob - tpv) < np.abs(ob - slv)
                px_h = np.where(same & tp_near, tpv, px)
                gb_h = d * (px_h / p0 - 1) * 1e4
                slip_h = np.where(same & tp_near, 0.0, slip).astype(np.float32)
                key = f"d{d}_r{r}"
                out[f"gb_{key}"] = gb.astype(np.float32)
                out[f"slip_{key}"] = slip
                out[f"xt_{key}"] = xt
                out[f"xo_{key}"] = xo
                out[f"sb_{key}"] = same
                out[f"gbo_{key}"] = gb_o.astype(np.float32)
                out[f"gbh_{key}"] = gb_h.astype(np.float32)
                out[f"sliph_{key}"] = slip_h
                v = valid
                print(f"H{H} {key}: geçerli {v.sum()}, rastgele brüt R ort {np.nanmean(gb[v] / s_bp[v]):+.4f}, "
                      f"net PEP {np.nanmean((gb[v] - 1.85 - slip[v]) / s_bp[v]):+.4f}, aynı-bar {same[v].mean():.4%}, "
                      f"TP {(xt[v] == 1).mean():.3f} SL {(xt[v] == -1).mean():.3f}")
        np.savez(C.CACHE / f"out_H{H}.npz", **out)


if __name__ == "__main__":
    main()
