"""Pine mum-mum inceleme hattı: son N bar + tüm scriptlerin tepki konsensüsü + aday scriptlerin tepki şeritleri.

Konsensüs çizgisi yalnız betimleyicidir (sınamada kullanılmaz): her barda etkin "boğa" tepkileri
(long/up/px+/z+/col+) eksi "ayı" tepkileri (short/dn/px-/z-/col-), tepki üreten script sayısına bölünür.
Şeritler: doğrulamayı geçen adayların (ve eşlerinin) durumları; oklar: adayın tetiklendiği barlar.
Kullanım: python pine_inceleme.py [SYM|ALL] [N]
Çıktı: inceleme/<SYM>.html + inceleme/index.html
"""
from __future__ import annotations

import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gosterge_cakisma_20261025"))
sys.path.insert(0, str(HERE))
import eval_scripts as EV  # noqa: E402
import indicators  # noqa: E402
import inceleme as GI  # noqa: E402  (GÇM inceleme şablonu)

OUT = HERE / "inceleme"
SYMS = ("NDX", "DAX", "XAU", "USOIL")
N_DEFAULT = 600
MAX_CANDS = 12
BULL = ("long", "up", "px+", "z+", "col+")
BEAR = ("short", "dn", "px-", "z-", "col-")


def _sign(state: str) -> int:
    suf = state.rsplit("|", 1)[-1]
    return 1 if suf in BULL else (-1 if suf in BEAR else 0)


def _scan(sym: str, n: int, sl: slice, need: set):
    """Tüm durumlardan konsensüs sayıları + istenen (sid, durum) dizileri (yalnız son N bar)."""
    bull = np.zeros(sl.stop - sl.start, np.int32)
    bear = np.zeros_like(bull)
    scripts = set()
    picked = {}
    for p in sorted((HERE / "data/runs/recent").glob("part_*.pkl.gz")):
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                v = r["per_sym"].get(sym)
                if not v or v["status"] != "ok" or not v["states"]:
                    continue
                scripts.add(r["sid"])
                for k, b in v["states"].items():
                    sg = _sign(k)
                    if not sg and (r["sid"], k) not in need:
                        continue
                    a = np.unpackbits(np.frombuffer(b, np.uint8))[:n].astype(bool)
                    if sg > 0:
                        bull += a[sl]
                    elif sg < 0:
                        bear += a[sl]
                    if (r["sid"], k) in need:
                        picked[(r["sid"], k)] = a
    return bull, bear, len(scripts), picked


def build(sym: str, n_show: int = N_DEFAULT) -> str:
    d = EV.window_frame(sym, "recent")
    n = len(d)
    sl = slice(max(0, n - n_show), n)
    cells_p = HERE / "results" / sym / "cells.csv"
    cells = pd.read_csv(cells_p) if cells_p.exists() else pd.DataFrame()
    if len(cells):
        cells["rank"] = cells.kanitli.astype(int) * 2 + cells.val_ok.astype(int)
        cells = cells[cells["rank"] > 0].sort_values(["rank", "KESIF_z"], ascending=False).head(MAX_CANDS)
    need = set()
    for c in cells.itertuples():
        need.add((c.sid, c.state))
        if isinstance(c.partner, str) and c.partner.startswith("R:"):
            need.add(tuple(c.partner[2:].split("|", 1)))
    bull, bear, n_scripts, picked = _scan(sym, n, sl, need)
    book = indicators.compute(d, "1h") if any(isinstance(c.partner, str) and c.partner.startswith("GCM:")
                                              for c in cells.itertuples()) else None
    w = d.iloc[sl]
    bars = [dict(time=int(t.timestamp()), open=float(o), high=float(h), low=float(l), close=float(c))
            for t, o, h, l, c in zip(w.ts, w.open, w.high, w.low, w.close)]
    rows, marks, legend = [], [], []
    for k, c in enumerate(cells.itertuples(), 1):
        lab = f"P{k}"
        a = picked.get((c.sid, c.state))
        if a is None:
            continue
        rows.append(dict(name=f"{lab} {str(c.script)[:28]} · {c.state.split('|', 1)[-1][:24]}",
                         fam="aday", s="".join("+" if x and c.dir == "BUY" else ("-" if x else ".") for x in a[sl])))
        trig = EV.onsets(a[:, None])[:, 0]
        if isinstance(c.partner, str) and c.partner.startswith("GCM:") and book is not None:
            trig = trig & book.states.get(c.partner[4:], np.zeros(n, bool))
        elif isinstance(c.partner, str) and c.partner.startswith("R:"):
            pa = picked.get(tuple(c.partner[2:].split("|", 1)))
            if pa is not None:
                on = EV.onsets(pa[:, None])[:, 0]
                rec = on.copy()
                for j in range(1, 3):
                    rec[j:] |= on[:-j]
                trig = trig & rec
                rows.append(dict(name=f"{lab} eş · {c.partner[2:].split('|', 1)[1][:40]}", fam="eş",
                                 s="".join("*" if x else "." for x in pa[sl])))
        for b in np.flatnonzero(trig[sl]):
            marks.append(dict(i=int(b), id=lab, dir=c.dir))
        legend.append(dict(id=lab, combo=f"{str(c.script)[:40]} · {c.state}" + (f" & {c.partner}" if isinstance(
            c.partner, str) else ""), dir=c.dir, h=int(c.h), kanitli=bool(c.kanitli), val_ok=bool(c.val_ok),
            kesif_z=round(c.KESIF_z, 2), kasa_z=round(c.KASA_z, 2), kasa_hit=round(c.KASA_hit, 3),
            kasa_base=round(c.KASA_base, 3)))
    cons = [dict(time=bars[i]["time"], value=round(float(bull[i] - bear[i]) / max(n_scripts, 1), 4))
            for i in range(len(bars))]
    payload = dict(sym=sym, tf="1h", bars=bars, rows=rows, marks=marks, legend=legend, cons=cons,
                   info=dict(n_states=f"{n_scripts} script", start=str(d.ts.iloc[0]), end=str(d.ts.iloc[-1])))
    html = GI.TEMPLATE.replace("__DATA__", json.dumps(payload, separators=(",", ":")))
    html = html.replace("<title>Gösterge İnceleme Hattı</title>", "<title>Pine İnceleme Hattı</title>")
    html = html.replace("— mum mum gösterge tepkileri`", "— Pine scriptleri, mum mum`")
    html = html.replace("cs.setData(D.bars);", CONSENSUS_JS)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{sym}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)


CONSENSUS_JS = r"""cs.setData(D.bars);
const cl=ch.addLineSeries({priceScaleId:'cons',color:css('--one'),lineWidth:1,title:'konsensüs'});
ch.priceScale('cons').applyOptions({scaleMargins:{top:0.78,bottom:0}});cs.priceScale().applyOptions({scaleMargins:{top:0.04,bottom:0.26}});
cl.setData(D.cons);
document.getElementById('sub').textContent+=` Mavi çizgi (alt bant): ${D.info.n_states} içinde etkin boğa − ayı tepkisi / script sayısı (betimleyici, sınamada kullanılmaz).`;"""


def index() -> str:
    rows = []
    for s in SYMS:
        f = OUT / f"{s}.html"
        if not f.exists():
            continue
        p = HERE / "results" / s / "cells.csv"
        c = pd.read_csv(p) if p.exists() else pd.DataFrame()
        k = int(c.kanitli.sum()) if len(c) else 0
        dg = f"{int(c.val_ok.sum())}/{int(c.val_wrong.sum())}" if len(c) else "–"
        rows.append(f"<tr><td><a href='{f.name}'>{s} 1h</a></td><td>{k}</td><td>{dg}</td></tr>")
    html = ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Pine İnceleme Dizini</title><style>:root{--bg:#fafaf9;--fg:#1c1917;--line:#e7e5e4}"
            "@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--fg:#e7e5e4;--line:#292524}}"
            "body{background:var(--bg);color:var(--fg);font:14px -apple-system,system-ui,sans-serif;margin:16px}"
            "td,th{border-bottom:1px solid var(--line);padding:4px 12px;text-align:left}a{color:inherit}</style></head><body>"
            "<h1>Pine Motoru — mum mum inceleme</h1><p>Her sayfa: son 600 bar (1h), tüm scriptlerin tepki konsensüsü, "
            "doğrulamayı geçen adayların tepki şeritleri ve tetiklendikleri barlar. Sonuçlar: SONUCLAR.md / RAPOR.md.</p>"
            "<table><tr><th>Sembol</th><th>Kanıtlı</th><th>Doğrulama geçen / ters</th></tr>" + "".join(rows) + "</table></body></html>")
    (OUT / "index.html").write_text(html, encoding="utf-8")
    return str(OUT / "index.html")


if __name__ == "__main__":
    a = sys.argv[1:]
    syms = SYMS if not a or a[0] == "ALL" else (a[0],)
    for s in syms:
        print(build(s, int(a[1]) if len(a) > 1 else N_DEFAULT))
    print(index())
