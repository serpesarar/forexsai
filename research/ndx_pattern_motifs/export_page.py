"""export_page.py — seq_scan.json → HTML atlas + TF başına tembel yüklenen data_<tf>.json.

Kullanım: python3 export_page.py <şablon.html> <çıktı.html> [bulgular.json]
Bulgular (Türkçe madde listesi) ayrı JSON'dan gelir; yoksa yalnız özet istatistik basılır.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = {"1m": "Dukascopy 2025 + broker 2026", "5m": "1m'den türetildi",
       "15m": "Pepperstone broker", "30m": "Pepperstone broker"}
SHOW_OCC = 5
MAX_OCC = 30


def _r(x, nd=3):
    return [[round(v, nd) for v in row] for row in x]


def compact(o: dict) -> dict:
    def n_show(k: int) -> int:
        return 4 if k <= 10 else 3 if k <= 30 else 2

    def trim(m: dict) -> dict:
        """Tembel yüklenen TF dosyası için sıkı biçim: örnekler dizi, OHLC binde-tamsayı."""
        occ = [[x["start"], x["end"], x["price"], x["fwd"], x["rms"], x.get("matched", m["k"])]
               for x in m["occurrences"][:MAX_OCC]]
        show = [{"lead": s["lead"], "k": s["k"], "start": s["start"], "matched": s.get("matched", m["k"]),
                 "ohlc": [[int(round(v * 1000)) for v in row] for row in s["ohlc"]]}
                for s in m["show"][:n_show(m["k"])]]
        return {**{k: m[k] for k in ("tol", "k", "count", "placebo_top", "name", "composition",
                                     "dense100", "fwd") if k in m},
                "q": m.get("q", 1.0), "occ": occ, "show": show}

    tfs, per_tf = [], {}
    for t in o["tfs"]:
        ex = t.get("exact") or {k: t[k] for k in ("tols", "grid", "motifs", "longest") if k in t}
        entry = {"tf": t["tf"], "exact": {"tols": ex["tols"], "grid": ex["grid"], "longest": ex.get("longest", []),
                                          "n_motifs": len(ex["motifs"])}}
        per_tf[t["tf"]] = {"exact": [trim(m) for m in ex["motifs"]], "partial": []}
        if t.get("partial"):
            P = t["partial"]
            entry["partial"] = {"tols": P["tols"], "qs": P["qs"], "grid": P["grid"],
                                "counts_only": bool(P.get("counts_only")),
                                "n_by_q": {str(q): sum(1 for m in P["motifs"] if m["q"] == q) for q in P["qs"]}}
            per_tf[t["tf"]]["partial"] = [trim(m) for m in P["motifs"]]
        tfs.append(entry)
    tpls = []
    for T in o["templates"]:
        res = []
        for r in T["results"]:
            rr = {"tf": r["tf"]}
            for mode in ("abs", "atr"):
                rr[mode] = [{**x, "show": [{**s, "ohlc": _r(s["ohlc"])} for s in x["show"]]} for x in r[mode]]
            res.append(rr)
        tpls.append({**{k: T[k] for k in ("label", "tf", "start", "end", "k", "name", "composition")},
                     "candles": {**T["candles"], "ohlc": _r(T["candles"]["ohlc"])}, "results": res})
    cov = [{"tf": t["tf"], "n": t["n"], "span": t["span"], "src": SRC[t["tf"]]} for t in o["tfs"]]
    order = {"1m": 0, "5m": 1, "15m": 2, "30m": 3}
    shapes = [{**x, "rows": [{**r, "show": [{**s, "ohlc": _r(s["ohlc"])} for s in r["show"]]} for r in x["rows"]]}
              for x in o["shape_templates"]]
    return per_tf, {"config": o["config"], "generated": o["generated"], "templates": tpls, "shape_templates": shapes,
            "tfs": sorted(tfs, key=lambda t: order[t["tf"]]), "coverage": sorted(cov, key=lambda c: order[c["tf"]])}


def summary(o: dict) -> None:
    """Bulgu metni yazmak için özet sayılar (birebir + kısmi)."""
    for t in o["tfs"]:
        ex = t.get("exact") or t
        blocks = [("birebir", 1.0, ex["grid"], ex["motifs"])]
        if t.get("partial"):
            for q in t["partial"]["qs"]:
                blocks.append((f"%{int(q * 100)}", q, [g for g in t["partial"]["grid"] if g["q"] == q],
                               [m for m in t["partial"]["motifs"] if m["q"] == q]))
        for lab, q, grid, motifs in blocks:
            g = [x for x in grid if x["top"] and x["placebo_top"]]
            ratios = [x["top"][0] / x["placebo_top"] for x in g]
            kmax = max([x["k"] for x in grid if x["top"]], default=0)
            print(f"{t['tf']:>4} {lab:8} modeller={len(motifs):4} en uzun k(tekrarlı)={kmax:3} "
                  f"gerçek/plasebo medyan={np.median(ratios) if ratios else float('nan'):.2f} "
                  f"aralık={min(ratios, default=0):.2f}–{max(ratios, default=0):.2f}")
            tols = sorted({x["tol"] for x in grid})
            for tol in tols:
                row = [x for x in grid if x["tol"] == tol]
                print("      pay", tol, " ".join(f"k{x['k']}:{(x['top'] or [0])[0]}/{x['placebo_top']}" for x in row))
            big = [m for m in motifs if m["fwd"]["n"] >= 30]
            if big:
                d = [m["fwd"]["up"] - m["fwd"]["base_up"] for m in big]
                print(f"      n≥30: {len(big)} motif, ileri yön farkı ort {np.mean(d):+.3f} mutlak {np.mean(np.abs(d)):.3f}")


def main() -> None:
    o = json.loads((HERE / "results" / "seq_scan.json").read_text())
    tp = HERE / "results" / "seq_templates.json"      # şablon araması (plasebo öz-dışlama düzeltmeli)
    if tp.exists():
        o["templates"] = json.loads(tp.read_text())["templates"]
    sp = HERE / "results" / "shape_templates.json"
    o["shape_templates"] = json.loads(sp.read_text()) if sp.exists() else []
    if len(sys.argv) < 3:
        summary(o)
        return
    tpl, out = Path(sys.argv[1]), Path(sys.argv[2])
    extra = json.loads(Path(sys.argv[3]).read_text()) if len(sys.argv) > 3 else {}
    per_tf, base = compact(o)
    data = {**base, **extra}
    html = tpl.read_text().replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out.write_text(html)
    print(f"{out} ({len(html) / 1e6:.2f} MB)")
    for tf, block in per_tf.items():                 # sayfanın yanında yayınlanan, tembel yüklenen dosyalar
        p = out.parent / f"data_{tf}.json"
        p.write_text(json.dumps(block, ensure_ascii=False, separators=(",", ":")))
        print(f"  {p.name} ({p.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
