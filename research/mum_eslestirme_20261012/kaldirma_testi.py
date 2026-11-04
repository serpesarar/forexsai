"""Keşif testi (kullanıcı isteği, 2026-10-12): en yakın eşleşmeleri KALDIRMADAN ÖNCE ve SONRA ileri tahminler tutuyor mu?

Soru: Mum eşleştirmesinin bulduğu geçmiş benzerlerden sonra yön / büyüklük / hedef tahminleri gerçekleşiyor mu ve
tasarımdaki "eşleşme kaldırma" kurallarının her biri sonucu nasıl değiştiriyor? Varsayıma dayalı kural EKLENMEZ;
her kural ayrı bir varyant olarak ölçülür. Büzülme, seans süzgeci, bağlam vb. YOK — çıplak komşu oyu.

Tek zorunlu şart (testin geçerliliği, kural değil): komşunun sonucu karar anında kapanmış olmalı (j + H ≤ q).

Varyant merdiveni:
  V0 ham        : K en yakın komşu (yalnız j + H ≤ q)
  V1 öz-çakışma : + sorgu penceresiyle mum paylaşan pencereler çıkarılır (j ≤ q − kapsam)
  V2 tekil      : V1 + seçilen komşular arası ≥ H bar (aynı tarihsel olayın kaydırılmış kopyaları çıkarılır)
  V3 katı       : V1 + seçilen komşular arası ≥ kapsam + H bar
  V4 kabul      : V2 + mesafe ≤ d_acc (ısınma döneminde rastgele pencere çiftlerinin %5 yüzdeliği); < 20 kalırsa çekimser
Temsiller: ikizA (son 2 mum, 0,2 ATR, L∞), ikizP (son 2 mum, %0,02 — kullanıcı payı), R7 (ham 7 mum, K=50),
           P33 (log-zaman piramidi, K=50). İkizlerde K sınırı yok: pay içindeki tüm eşleşmeler.
Hedefler (ATR birimi, A = önceki 14 barın TR ortalaması): yön sign(r_H); büyüklük |r_H|; yarış ±1 ATR hangisi önce.
Tabanlar: kütüphanedeki koşulsuz yukarı oranı (tüm saatler / aynı UTC saati), aynı saat medyan |r_H|; plasebo = aynı
havuzdan (aynı kaldırma kuralıyla) rastgele komşu, 20 tekrar.
Dönem: her hücrede son 7 ay DOKUNULMADI (ileride protokolün iç test + kalibrasyonu); sorgunun sonucu da bu sınırdan önce
biter. Kütüphane kayan 5 yıl (kullanıcı tanımı). Sorgu saati: 5m–1h için UTC 00/04/08/12/16/20'de kapanan barlar
(TF'ler arası hizalı → çoklu-TF uyum analizi), 4h her 6. bar, 1d her bar.
Veri hijyeni (kural değil): > 4 günlük boşluğu geçen pencere/sonuç geçersiz; XAU/OIL'de yalnız broker satırları.
Çıktı: results/kaldirma/<SYM>_<TF>.parquet (sorgu × ufuk × temsil × varyant).
Çalıştır: python3 research/mum_eslestirme_20261012/kaldirma_testi.py   (8 çekirdek, ~20–40 dk)
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from fizibilite_3_piramit import pyramid  # noqa: E402  (nedensel P33 özellikleri)

OUT = HERE / "results" / "kaldirma"
GF, PM, PB = ROOT / "research/ndx_gate_forge/data", ROOT / "research/ndx_pattern_motifs/data", ROOT / "research/pinbar_20261010/data"
SRC = {
    "NDX": {"5m": PM / "bars_5m.parquet", "15m": PM / "bars_15m.parquet", "30m": GF / "long_30m_utc.parquet", "1h": GF / "long_1h_utc.parquet"},
    "DAX": {"15m": GF / "dax_15m.parquet", "30m": GF / "dax_30m.parquet", "1h": GF / "dax_1h.parquet"},
    "XAU": {tf: PB / f"XAUUSD_{tf}.parquet" for tf in ("5m", "15m", "30m", "1h")},
    "OIL": {tf: PB / f"USOIL_{tf}.parquet" for tf in ("5m", "15m", "30m", "1h")},
}
TF_MIN = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
HS = {"5m": [6, 12, 48], "15m": [4, 16, 32], "30m": [2, 8, 16], "1h": [4, 8, 24], "4h": [3, 6, 30], "1d": [1, 5, 20]}
K = 50
R_PLC = 20
LIB_DAYS = int(365.25 * 5)
RESERVE_DAYS = 213                    # son ~7 ay dokunulmaz
SEG_GAP = pd.Timedelta(days=4)
TWIN_TOL = {"ikizA": 0.20, "ikizP": 0.02}
COV = {"ikizA": 2, "ikizP": 2, "R7": 7, "P33": 33}
VARIANTS = ("V0", "V1", "V2", "V3", "V4")
MIN_ACC = 20


# ─────────────────────────── veri ───────────────────────────
def load_tf(sym: str, tf: str) -> pd.DataFrame:
    if tf in ("4h", "1d"):
        return derive(load_tf(sym, "1h"), tf)
    d = pd.read_parquet(SRC[sym][tf])
    if "src" in d.columns:
        d = d[d.src == "broker"]
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    if sym == "DAX" and tf == "1h":
        d = d[d.ts >= "2020-01-01"].reset_index(drop=True)          # 2020 öncesi seyrek (ME-00)
    return d[["ts", "open", "high", "low", "close"]]


def derive(d1h: pd.DataFrame, tf: str) -> pd.DataFrame:
    """1h → 4h / 1d, broker gün sınırı NY 17:00; gerçek UTC başlangıç zamanıyla."""
    ny = d1h.ts.dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)
    key = ny.dt.floor("1D") if tf == "1d" else ny.dt.floor("4h")
    g = d1h.groupby(key)
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(),
                        "nbar": g.size()})
    out = out[out.nbar >= (3 if tf == "4h" else 20)]
    start_local = pd.DatetimeIndex(out.index) - pd.Timedelta(hours=7)
    ts = start_local.tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward").tz_convert("UTC")
    out = out.assign(ts=ts).dropna(subset=["ts"]).reset_index(drop=True)
    return out[["ts", "open", "high", "low", "close"]]


# ─────────────────────────── yardımcılar ───────────────────────────
def greedy_dedup(cand_sorted: np.ndarray, gap: int, k: int | None, buf: np.ndarray) -> np.ndarray:
    """Mesafe sırasıyla: seçilen komşular arası ≥ gap bar. buf: yeniden kullanılan bool tampon (hep False döner)."""
    kept: list[int] = []; touched = []; n = len(buf)
    for c in cand_sorted.tolist():
        if buf[c]:
            continue
        kept.append(c); a, b = max(0, c - gap + 1), min(n, c + gap)
        buf[a:b] = True; touched.append((a, b))
        if k is not None and len(kept) >= k:
            break
    for a, b in touched:
        buf[a:b] = False
    return np.array(kept, dtype=np.int64)


def race_labels(c, h, l, A, H) -> np.ndarray:
    """1 = +1ATR önce, −1 = −1ATR önce, 0 = H içinde hiçbiri, 2 = aynı barda ikisi (belirsiz), −9 = geçersiz."""
    n = len(c); lab = np.zeros(n, np.int8); done = np.zeros(n, bool)
    up_t, dn_t = c + A, c - A
    for k in range(1, H + 1):
        hh = np.full(n, -np.inf); ll = np.full(n, np.inf)
        hh[:n - k] = h[k:]; ll[:n - k] = l[k:]
        u = (hh >= up_t) & ~done; d = (ll <= dn_t) & ~done
        lab[u & d] = 2; lab[u & ~d] = 1; lab[d & ~u] = -1
        done |= u | d
    lab[np.arange(n) + H >= n] = -9
    return lab


def predict(idx: np.ndarray, r: np.ndarray, race: np.ndarray) -> tuple:
    if len(idx) == 0:
        return 0, np.nan, np.nan, np.nan, np.nan
    rr = r[idx]; rc = race[idx]
    up, dn = (rc == 1).sum(), (rc == -1).sum()
    p_race = up / (up + dn) if up + dn > 0 else np.nan
    return len(idx), float(np.mean(rr > 0)), float(np.median(np.abs(rr))), p_race, float(np.mean(rc == 0))


# ─────────────────────────── hücre ───────────────────────────
def run_cell(sym: str, tf: str) -> str:
    t0 = time.time(); rng = np.random.default_rng(zlib.crc32(f"{sym}|{tf}".encode()))
    d = load_tf(sym, tf)
    ts = d.ts.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(); o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close")); n = len(d)
    gap_after = np.r_[np.diff(ts) > np.timedelta64(4, "D"), False]               # i ile i+1 arasında boşluk
    gcum = np.r_[0, np.cumsum(gap_after)]                            # gcum[i] = 0..i-1 arasındaki boşluk sayısı
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    A = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()
    raw = np.stack([h - o, l - o, c - o], 1)
    pct = np.stack([100 * (h / o - 1), 100 * (l / o - 1), 100 * (c / o - 1)], 1)

    def win_ok(cov: int) -> np.ndarray:                              # pencere [e−cov−14, e] boşluk yok + ATR geçerli
        e = np.arange(n); s = np.maximum(e - cov - 14, 0)
        return (gcum[e] - gcum[s] == 0) & (e >= cov + 14) & np.isfinite(A) & (A > 0)

    feats = {}
    for k_ in (7,):
        F = np.full((n, 3 * k_), np.nan)
        for k in range(k_):
            F[k:, 3 * k:3 * k + 3] = raw[:n - k] / A[k:, None]
        feats["R7"] = F
    feats["P33"] = pyramid(o, h, l, c, A).astype(float)
    tw = np.full((n, 6), np.nan); twp = np.full((n, 6), np.nan)
    for k in range(2):
        tw[k:, 3 * k:3 * k + 3] = raw[:n - k] / A[k:, None]
        twp[k:, 3 * k:3 * k + 3] = pct[:n - k]
    feats["ikizA"], feats["ikizP"] = tw, twp
    valid = {rep: win_ok(COV[rep]) & np.isfinite(feats[rep]).all(1) for rep in feats}

    Hs = HS[tf]; Hmax = max(Hs)
    outc, racel, out_ok = {}, {}, {}
    for H in Hs:
        r = np.full(n, np.nan); r[:n - H] = (c[H:] - c[:n - H]) / A[:n - H]
        ok = np.zeros(n, bool); idx = np.arange(n - H)
        ok[:n - H] = (gcum[idx + H] - gcum[idx] == 0) & np.isfinite(r[:n - H])
        outc[H], racel[H], out_ok[H] = r, race_labels(c, h, l, A, H), ok

    # sorgu takvimi
    te = d.ts + pd.Timedelta(minutes=TF_MIN[tf])
    if tf in ("5m", "15m", "30m", "1h"):
        qmask = ((te.dt.minute == 0) & (te.dt.hour % 4 == 0)).to_numpy()
    elif tf == "4h":
        qmask = (np.arange(n) % 6 == 0)
    else:
        qmask = np.ones(n, bool)
    warm = pd.Timedelta(days=90 if tf == "5m" else 365)
    reserve_ts = d.ts.max() - pd.Timedelta(days=RESERVE_DAYS)
    end_ok = np.zeros(n, bool); end_ok[:n - Hmax] = (d.ts.iloc[Hmax:].reset_index(drop=True) <= reserve_ts).to_numpy()
    qmask &= (d.ts >= d.ts.iloc[0] + warm).to_numpy() & end_ok & valid["P33"] & valid["R7"]
    Q = np.flatnonzero(qmask)
    lo_all = np.searchsorted(ts, ts - np.timedelta64(LIB_DAYS, "D"))
    hour = d.ts.dt.hour.to_numpy()

    # taban önekleri
    pref = {}
    for H in Hs:
        ok = out_ok[H]; upm = ok & (outc[H] > 0)
        rc = racel[H]
        pref[H] = dict(cv=np.r_[0, np.cumsum(ok)], cu=np.r_[0, np.cumsum(upm)],
                       ru=np.r_[0, np.cumsum(ok & (rc == 1))], rd=np.r_[0, np.cumsum(ok & (rc == -1))],
                       hv={b: np.r_[0, np.cumsum(ok & (hour == b))] for b in range(24)},
                       hu={b: np.r_[0, np.cumsum(upm & (hour == b))] for b in range(24)})
    hour_idx = {b: np.flatnonzero(hour == b) for b in range(24)}

    # d_acc: ısınma dönemindeki rastgele çiftlerin %5 yüzdeliği (kNN temsilleri)
    d_acc = {}
    warm_end = Q[0] if len(Q) else n
    for rep in ("R7", "P33"):
        vi = np.flatnonzero(valid[rep][:warm_end])
        if len(vi) > 100:
            a_ = rng.choice(vi, 20000); b_ = rng.choice(vi, 20000); keep = np.abs(a_ - b_) >= COV[rep]
            dd = ((feats[rep][a_[keep]] - feats[rep][b_[keep]]) ** 2).sum(1)
            d_acc[rep] = float(np.quantile(dd, 0.05))
        else:
            d_acc[rep] = np.inf

    rows = []; buf = np.zeros(n, bool)
    ok_idx = {H: np.flatnonzero(out_ok[H]) for H in Hs}
    Fz = {rep: np.nan_to_num(feats[rep], nan=0.0).astype(np.float32) for rep in ("R7", "P33")}
    sq = {rep: (Fz[rep].astype(np.float64) ** 2).sum(1) for rep in Fz}
    CH = 128
    for c0 in range(0, len(Q), CH):
        qs = Q[c0:c0 + CH]
        D2 = {rep: (sq[rep][:, None] + sq[rep][qs][None, :] - 2.0 * (Fz[rep] @ Fz[rep][qs].T).astype(np.float64))
              for rep in Fz}
        for ci, q in enumerate(qs):
            lo = lo_all[q]
            # ikiz eşleşmeleri (sorgu başına bir kez)
            twin_d = {}
            for rep, tol in TWIN_TOL.items():
                if not valid[rep][q]:
                    twin_d[rep] = None; continue
                dd = np.abs(feats[rep] - feats[rep][q]).max(1)
                dd[~valid[rep]] = np.inf
                twin_d[rep] = np.where(dd <= tol, dd, np.inf)
            for H in Hs:
                r, rc, ok = outc[H], racel[H], out_ok[H]
                if not ok[q]:
                    continue
                y, ar, rq = r[q], abs(r[q]), rc[q]
                hi0 = q - H
                if hi0 <= lo + 10:
                    continue
                P = pref[H]; b = hour[q]
                nv = P["cv"][hi0 + 1] - P["cv"][lo]
                p0 = (P["cu"][hi0 + 1] - P["cu"][lo]) / nv if nv else np.nan
                nvh = P["hv"][b][hi0 + 1] - P["hv"][b][lo]
                p0h = (P["hu"][b][hi0 + 1] - P["hu"][b][lo]) / nvh if nvh else np.nan
                ru_, rd_ = P["ru"][hi0 + 1] - P["ru"][lo], P["rd"][hi0 + 1] - P["rd"][lo]
                prace0 = ru_ / (ru_ + rd_) if ru_ + rd_ else np.nan
                hi_b = hour_idx[b]; hb = hi_b[(hi_b >= lo) & (hi_b <= hi0)]; hb = hb[ok[hb]]
                bmed_h = float(np.median(np.abs(r[rng.choice(hb, 1500)]))) if len(hb) else np.nan
                base = dict(sym=sym, tf=tf, H=H, q=int(q), te=te.iloc[q].value, y=y, absr=ar, race=int(rq), p0=p0, p0h=p0h,
                            prace0=prace0, bmed_h=bmed_h)
                for rep in ("ikizA", "ikizP", "R7", "P33"):
                    cov = COV[rep]
                    hi1 = min(hi0, q - cov)
                    if rep in TWIN_TOL:
                        td = twin_d[rep]
                        if td is None:
                            continue
                        dist = td
                    else:
                        if not valid[rep][q]:
                            continue
                        dist = D2[rep][:, ci].copy()
                        dist[~valid[rep]] = np.inf
                    dist = dist.copy(); dist[~ok] = np.inf
                    dist[:lo] = np.inf; dist[hi0 + 1:] = np.inf
                    is_twin = rep in TWIN_TOL
                    d1 = dist.copy(); d1[hi1 + 1:hi0 + 1] = np.inf
                    sel = {}
                    for v, dv in (("V0", dist), ("V1", d1)):
                        fin = np.flatnonzero(np.isfinite(dv))
                        if is_twin or len(fin) <= K:
                            sel[v] = fin
                        else:
                            sel[v] = fin[np.argpartition(dv[fin], K)[:K]]
                    fin = np.flatnonzero(np.isfinite(d1))
                    order = None
                    for v, gap in (("V2", H), ("V3", cov + H)):
                        m = len(fin) if (is_twin or len(fin) <= 4000) else 4000
                        cand = fin[np.argpartition(d1[fin], m - 1)[:m]] if m < len(fin) else fin
                        cand = cand[np.argsort(d1[cand], kind="stable")]
                        idx = greedy_dedup(cand, gap, None if is_twin else K, buf)
                        if not is_twin and len(idx) < K and m < len(fin):
                            if order is None:
                                order = fin[np.argsort(d1[fin], kind="stable")]
                            idx = greedy_dedup(order, gap, K, buf)
                        sel[v] = idx
                    if not is_twin:
                        v4 = sel["V2"][d1[sel["V2"]] <= d_acc[rep]]
                        sel["V4"] = v4 if len(v4) >= MIN_ACC else v4[:0]
                    okH = ok_idx[H]
                    for v, idx in sel.items():
                        nn, pu, med, prace, pnone = predict(idx, r, rc)
                        plc_acc = plc_br = plc_ae = np.nan
                        if nn > 0:                       # plasebo: aynı havuzdan (V0 ya da öz-çakışmasız) aynı sayıda rastgele komşu
                            hi_v = hi0 if v == "V0" else hi1
                            pool = okH[np.searchsorted(okH, lo):np.searchsorted(okH, hi_v + 1)]
                            if len(pool):
                                pick = pool[rng.integers(0, len(pool), size=(R_PLC, min(nn, 500)))]
                                rr = r[pick]; pr = (rr > 0).mean(1)
                                yy = float(y > 0)
                                accs = np.where(pr == 0.5, 0.5, ((pr > 0.5) == (y > 0)).astype(float))
                                plc_acc = float(accs.mean()); plc_br = float(((pr - yy) ** 2).mean())
                                plc_ae = float(np.abs(np.median(np.abs(rr), 1) - ar).mean())
                        rows.append((sym, tf, H, int(q), base["te"], y, ar, int(rq), p0, p0h, prace0, bmed_h,
                                     rep, v, nn, pu, med, prace, pnone, plc_acc, plc_br, plc_ae))
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["sym", "tf", "H", "q", "te", "y", "absr", "race", "p0", "p0h", "prace0", "bmed_h",
                                     "rep", "var", "n", "pu", "med", "prace", "pnone", "plc_acc", "plc_br", "plc_ae"])
    for col in ("y", "absr", "p0", "p0h", "prace0", "bmed_h", "pu", "med", "prace", "pnone", "plc_acc", "plc_br", "plc_ae"):
        df[col] = df[col].astype("float32")
    df.to_parquet(OUT / f"{sym}_{tf}.parquet")
    span = f"{pd.Timestamp(ts[Q[0]]).date()}→{pd.Timestamp(ts[Q[-1]]).date()}" if len(Q) else "-"
    return f"{sym} {tf}: n_bar={n} sorgu={len(Q)} {span} satır={len(df)} d_acc={d_acc} {time.time() - t0:.0f}s"


def main() -> None:
    only = os.environ.get("KT_ONLY")
    cells = [(s, tf) for s in SRC for tf in list(SRC[s]) + ["4h", "1d"]]
    if only:
        keep = {tuple(x.split(":")) for x in only.split(",")}
        cells = [c for c in cells if c in keep]
    cells.sort(key=lambda x: {"1h": 0, "30m": 1, "15m": 2, "5m": 3, "4h": 4, "1d": 5}[x[1]])   # uzunlar önce
    workers = int(os.environ.get("KT_WORKERS", "7"))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_cell, s, tf): (s, tf) for s, tf in cells}
        for f in as_completed(futs):
            try:
                print(f.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                print("HATA", futs[f], repr(e), flush=True)


if __name__ == "__main__":
    main()
