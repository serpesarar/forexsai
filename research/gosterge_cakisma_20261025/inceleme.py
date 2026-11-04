"""Mum-mum inceleme hattı (PROTOCOL §8): son N bar + her göstergenin durum şeridi + kombinasyon işaretleri.

Kullanım: python inceleme.py NDX 1h [N]   |   python inceleme.py ALL
Çıktı: inceleme/<SYM>_<TF>.html (tek dosya, lightweight-charts CDN'den).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import config as C
import data
import engine as E
import indicators

OUT = C.HERE / "inceleme"
N_DEFAULT = 600
MAX_MARK_COMBOS = 8


def _rows(book, sl):
    """Gösterge-durum çiftlerini tek satıra indir: '+' boğa, '-' ayı, '*' tek durum, '.' yok."""
    groups: dict[str, dict] = {}
    for key, arr in book.states.items():
        ind, fam = book.meta[key]
        base, sign = (key[:-1], key[-1]) if key[-1] in "+-" else (key, "*")
        g = groups.setdefault(base, dict(fam=fam, ind=ind, codes=np.full(sl.stop - sl.start, ".", dtype="<U1")))
        g["codes"][arr[sl]] = sign
    order = sorted(groups.items(), key=lambda kv: (kv[1]["fam"], kv[0]))
    return [dict(name=k, fam=v["fam"], s="".join(v["codes"])) for k, v in order]


def _combo_marks(sym, tf, d, book, sl):
    p = C.RES / sym / tf / "cells.csv"
    if not p.exists():
        return [], []
    cells = pd.read_csv(p)
    cells["rank"] = cells.kanitli.astype(int) * 2 + cells.val_ok.astype(int)
    cells = cells.sort_values(["rank", "KESIF_z"], ascending=False).head(MAX_MARK_COMBOS)
    names, Sm, T, Rm, ind = E.matrices(book)
    X = E.x_matrix(Sm, Rm)
    idx = {k: i for i, k in enumerate(names)}
    ns = len(names)
    marks, legend = [], []
    for n_c, (_, c) in enumerate(cells.iterrows()):
        parts = [x.split(":", 1) for x in c["combo"].split(" & ")]
        m = E.thin(T[:, [idx[parts[0][1]]]], int(c["h"]))[:, 0].copy()
        for kind, nm in parts[1:]:
            j = idx[nm]
            m &= Sm[:, j] if kind == "S" else Rm[:, j]
        hits = np.flatnonzero(m[sl])
        label = f"K{n_c + 1}"
        legend.append(dict(id=label, combo=c["combo"], dir=c["dir"], h=int(c["h"]), kanitli=bool(c["kanitli"]),
                           val_ok=bool(c["val_ok"]), kesif_z=round(c["KESIF_z"], 2), kasa_z=round(c["KASA_z"], 2),
                           kasa_hit=round(c["KASA_hit"], 3), kasa_base=round(c["KASA_base"], 3)))
        for b in hits:
            marks.append(dict(i=int(b), id=label, dir=c["dir"]))
    return marks, legend


def build(sym: str, tf: str, n: int = N_DEFAULT) -> str:
    d = data.load(sym, tf)
    book = indicators.compute(d, tf)
    sl = slice(max(0, len(d) - n), len(d))
    w = d.iloc[sl]
    bars = [dict(time=int(t.timestamp()), open=float(o), high=float(h), low=float(l), close=float(c))
            for t, o, h, l, c in zip(w.ts, w.open, w.high, w.low, w.close)]
    rows = _rows(book, sl)
    marks, legend = _combo_marks(sym, tf, d, book, sl)
    meta_p = C.RES / sym / tf / "meta.json"
    meta = json.load(open(meta_p)) if meta_p.exists() else {}
    payload = dict(sym=sym, tf=tf, bars=bars, rows=rows, marks=marks, legend=legend,
                   info=dict(n_states=len(book.states), start=meta.get("start"), end=meta.get("end")))
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{sym}_{tf}.html"
    path.write_text(TEMPLATE.replace("__DATA__", json.dumps(payload, separators=(",", ":"))), encoding="utf-8")
    return str(path)


TEMPLATE = r"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gösterge İnceleme Hattı</title>
<style>
:root{--bg:#fafaf9;--fg:#1c1917;--mut:#78716c;--line:#e7e5e4;--up:#16a34a;--dn:#dc2626;--one:#2563eb;--card:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0c0a09;--fg:#e7e5e4;--mut:#a8a29e;--line:#292524;--up:#22c55e;--dn:#ef4444;--one:#60a5fa;--card:#1c1917}}
:root[data-theme="dark"]{--bg:#0c0a09;--fg:#e7e5e4;--mut:#a8a29e;--line:#292524;--up:#22c55e;--dn:#ef4444;--one:#60a5fa;--card:#1c1917}
body{margin:0;background:var(--bg);color:var(--fg);font:13px/1.4 -apple-system,system-ui,sans-serif}
header{padding:12px 16px;border-bottom:1px solid var(--line)} h1{font-size:16px;margin:0 0 4px} .mut{color:var(--mut)}
#chart{height:360px;margin:0 16px} #wrap{margin:0 16px 16px;border-top:1px solid var(--line)}
#scroll{overflow-y:auto;max-height:62vh} #raster{display:block;width:100%}
#tip{position:fixed;pointer-events:none;background:var(--card);border:1px solid var(--line);padding:8px;max-width:420px;font-size:11px;display:none;z-index:9;max-height:70vh;overflow:hidden}
#legend{margin:8px 16px;font-size:12px} #legend span{display:inline-block;margin:2px 10px 2px 0}
.u{color:var(--up)} .d{color:var(--dn)}
</style></head><body>
<header><h1 id="ttl"></h1><div class="mut" id="sub"></div></header>
<div id="chart"></div><div id="legend"></div>
<div id="wrap"><div id="scroll"><canvas id="raster"></canvas></div></div><div id="tip"></div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
const D=__DATA__;const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
document.getElementById('ttl').textContent=`${D.sym} ${D.tf} — mum mum gösterge tepkileri`;
document.getElementById('sub').textContent=`Son ${D.bars.length} bar · ${D.rows.length} gösterge satırı (${D.info.n_states} durum) · yeşil = boğa durumu, kırmızı = ayı, mavi = tek durum. Oklar: seçilen kombinasyonların ateşlendiği barlar (K1…).`;
document.getElementById('legend').innerHTML=D.legend.map(l=>`<span class="${l.dir==='BUY'?'u':'d'}"><b>${l.id}</b> ${l.dir} h=${l.h} · ${l.combo} · keşif z ${l.kesif_z}, kasa z ${l.kasa_z}, kasa isabet ${(l.kasa_hit*100).toFixed(1)}% / taban ${(l.kasa_base*100).toFixed(1)}%${l.kanitli?' · <b>KANITLI</b>':(l.val_ok?' · doğrulamayı geçti':'')}</span>`).join('')||'<span class="mut">Bu hücre için kombinasyon sonucu yok.</span>';
const el=document.getElementById('chart');
const ch=LightweightCharts.createChart(el,{layout:{background:{color:css('--bg')},textColor:css('--fg')},grid:{vertLines:{color:css('--line')},horzLines:{color:css('--line')}},timeScale:{timeVisible:true},rightPriceScale:{borderColor:css('--line')}});
const cs=ch.addCandlestickSeries({upColor:css('--up'),downColor:css('--dn'),wickUpColor:css('--up'),wickDownColor:css('--dn'),borderVisible:false});
cs.setData(D.bars);
cs.setMarkers(D.marks.map(m=>({time:D.bars[m.i].time,position:m.dir==='BUY'?'belowBar':'aboveBar',color:m.dir==='BUY'?css('--up'):css('--dn'),shape:m.dir==='BUY'?'arrowUp':'arrowDown',text:m.id})).sort((a,b)=>a.time-b.time));
const cv=document.getElementById('raster'),ctx=cv.getContext('2d'),RH=10;let range={from:0,to:D.bars.length-1};
function draw(){const w=cv.parentElement.clientWidth,dpr=devicePixelRatio||1;cv.width=w*dpr;cv.height=D.rows.length*RH*dpr;cv.style.height=(D.rows.length*RH)+'px';ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,D.rows.length*RH);
 const ts=ch.timeScale(),pw=ts.width(),f=Math.max(0,Math.floor(range.from)),t=Math.min(D.bars.length-1,Math.ceil(range.to));
 const bw=Math.max(1,(ts.logicalToCoordinate(f+1)??0)-(ts.logicalToCoordinate(f)??0));
 const cu=css('--up'),cd=css('--dn'),c1=css('--one');ctx.font='9px -apple-system,system-ui,sans-serif';ctx.textBaseline='middle';
 D.rows.forEach((r,y)=>{for(let i=f;i<=t;i++){const s=r.s[i];if(s==='.')continue;const x=ts.logicalToCoordinate(i);if(x===null||x>pw)continue;
  ctx.fillStyle=s==='+'?cu:(s==='-'?cd:c1);ctx.fillRect(x-bw/2,y*RH+1,Math.max(1,bw-0.5),RH-2)}
  ctx.fillStyle=css('--mut');ctx.fillText(r.name,pw+4,y*RH+RH/2)})}
ch.timeScale().subscribeVisibleLogicalRangeChange(r=>{if(r){range=r;draw()}});addEventListener('resize',()=>{ch.applyOptions({width:el.clientWidth});draw()});
const tip=document.getElementById('tip');
function show(i,x,y){if(i<0||i>=D.bars.length){tip.style.display='none';return}const b=D.bars[i];const on=D.rows.filter(r=>r.s[i]!=='.');
 const up=on.filter(r=>r.s[i]==='+').map(r=>r.name),dn=on.filter(r=>r.s[i]==='-').map(r=>r.name),one=on.filter(r=>r.s[i]==='*').map(r=>r.name);
 const mk=D.marks.filter(m=>m.i===i).map(m=>m.id).join(', ');
 tip.innerHTML=`<b>${new Date(b.time*1000).toISOString().replace('T',' ').slice(0,16)} UTC</b> · O ${b.open} H ${b.high} L ${b.low} C ${b.close}${mk?`<br><b>Kombinasyon: ${mk}</b>`:''}<br><span class="u">Boğa (${up.length}):</span> ${up.join(', ')}<br><span class="d">Ayı (${dn.length}):</span> ${dn.join(', ')}${one.length?`<br>Tek: ${one.join(', ')}`:''}`;
 tip.style.display='block';tip.style.left=Math.min(x+14,innerWidth-430)+'px';tip.style.top=Math.min(y+14,innerHeight-200)+'px'}
ch.subscribeCrosshairMove(p=>{if(!p.time||!p.point){tip.style.display='none';return}const i=D.bars.findIndex(b=>b.time===p.time);const r=el.getBoundingClientRect();show(i,r.left+p.point.x,r.top+p.point.y)});
cv.addEventListener('mousemove',e=>{const r=cv.getBoundingClientRect();const lg=ch.timeScale().coordinateToLogical(e.clientX-r.left);show(lg===null?-1:Math.round(lg),e.clientX,e.clientY)});
cv.addEventListener('mouseleave',()=>tip.style.display='none');
ch.timeScale().setVisibleLogicalRange({from:Math.max(0,D.bars.length-200),to:D.bars.length-1});draw();
</script></body></html>"""


def index() -> str:
    """inceleme/index.html: her (sembol, TF) sayfasına bağlantı + hücre özeti."""
    tab = C.RES / "hucre_tablosu.csv"
    g = pd.read_csv(tab) if tab.exists() else pd.DataFrame()
    rows = []
    for s in C.SOURCES:
        for t in C.SOURCES[s]:
            f = OUT / f"{s}_{t}.html"
            if not f.exists():
                continue
            c = g[(g.sym == s) & (g.tf == t)] if len(g) else g
            k = int(c.kanitli.sum()) if len(c) else 0
            dg = f"{int(c.dogr.sum())}/{int(c.dogr_ters.sum())}" if len(c) else "–"
            rows.append(f"<tr><td><a href='{f.name}'>{s} {t}</a></td><td>{k}</td><td>{dg}</td></tr>")
    html = ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Gösterge İnceleme Dizini</title><style>:root{--bg:#fafaf9;--fg:#1c1917;--line:#e7e5e4}"
            "@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--fg:#e7e5e4;--line:#292524}}"
            "body{background:var(--bg);color:var(--fg);font:14px -apple-system,system-ui,sans-serif;margin:16px}"
            "td,th{border-bottom:1px solid var(--line);padding:4px 12px;text-align:left}a{color:inherit}</style></head><body>"
            "<h1>Gösterge Çakışma Motoru — mum mum inceleme</h1><p>Her sayfa: son 600 bar, 353 durumun şeridi, seçilen "
            "kombinasyonların ateşlendiği barlar. Sonuçlar: SONUCLAR.md / RAPOR.md.</p>"
            "<table><tr><th>Sembol TF</th><th>Kanıtlı</th><th>Doğrulama geçen / ters</th></tr>" + "".join(rows) + "</table></body></html>")
    (OUT / "index.html").write_text(html, encoding="utf-8")
    return str(OUT / "index.html")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "INDEX":
        print(index())
    elif args and args[0] == "ALL":
        for s in C.SOURCES:
            for t in C.SOURCES[s]:
                print(build(s, t))
        print(index())
    else:
        print(build(args[0], args[1], int(args[2]) if len(args) > 2 else N_DEFAULT))
