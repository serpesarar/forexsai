"""run_seq.py — NASDAQ'da mum-mum benzerlikle tekrar eden diziler + örnek şablon araması.

Kullanım:
  python3 run_seq.py                       # 4 TF tam tarama + varsayılan şablonlar
  python3 run_seq.py --tfs 15m 30m         # yalnız seçili TF'ler
  python3 run_seq.py --template 15m "2026-09-16 20:30" "2026-09-16 23:00" "Flaş-V çekirdeği"
      (şablon saatleri MT5 SUNUCU saati = New York + 7s; birden çok --template verilebilir)

Çıktı: results/seq_scan.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from naming import name_candles  # noqa: E402
from seq_engine import (ELIG_RATIO, ELIG_RATIO_PARTIAL, KS, KS_PARTIAL, N_CHUNK, QS_PARTIAL,  # noqa: E402
                        breaks, candle_features, diag_counts, diag_counts_partial, eligibility_matrix,
                        eligible_starts, greedy_spaced, max_in_window, mirror_placebo, need_table,
                        run_lengths, select_motifs, select_partial, seq_matches, template_counts)

# Birebir (her mum) — pay ≤ medyan mum boyu/3 kuralı geniş paylarda yalnız büyük mumları bırakır
TOLS = {"1m": [0.005, 0.0075, 0.01, 0.015, 0.02],
        "5m": [0.01, 0.015, 0.02, 0.03, 0.05, 0.07],
        "15m": [0.02, 0.03, 0.05, 0.07, 0.10, 0.15],
        "30m": [0.03, 0.05, 0.07, 0.10, 0.15, 0.20]}
# Kısmi (mumların ≥ %90 / %80 / %70'i) — 10–100 mumluk uzun diziler
TOLS_PARTIAL = {"1m": [0.01],                # %0,02 koşusu zaman aşımına uğradı (Mac uykusu olabilir) — gerekirse ekle
                "5m": [0.02, 0.03, 0.05],
                "15m": [0.03, 0.05, 0.07],
                "30m": [0.05, 0.07, 0.10]}
TPL_ABS = [0.02, 0.03, 0.05, 0.07, 0.10]       # şablonun kendi TF'inde (% pay)
TPL_ATR = [0.10, 0.15, 0.20, 0.25, 0.33]       # tüm TF'lerde (ortalama mum boyu birimi)
ATR_N = 20
FWD = 10                 # motif sonrası bakılan bar
CTX = 5                  # gösterimde motifin önü/arkası bağlam mumu
SHOW_OCC = 8
MAX_OCC = 60
K_TOP = 6
DEFAULT_TEMPLATES = [
    ("15m", "2026-09-16 03:00", "2026-09-17 04:45", "Ekran görüntüsündeki 100 mumluk alan"),
    ("15m", "2026-09-16 21:00", "2026-09-17 02:45", "Flaş çöküş + V dönüş çekirdeği"),
]


def to_server(ts: pd.Series) -> pd.Series:
    """MT5 sunucu saati (Pepperstone NAS100) = New York yerel + 7 saat."""
    return ts.dt.tz_convert("America/New_York").dt.tz_localize(None) + pd.Timedelta(hours=7)


class TF:
    def __init__(self, tf: str):
        d = pd.read_parquet(HERE / "data" / f"bars_{tf}.parquet").reset_index(drop=True)
        self.tf, self.d = tf, d
        self.o, self.h, self.l, self.c = (d[x].to_numpy(float) for x in ("open", "high", "low", "close"))
        self.seg = d.seg.to_numpy()
        self.X = candle_features(self.o, self.h, self.l, self.c)
        self.brk = breaks(self.seg)
        self.Xp = mirror_placebo(self.X)
        rng = pd.Series(self.X[:, 0] - self.X[:, 1])
        atr = rng.groupby(self.seg).transform(lambda s: s.rolling(ATR_N, min_periods=5).mean().shift(1))
        atr = atr.bfill().to_numpy()
        self.Xa = (self.X / atr[:, None]).astype(np.float32)
        self.Xap = mirror_placebo(self.Xa)
        self.srv = to_server(d.ts).dt.strftime("%Y-%m-%d %H:%M").to_numpy()
        self.fwd = self._fwd()

    def _fwd(self) -> np.ndarray:
        n = len(self.c)
        tgt = np.arange(n) + FWD
        ok = tgt < n
        ok[ok] &= self.seg[tgt[ok]] == self.seg[np.arange(n)[ok]]
        out = np.full(n, np.nan)
        out[ok] = 100 * (self.c[tgt[ok]] / self.c[np.arange(n)[ok]] - 1)
        return out

    def pos_of_server(self, s: str) -> int:
        hit = np.where(self.srv == s)[0]
        if not len(hit):
            raise SystemExit(f"{self.tf}: sunucu saati {s} veride yok")
        return int(hit[0])

    def candles(self, s: int, k: int, ctx: int = CTX) -> dict:
        a, b = max(0, s - ctx), min(len(self.c), s + k + ctx)
        base = self.o[s]
        arr = np.stack([self.o[a:b], self.h[a:b], self.l[a:b], self.c[a:b]], 1)
        return {"ohlc": np.round(100 * (arr / base - 1), 4).tolist(), "lead": s - a, "k": k}

    def occ(self, s: int, k: int, **kw) -> dict:
        end = s + k - 1
        f = self.fwd[end]
        return {"start": self.srv[s], "end": self.srv[end], "price": round(float(self.o[s]), 1),
                "fwd": None if np.isnan(f) else round(float(f), 3), **kw}


def fwd_summary(T: TF, ends: list[int], base_mask: np.ndarray | None = None) -> dict:
    v = T.fwd[np.array(ends, int)] if ends else np.array([])
    v = v[~np.isnan(v)]
    b = T.fwd if base_mask is None else T.fwd[base_mask]
    b = b[~np.isnan(b)]
    out = {"n": int(len(v)), "base_up": round(float((b > 0).mean()), 3)}
    if len(v):
        out.update(up=round(float((v > 0).mean()), 3), mean=round(float(v.mean()), 4))
    return out


def motif_block(T: TF, m: dict, tol: float, sur_top: int, q: float = 1.0) -> dict:
    s, k = m["start"], m["k"]
    nm = name_candles(np.stack([T.o[s:s + k], T.h[s:s + k], T.l[s:s + k], T.c[s:s + k]], 1))
    matched = m.get("matched", [k] * len(m["occ"]))
    occ_sorted = sorted(zip(m["occ"], m["rms"], matched), key=lambda x: x[0])
    return {
        "tf": T.tf, "tol": tol, "q": q, "k": k, "count": m["count"], "placebo_top": sur_top,
        "name": nm["name"], "types": nm["types"], "composition": nm["composition"],
        "dense100": max_in_window(m["occ"], 100),
        "occurrences": [T.occ(o, k, rms=r, matched=int(mt)) for o, r, mt in occ_sorted[:MAX_OCC]],
        "show": [{**T.candles(o, k), "start": T.srv[o], "matched": int(mt)}
                 for o, mt in list(zip(m["occ"], matched))[:SHOW_OCC]],
        "fwd": fwd_summary(T, [o + k - 1 for o in m["occ"]]),
    }


def longest_repeat(T: TF, cands: list[int], k0: int, tol: float, X: np.ndarray) -> tuple[int, int, int]:
    """Son ızgara uzunluğundaki motif adaylarını mum mum uzatarak en uzun tekrar."""
    best = (k0, cands[0] if cands else -1, -1)
    for s in cands[:40]:
        k = k0
        while True:
            el = eligible_starts(X, T.brk, k + 1, tol)
            if not el[s]:
                break
            ts, _ = seq_matches(X, T.brk, s, k + 1, np.float32(tol))
            ts = ts[el[ts]]
            if not len(ts):
                break
            k += 1
            if k > best[0]:
                best = (k, s, int(ts[0]))
    return best


def discover_exact(T: TF) -> dict:
    """Birebir: k mumun HER BİRİ pay içinde."""
    out = {"tols": TOLS[T.tf], "elig_ratio": ELIG_RATIO, "grid": [], "motifs": [], "longest": []}
    for tol in TOLS[T.tf]:
        t0 = time.time()
        C, _ = diag_counts(T.X, T.brk, np.float32(tol), KS, N_CHUNK)
        Cp, _ = diag_counts(T.Xp, T.brk, np.float32(tol), KS, N_CHUNK)
        last_k, last_cands = None, []
        for kk, k in enumerate(KS):
            k = int(k)
            el = eligible_starts(T.X, T.brk, k, tol)
            elp = eligible_starts(T.Xp, T.brk, k, tol)
            ms = select_motifs(T.X, T.brk, C[:, kk], k, tol, el, k_top=K_TOP)
            mp = select_motifs(T.Xp, T.brk, Cp[:, kk], k, tol, elp, k_top=1)
            sur = mp[0]["count"] if mp else 0
            out["grid"].append({
                "tol": tol, "k": k, "n_elig": int(el.sum()),
                "with_repeat": int((el & (C[:, kk] > 0)).sum()),
                "placebo_with_repeat": int((elp & (Cp[:, kk] > 0)).sum()),
                "top": [m["count"] for m in ms], "placebo_top": sur})
            for m in ms:
                out["motifs"].append(motif_block(T, m, tol, sur))
            if ms:
                last_k, last_cands = k, [m["start"] for m in ms]
            if not ms and not mp:
                break
        if last_k:
            L, s, t = longest_repeat(T, last_cands, last_k, tol, T.X)
            out["longest"].append({"tol": tol, "k": L, "a": T.srv[s], "b": T.srv[t] if t >= 0 else None})
        g = [x for x in out["grid"] if x["tol"] == tol]
        print(f"  {T.tf} pay %{tol:<6} " + " ".join(f"k{x['k']}:{(x['top'] or [0])[0]}/{x['placebo_top']}" for x in g)
              + f"  ({time.time() - t0:.0f}s)", flush=True)
    return out


def partial_for_tol(T: TF, tol: float, run: np.ndarray, need: np.ndarray) -> tuple[list, list]:
    """Tek pay için kısmi tarama → (ızgara satırları, motif blokları)."""
    t0 = time.time()
    E = eligibility_matrix(T.X, T.brk, KS_PARTIAL, tol, ELIG_RATIO_PARTIAL)
    Ep = eligibility_matrix(T.Xp, T.brk, KS_PARTIAL, tol, ELIG_RATIO_PARTIAL)
    C = diag_counts_partial(T.X, run, E, np.float32(tol), KS_PARTIAL, need, N_CHUNK)
    Cp = diag_counts_partial(T.Xp, run, Ep, np.float32(tol), KS_PARTIAL, need, N_CHUNK)
    grid, motifs, line = [], [], []
    for kk, k in enumerate(KS_PARTIAL):
        k = int(k)
        el, elp = E[:, kk].astype(bool), Ep[:, kk].astype(bool)
        any_hit = False
        for qq, q in enumerate(QS_PARTIAL):
            nd = int(need[kk, qq])
            ms = select_partial(T.X, run, C[:, kk, qq], k, tol, nd, el, k_top=K_TOP)
            mp = select_partial(T.Xp, run, Cp[:, kk, qq], k, tol, nd, elp, k_top=1)
            sur = mp[0]["count"] if mp else 0
            grid.append({"tol": tol, "k": k, "q": q, "need": nd, "n_elig": int(el.sum()),
                         "top": [m["count"] for m in ms], "placebo_top": sur})
            motifs.extend(motif_block(T, m, tol, sur, q) for m in ms)
            any_hit |= bool(ms or mp)
            line.append(f"k{k}@{int(q * 100)}:{(ms[0]['count'] if ms else 0)}/{sur}")
        if not any_hit:
            break
    print(f"  {T.tf} kısmi pay %{tol:<6} uygun(k10)={int(E[:, 0].sum())} " + " ".join(line)
          + f"  ({time.time() - t0:.0f}s)", flush=True)
    return grid, motifs


def discover_partial(T: TF, tols: list[float], prev: dict | None, save) -> dict:
    """Kısmi: k mumun en az q'su pay içinde (ilk mum tutmalı). Uzun diziler için.

    prev verilirse aynı payların eski sonuçları değiştirilir, diğerleri korunur; her pay
    bitince save() çağrılır (uzun koşu kesilirse bitenler kaybolmaz).
    """
    need = need_table(KS_PARTIAL, QS_PARTIAL)
    run = run_lengths(T.brk)
    out = prev or {"tols": [], "grid": [], "motifs": []}
    out.update(qs=list(QS_PARTIAL), elig_ratio=ELIG_RATIO_PARTIAL)
    out.pop("counts_only", None)
    out.pop("note", None)
    for tol in tols:
        grid, motifs = partial_for_tol(T, tol, run, need)
        out["grid"] = [g for g in out["grid"] if g["tol"] != tol] + grid
        out["motifs"] = [m for m in out["motifs"] if m["tol"] != tol] + motifs
        out["tols"] = sorted(set(out["tols"]) | {tol})
        save(out)
    return out


def template_search(T: TF, tpl: dict, src: TF) -> dict:
    """Şablona mum-mum benzerlik: tam eşleşme sayısı + en iyi kısmi eşleşmeler (kaç mum tutuyor)."""
    s0, k = tpl["pos"], tpl["k"]
    same = T.tf == src.tf
    res = {"tf": T.tf, "abs": [], "atr": []}
    modes = (("abs", TPL_ABS, src.X, T.X, T.Xp), ("atr", TPL_ATR, src.Xa, T.Xa, T.Xap))
    for mode, grid, Xsrc, X, Xp in modes:
        if mode == "abs" and not same:
            continue
        Tm = np.ascontiguousarray(Xsrc[s0:s0 + k])
        for tol in grid:
            sc = template_counts(X, T.brk, Tm, np.float32(tol))
            scp = template_counts(Xp, T.brk, Tm, np.float32(tol))
            if same:                                         # kendisi ve kaydırmaları (plaseboda da:
                sc[max(0, s0 - k + 1):s0 + k] = -1          # aynalanmamış mumları kendini sayar)
                scp[max(0, s0 - k + 1):s0 + k] = -1
            valid = sc >= 0
            idx = np.where(valid)[0]
            # en iyi kısmi eşleşmeler (çakışmasız)
            order_key = -(sc[idx].astype(float))
            top = greedy_spaced(idx, order_key, k, np.empty(0, np.int64))[:12]
            full = idx[sc[idx] == k]
            n_full = len(greedy_spaced(full, np.zeros(len(full)), k, np.empty(0, np.int64)))
            vp = scp[scp >= 0]
            res[mode].append({
                "tol": tol, "full": n_full,
                "best": int(sc[top[0]]) if top else 0,
                "placebo_best": int(vp.max()) if len(vp) else 0,
                "mean_match": round(float(sc[valid].mean() / k), 4),
                "placebo_mean_match": round(float(vp.mean() / k), 4) if len(vp) else 0,
                "matches": [{**T.occ(t, k), "matched": int(sc[t])} for t in top],
                "show": [{**T.candles(t, k, ctx=3), "start": T.srv[t], "matched": int(sc[t])} for t in top[:4]],
            })
        print(f"  şablon[{tpl['label'][:22]}] {T.tf} {mode}: " +
              " ".join(f"%{x['tol']}→tam {x['full']} en iyi {x['best']}/{k} (plasebo {x['placebo_best']})"
                       for x in res[mode]), flush=True)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tfs", nargs="+", default=["30m", "15m", "5m", "1m"])
    ap.add_argument("--template", nargs=4, action="append", metavar=("TF", "BAŞ", "SON", "AD"))
    ap.add_argument("--no-discover", action="store_true")
    ap.add_argument("--out", default="seq_scan.json")
    ap.add_argument("--partial-tols", nargs="+", type=float,
                    help="kısmi modda yalnız bu paylar (eski sonuçlarla birleştirilir)")
    ap.add_argument("--modes", nargs="+", default=["templates", "exact", "partial"],
                    help="templates | exact | partial — çıktı dosyası varsa diğer modlar korunur")
    a = ap.parse_args()
    tpls_raw = a.template or DEFAULT_TEMPLATES
    cache: dict[str, TF] = {}

    def get(tf: str) -> TF:
        if tf not in cache:
            cache[tf] = TF(tf)
        return cache[tf]

    path = HERE / "results" / a.out
    out = json.loads(path.read_text()) if path.exists() else {"templates": [], "tfs": []}
    for e in out["tfs"]:                       # eski biçim: birebir alanları üst düzeydeydi
        if "grid" in e:
            e["exact"] = {k: e.pop(k) for k in ("tols", "elig_ratio", "grid", "motifs", "longest") if k in e}
    out["generated"] = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC")
    out["config"] = {"tols": TOLS, "tols_partial": TOLS_PARTIAL, "tpl_abs": TPL_ABS, "tpl_atr": TPL_ATR,
                     "ks": KS.tolist(), "ks_partial": KS_PARTIAL.tolist(), "qs_partial": list(QS_PARTIAL),
                     "elig_ratio": ELIG_RATIO, "elig_ratio_partial": ELIG_RATIO_PARTIAL,
                     "fwd": FWD, "atr_n": ATR_N, "k_top": K_TOP}
    templates = []
    if "templates" in a.modes:
        for tf, b, e, label in tpls_raw:
            S = get(tf)
            s0, s1 = S.pos_of_server(b), S.pos_of_server(e)
            k = s1 - s0 + 1
            nm = name_candles(np.stack([S.o[s0:s1 + 1], S.h[s0:s1 + 1], S.l[s0:s1 + 1], S.c[s0:s1 + 1]], 1))
            templates.append({"tf": tf, "start": b, "end": e, "label": label, "pos": s0, "k": k,
                              "name": nm["name"], "composition": nm["composition"],
                              "candles": S.candles(s0, k, ctx=0), "results": []})
            print(f"Şablon '{label}': {tf} {b} → {e} ({k} mum) ad={nm['name']}")
        out["templates"] = templates
    for tf in a.tfs:
        print(f"== {tf}", flush=True)
        T = get(tf)
        for tpl in templates:
            tpl["results"].append(template_search(T, tpl, get(tpl["tf"])))
        entry = next((e for e in out["tfs"] if e["tf"] == tf), None)
        if entry is None:
            entry = {"tf": tf}
            out["tfs"].append(entry)
        entry.update(n=int(len(T.c)), span=[T.srv[0], T.srv[-1]])
        if "exact" in a.modes:
            entry["exact"] = discover_exact(T)
        if "partial" in a.modes:
            tols = a.partial_tols or TOLS_PARTIAL[tf]
            prev = entry.get("partial") if a.partial_tols else None

            def save(block: dict, entry: dict = entry) -> None:
                entry["partial"] = block
                path.write_text(json.dumps(out, ensure_ascii=False))

            entry["partial"] = discover_partial(T, tols, prev, save)
        path.write_text(json.dumps(out, ensure_ascii=False))
    print("yazıldı:", path)


if __name__ == "__main__":
    main()
