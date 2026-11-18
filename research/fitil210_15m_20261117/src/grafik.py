"""grafik.py — doğrulama grafikleri (SVG, bağımlılıksız).

Her grafik iki panel: üstte 3,5 saatlik (210m) mumlar — olay mumu sarı zeminli, alt/üst fitil ve gövde yüzdeleri iki beslemede
(Dukascopy + kullanıcının broker'ı MT5) yazılı; altta 15m mumlar — ana mum çizgileri (BT/BB/%48/%50/%25) ve işlemler.

Çıktılar (results/): grafik_17kasim_{W14,ANA}.svg, grafik_ornek_{1..6}.svg, grafik_eski_ornek_{1,2,4,5}.svg,
grafikler.html (hepsi gömülü), galeri.html (rastgele 24 olayın 210m görünümü).
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

import kurallar as K
import veri

W, PAD_L, PAD_R = 980, 10, 90
UP, DN, TXT, GRID, HL = "#1a9e86", "#e0524f", "#333", "#e6e6e6", "#fff4c2"
LINE_COL = {"BT": "#d62728", "BB": "#d62728", "L50": "#9467bd", "L48": "#ff7f0e", "L25": "#2ca02c"}
STRAT_COL = {"S1": "#1f77b4", "S2": "#17becf", "S3": "#e377c2", "S4": "#8c564b"}
OLD_EXAMPLES = {1: "2022-05-23 07:00", 2: "2022-12-07 07:00", 4: "2026-04-08 10:30", 5: "2022-07-12 14:00"}


def fmt(t: int, f: str = "%m-%d %H:%M") -> str:
    return pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(veri.NY).strftime(f)


def pct(x: float) -> str:
    return f"%{x:.2f}".replace(".", ",")


class Panel:
    """Bir fiyat paneli: y ölçeği + mum çizimi."""

    def __init__(self, y0: float, h: float, lo: float, hi: float, n: int, w: float = W, x0: float = 0):
        pad = (hi - lo) * 0.04
        self.y0, self.h, self.lo, self.hi, self.n, self.w, self.x0 = y0, h, lo - pad, hi + pad, n, w, x0
        self.cw = (w - PAD_L - PAD_R) / max(n, 1)

    def y(self, p: float) -> float:
        return self.y0 + (self.hi - p) / (self.hi - self.lo) * self.h

    def x(self, i: float) -> float:
        return self.x0 + PAD_L + (i + 0.5) * self.cw

    def grid(self, out: list[str], k: int = 5) -> None:
        for j in range(k + 1):
            p = self.lo + (self.hi - self.lo) * j / k
            out.append(f'<line x1="{self.x0 + PAD_L}" x2="{self.x0 + self.w - PAD_R}" y1="{self.y(p):.1f}" y2="{self.y(p):.1f}" '
                       f'stroke="{GRID}"/><text x="{self.x0 + self.w - PAD_R + 4}" y="{self.y(p) + 4:.1f}" fill="#888">{p:.1f}</text>')

    def candles(self, out: list[str], df: pd.DataFrame, every: int, tf: str, hl: int | None = None) -> None:
        for i, r in enumerate(df.itertuples()):
            if hl is not None and i == hl:
                out.append(f'<rect x="{self.x(i) - self.cw / 2:.1f}" y="{self.y0:.1f}" width="{self.cw:.1f}" height="{self.h:.1f}" fill="{HL}"/>')
            col = UP if r.close >= r.open else DN
            out.append(f'<line x1="{self.x(i):.1f}" x2="{self.x(i):.1f}" y1="{self.y(r.high):.1f}" y2="{self.y(r.low):.1f}" stroke="{col}" stroke-width="1.2"/>')
            top, bot = self.y(max(r.open, r.close)), self.y(min(r.open, r.close))
            out.append(f'<rect x="{self.x(i) - self.cw * 0.35:.1f}" y="{top:.1f}" width="{self.cw * 0.7:.1f}" height="{max(bot - top, 1):.1f}" fill="{col}"/>')
            if i % every == 0:
                out.append(f'<text x="{self.x(i):.1f}" y="{self.y0 + self.h + 14:.1f}" fill="#888" text-anchor="middle">{fmt(r.t)}</text>')


def wick_note(e: pd.Series, m: pd.Series | None, feed: str = "Dukascopy", h: pd.Series | None = None) -> str:
    s = (f"{feed}: alt fitil {pct(e.lw_pct)} ({min(e.open, e.close) - e.low:.1f} puan) · üst fitil {pct(e.uw_pct)} · gövde {pct(e.gv_pct)}")
    if m is not None:
        s += f"  |  MT5 3,5 sa: alt {pct(m.lw_pct)} · üst {pct(m.uw_pct)} · gövde {pct(m.gv_pct)}"
    if h is not None:
        s += f"  |  MT5 H4: alt {pct(h.lw_pct)} · üst {pct(h.uw_pct)} · gövde {pct(h.gv_pct)}"
    return s


def panel_210(out: list[str], b: pd.DataFrame, k_ev: int, y0: float, h: float, e_m: pd.Series | None, title: str,
              x0: float = 0, w: float = W, n_before: int = 10, n_after: int = 4, note: bool = True, feed: str = "Dukascopy",
              h4v: pd.Series | None = None) -> None:
    a, z = max(0, k_ev - n_before), min(len(b), k_ev + n_after + 1)
    x = b.iloc[a:z]
    pn = Panel(y0 + 22, h - (58 if note else 40), float(x.low.min()), float(x.high.max()), len(x), w, x0)
    out.append(f'<text x="{x0 + PAD_L}" y="{y0 + 12}" fill="{TXT}" font-size="13">{title}</text>')
    pn.grid(out, 4)
    pn.candles(out, x, 3, "210m", hl=k_ev - a)
    e = b.iloc[k_ev]
    xi = pn.x(k_ev - a) + pn.cw * 0.42
    bb = min(e.open, e.close)
    out.append(f'<line x1="{xi:.1f}" x2="{xi:.1f}" y1="{pn.y(bb):.1f}" y2="{pn.y(e.low):.1f}" stroke="#000" stroke-width="2"/>'
               f'<text x="{xi + 4:.1f}" y="{(pn.y(bb) + pn.y(e.low)) / 2 + 4:.1f}" fill="#000" font-weight="bold">alt fitil {pct(e.lw_pct)}</text>')
    if note:
        out.append(f'<text x="{x0 + PAD_L}" y="{y0 + h - 2:.1f}" fill="{TXT}">{wick_note(e, e_m, feed, h4v)}</text>')


def panel_15(out: list[str], q: pd.DataFrame, a: int, z: int, s: pd.Series | None, tr: pd.DataFrame, i_last_ev: int,
             y0: float, h: float, title: str) -> None:
    x = q.iloc[a:z]
    lo, hi = float(x.low.min()), float(x.high.max())
    has_main = s is not None and s.get("j_main") is not None and s.get("j_main") == s.get("j_main")
    if has_main:
        lo, hi = min(lo, s.BB), max(hi, s.BT)
    pn = Panel(y0 + 20, h - 40, lo, hi, len(x))
    out.append(f'<text x="{PAD_L}" y="{y0 + 12}" fill="{TXT}" font-size="13">{title}</text>')
    pn.grid(out)
    pn.candles(out, x, 8, "15m")
    ev_i = i_last_ev - a
    if 0 <= ev_i < len(x):
        xe = PAD_L + (ev_i + 1) * pn.cw
        out.append(f'<line x1="{xe:.1f}" x2="{xe:.1f}" y1="{pn.y0}" y2="{pn.y0 + pn.h}" stroke="#555" stroke-dasharray="4 3"/>'
                   f'<text x="{xe + 3:.1f}" y="{pn.y0 + 10}" fill="#555">3,5 sa kapanış</text>')
    if has_main:
        B = s.BT - s.BB
        lv = {"BT": s.BT, "BB": s.BB, "L50": s.BB + 0.5 * B, "L48": s.BB + 0.48 * B, "L25": s.BB + 0.25 * B}
        jm = int(s.j_main) - a
        out.append(f'<rect x="{pn.x(jm) - pn.cw / 2:.1f}" y="{pn.y0}" width="{pn.cw:.1f}" height="{pn.h}" fill="none" stroke="#d62728" stroke-dasharray="2 2"/>')
        for k, p in lv.items():
            dash = "" if k in ("BT", "BB") else ' stroke-dasharray="5 3"'
            out.append(f'<line x1="{pn.x(jm) - pn.cw / 2:.1f}" x2="{W - PAD_R}" y1="{pn.y(p):.1f}" y2="{pn.y(p):.1f}" stroke="{LINE_COL[k]}"{dash}/>'
                       f'<text x="{W - PAD_R + 4}" y="{pn.y(p) - 2:.1f}" fill="{LINE_COL[k]}" font-weight="bold">{k} {p:.1f}</text>')
    elif s is not None:
        out.append(f'<text x="{PAD_L}" y="{pn.y0 + 14}" fill="#b00">15m kurulum yok: {s.bitis}</text>')
    t0 = int(x.t.iloc[0])
    for r in tr.itertuples():
        i_in, i_out = (r.t_in - t0) / 900, (r.t_out - t0) / 900
        if not 0 <= i_in < len(x):
            continue
        c = STRAT_COL[r.rule]
        x1, x2 = PAD_L + i_in * pn.cw, PAD_L + min(i_out, len(x)) * pn.cw
        y1 = pn.y(r.px_in)
        out.append(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y1:.1f}" y2="{pn.y(r.px_out):.1f}" stroke="{c}" stroke-width="2"/>')
        tri = (f"{x1:.1f},{y1 + 6:.1f} {x1 - 6:.1f},{y1 + 15:.1f} {x1 + 6:.1f},{y1 + 15:.1f}" if r.side > 0 else
               f"{x1:.1f},{y1 - 6:.1f} {x1 - 6:.1f},{y1 - 15:.1f} {x1 + 6:.1f},{y1 - 15:.1f}")
        out.append(f'<polygon points="{tri}" fill="{c}"/>'
                   f'<text x="{x2 + 3:.1f}" y="{pn.y(r.px_out) + 4:.1f}" fill="{c}">{r.rule} {"AL" if r.side > 0 else "SAT"} {r.why} {r.net_bp:+.0f}bp</text>')


def full_chart(b: pd.DataFrame, q: pd.DataFrame, e: pd.Series, s: pd.Series | None, tr: pd.DataFrame,
               e_m: pd.Series | None, title: str, feed: str = "Dukascopy", h: pd.Series | None = None) -> str:
    H1, H2 = 300, 430
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H1 + H2}" font-family="Helvetica,Arial" font-size="11">',
           f'<rect width="{W}" height="{H1 + H2}" fill="#fff"/>']
    k_ev = int(np.flatnonzero(b.t.values == e.t)[0])
    panel_210(out, b, k_ev, 0, H1, e_m, f"{title} — 3,5 saatlik mumlar (olay sarı zeminli)", feed=feed, h4v=h)
    nb = int(s.n_bar) if s is not None and s.n_bar == s.n_bar else 0
    a, z = int(e.i_first) - 2, min(len(q), int(e.i_last) + max(nb, 4) + 10)
    panel_15(out, q, a, z, s, tr, int(e.i_last), H1, H2, "15 dk — ana mum (kırmızı kesik çerçeve), çizgiler ve işlemler")
    out.append("</svg>")
    return "".join(out)


def thumb(b: pd.DataFrame, k_ev: int, e_m: pd.Series | None, h: pd.Series | None = None) -> str:
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 470 250" font-family="Helvetica,Arial" font-size="10">',
           '<rect width="470" height="250" fill="#fff"/>']
    e = b.iloc[k_ev]
    panel_210(out, b, k_ev, 0, 250, e_m, f"{fmt(e.t, '%Y-%m-%d %H:%M')} NY", w=470, n_before=8, n_after=3, note=False)
    out.append("</svg>")
    note = wick_note(e, e_m, h=h).replace("  |  ", "<br>")
    return f"<div style='border:1px solid #ddd;padding:4px'>{''.join(out)}<div style='font-size:11px'>{note}</div></div>"


def main() -> None:
    files: list[tuple[str, str]] = []
    conf = veri.mt5_210m().set_index("t")
    cm = lambda t: conf.loc[int(t)] if int(t) in conf.index else None   # noqa: E731
    h4 = veri.mt5_h4()

    def hv(bb: pd.DataFrame, qq: pd.DataFrame, t: int) -> pd.Series | None:
        """Olayın dibini içeren MT5 H4 mumu."""
        k = veri.h4_key(K.low_time(bb[bb.t == t], qq))[0]
        return h4.loc[k] if k in h4.index else None

    # 17 Kasım — kutu MT5 M1 (kullanıcının grafiği)
    pm = veri.mt5_path("M1")
    qm = veri.build_15m(pm)
    bm = veri.build_210m(qm)
    lo = int(pd.Timestamp("2026-11-17 10:30", tz=veri.NY).timestamp())
    for name, cfg in [("W14", replace(K.Cfg(), window="L14")), ("ANA", K.Cfg())]:
        ev = K.events(bm, cfg.thr, None, cfg.uw_ratio, cfg.body_rule, q=qm, h4=h4 if cfg.h4_check else None)
        ev = ev[ev.t >= lo].reset_index(drop=True)
        assert len(ev), "17 Kas mumu ana kuralı sağlamıyor"
        assert int(ev.t.iloc[0]) == int(pd.Timestamp("2026-11-17 10:30", tz=veri.NY).timestamp())
        sigs, st = K.setup_signals(qm, ev, cfg)
        tr = K.execute(pm, sigs + K.s1_signals(ev, cfg))
        f = f"grafik_17kasim_{name}.svg"
        (veri.RESULTS / f).write_text(full_chart(bm, qm, ev.iloc[0], st.iloc[0], tr[tr.setup == 0], cm(ev.t.iloc[0]),
                                                 f"17 Kas 2026 MT5 NAS100 — ana mum penceresi {cfg.window}", feed="MT5 M1'den",
                                                 h=hv(bm, qm, int(ev.t.iloc[0]))))
        files.append((f, f"17 Kasım, pencere {cfg.window}"))

    # Dukascopy ana koşu (EK-1 tanımı, broker teyitli)
    p = veri.duka_path()
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    cfg = K.Cfg()
    excl = veri.check_vs_file(b)["supheli_t"]
    ev = K.events(b, cfg.thr, excl, cfg.uw_ratio, cfg.body_rule, veri.mt5_210m(), "MT5", q, h4 if cfg.h4_check else None)
    e1 = replace(cfg, body_rule=False, h4_check=False)
    ev_e1 = set(K.events(b, e1.thr, excl, e1.uw_ratio, e1.body_rule, veri.mt5_210m(), "MT5", q, None).t.astype(int))
    sigs, st = K.setup_signals(q, ev, cfg)
    tr = K.execute(p, sigs + K.s1_signals(ev, cfg))
    has = sorted(set(tr[tr.rule != "S1"].setup))
    for n, k in enumerate(np.random.default_rng(7).choice(has, 6, replace=False), 1):
        e = ev.iloc[int(k)]
        f = f"grafik_ornek_{n}.svg"
        (veri.RESULTS / f).write_text(full_chart(b, q, e, st.iloc[int(k)], tr[tr.setup == k], cm(e.t),
                                                 f"Örnek {n}: {fmt(e.t, '%Y-%m-%d %H:%M')} NY", h=hv(b, q, int(e.t))))
        files.append((f, f"Yeni örnek {n}"))

    # Kullanıcının işaretlediği eski örnekler — yeni kuralda durumu
    ev_t = set(ev.t.astype(int))
    for n, z in OLD_EXAMPLES.items():
        t = int(pd.Timestamp(z, tz=veri.NY).timestamp())
        row = b[b.t == t].iloc[0]
        mm = cm(t)
        hh = hv(b, q, t)
        why = []                                   # ANA kural (EK-4): 3,5 sa Duka+MT5 alt ≥ %0,50, üst ≤ alt/2, alt ≥ gövde; H4 alt ≥ %0,50, üst ≤ alt/2
        for nm, c in (("Dukascopy 3,5 sa", row), ("MT5 3,5 sa", mm), ("MT5 H4 (sizin grafiğiniz)", hh)):
            if c is None:
                why.append(f"{nm} mumu yok")
                continue
            if c.lw_pct < 0.5:
                why.append(f"{nm} alt fitil {pct(c.lw_pct)}, %0,50'nin altında")
            if c.uw_pct > 0.5 * c.lw_pct:
                why.append(f"{nm} üst fitil {pct(c.uw_pct)} > alt/2 (büyük fitil yukarıda)")
            if "H4" not in nm and c.gv_pct > c.lw_pct:
                why.append(f"{nm} gövde {pct(c.gv_pct)} > alt fitil {pct(c.lw_pct)} (fitil kısa görünür)")
        if t in ev_t:
            k = int(np.flatnonzero(ev.t.values == t)[0])
            durum = "KURALA UYUYOR"
            s, tt = st.iloc[k], tr[tr.setup == k]
        else:
            durum = "ELENDİ: " + "; ".join(why)
            s, tt = None, tr.iloc[0:0]
        durum += " · yalnız eşik kuralı E1: " + ("uyar" if t in ev_e1 else "elenir")
        f = f"grafik_eski_ornek_{n}.svg"
        (veri.RESULTS / f).write_text(full_chart(b, q, row, s, tt, mm, f"Eski örnek {n}: {z} NY — {durum}", h=hv(b, q, t)))
        files.append((f, f"Eski örnek {n}: {durum}"))

    html = ["<!doctype html><meta charset='utf-8'><title>Fitil 210m grafikleri</title>"
            "<body style='font-family:Helvetica;background:#fff;color:#222;max-width:1000px;margin:auto;padding:0 16px'>"
            "<h2>3,5 sa alt fitil — doğrulama grafikleri (EK-1 tanımı)</h2>"
            "<p>Ana kural: 3,5 saatlik mumda (Dukascopy ve MT5) alt fitil ≥ %0,50, üst fitil ≤ alt fitilin yarısı, alt fitil ≥ gövde; "
            "fitilin dibini içeren MT5 H4 mumunda (sizin grafiğiniz) alt fitil ≥ %0,50 ve üst fitil ≤ alt fitilin yarısı. "
            "Bu tanım işaretlediğiniz 4 örneği eler, 17 Kasım örneğinizi tutar.</p>"]
    html += [f"<h3>{t}</h3><div>{(veri.RESULTS / f).read_text()}</div>" for f, t in files]
    (veri.RESULTS / "grafikler.html").write_text("".join(html))

    gal = ["<!doctype html><meta charset='utf-8'><title>Olay galerisi</title><body style='font-family:Helvetica;background:#fff;"
           "max-width:1000px;margin:auto;padding:0 16px'><h2>Rastgele 24 olay — 3,5 saatlik mum görünümü</h2>"
           f"<p>Toplam {len(ev)} olay; tam liste results/olaylar_ANA.csv.</p>"
           "<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:8px'>"]
    for k in sorted(np.random.default_rng(3).choice(len(ev), 24, replace=False)):
        t = int(ev.t.iloc[k])
        gal.append(thumb(b, int(np.flatnonzero(b.t.values == t)[0]), cm(t), hv(b, q, t)))
    gal.append("</div>")
    (veri.RESULTS / "galeri.html").write_text("".join(gal))
    import xml.dom.minidom
    for f, _ in files:
        xml.dom.minidom.parseString((veri.RESULTS / f).read_text())          # SVG geçerli XML mi
    print("yazıldı:", [f for f, _ in files], "+ galeri.html")


if __name__ == "__main__":
    main()
