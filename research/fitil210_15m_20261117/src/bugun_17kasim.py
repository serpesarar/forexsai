"""bugun_17kasim.py — kullanıcının ekran görüntülerindeki gün (17 Kas 2026) için dört kuralın tam gün sonucu + geçmiş win rate.

Veri: kutudan 2026-11-18 01:37 UTC'de taze çekilen MT5 NAS100 M1/H1 (`data/kutu_1117/`, calistir/arac_nas100_mum_export.py).
Kural: RAPOR'daki ana kural (kullanıcının seçtiği "görünüşe göre" tanımı); ana mum penceresi hem "son 6 mum" (ANA) hem
kullanıcının çizdiği "tüm 14 mum" (W14).
"""
from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pandas as pd

import kurallar as K
import veri

FRESH = veri.HERE / "data/kutu_1117"
DAY0 = "2026-11-17 00:00"


def fmt(t: int) -> str:
    return pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(veri.NY).strftime("%H:%M")


def history_winrate() -> pd.DataFrame:
    """Geçmiş (Dukascopy 2018-26, ana kural) win rate, ortalama kazanç/kayıp ve başabaş win rate."""
    t = pd.read_csv(veri.RESULTS / "islemler_DUKA_ANA.csv")
    rows = []
    for s, g in t.groupby("rule"):
        col = "net_bp" if s == "S1" else "R"
        v = g[col].astype(float)
        w, l = v[v > 0], v[v <= 0]
        be = abs(l.mean()) / (w.mean() + abs(l.mean())) if len(w) and len(l) else np.nan
        rows.append({"kural": s, "işlem": len(g), "win_rate": round(100 * len(w) / len(g), 1),
                     "ort_kazanç": round(w.mean(), 2), "ort_kayıp": round(l.mean(), 2),
                     "başabaş_wr": round(100 * be, 1), "beklenti": round(v.mean(), 3), "birim": "bp" if s == "S1" else "R"})
    return pd.DataFrame(rows)


def main() -> None:
    veri.KUTU = FRESH
    p = veri.mt5_path("M1")
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    h4 = veri.mt5_h4()
    lo = int(pd.Timestamp(DAY0, tz=veri.NY).timestamp())
    print(f"veri sonu: {pd.Timestamp(int(p.t[-1]), unit='s', tz='UTC').tz_convert(veri.NY)} NY")
    day = b[b.t >= lo]
    print("\n17 Kasım 3,5 saatlik mumlar (MT5):")
    for r in day.itertuples():
        print(f"  {fmt(r.t)}–{fmt(r.t_end_nom)}  O {r.open:.1f} H {r.high:.1f} L {r.low:.1f} C {r.close:.1f}  "
              f"alt %{r.lw_pct:.2f} üst %{r.uw_pct:.2f} gövde %{r.gv_pct:.2f}  n15 {r.n15}")
    svgs: list[tuple[str, str]] = []
    out = {"veri_sonu_ny": str(pd.Timestamp(int(p.t[-1]), unit='s', tz='UTC').tz_convert(veri.NY)), "pencereler": {}}
    for name, cfg in [("ANA (son 6 mum)", K.Cfg()), ("W14 (tüm 14 mum — sizin çiziminiz)", replace(K.Cfg(), window="L14"))]:
        ev = K.events(b, cfg.thr, None, cfg.uw_ratio, cfg.body_rule, q=q, h4=h4)
        ev = ev[ev.t >= lo].reset_index(drop=True)
        sigs, st = K.setup_signals(q, ev, cfg)
        tr = K.execute(p, sigs + K.s1_signals(ev, cfg))
        print(f"\n=== {name} ===  olay: {len(ev)}")
        for e, s in zip(ev.itertuples(), st.itertuples()):
            print(f"  olay {fmt(e.t)}–{fmt(e.t_end_nom)} NY  alt fitil %{e.lw_pct:.2f}")
            if s.j_main is not None and s.j_main == s.j_main:
                j = int(s.j_main)
                print(f"  ana mum {fmt(q.t[j])}  üst çizgi {s.BT:.1f}  alt çizgi {s.BB:.1f}  %48 {s.BB + 0.48 * s.B:.1f}  "
                      f"%50 {s.L50:.1f}  %25 {s.BB + 0.25 * s.B:.1f}  kurulum bitişi: {s.bitis} ({s.n_bar} mum)")
        rows = []
        for x in tr.sort_values("t_in").itertuples():
            ok = "KAZANDI" if x.net_bp > 0 else "KAYBETTİ"
            print(f"  {x.rule} {'AL ' if x.side > 0 else 'SAT'} giriş {fmt(x.t_in)} @ {x.px_in:.1f} → {x.why:5s} {fmt(x.t_out)} @ "
                  f"{x.px_out:.1f}  net {x.net_bp:+6.1f} bp  {'' if np.isnan(x.R) else f'R {x.R:+.2f}'}  {ok}")
            rows.append({"kural": x.rule, "yön": "AL" if x.side > 0 else "SAT", "giriş": fmt(x.t_in), "giriş_fiyat": round(x.px_in, 1),
                         "çıkış": fmt(x.t_out), "çıkış_fiyat": round(x.px_out, 1), "neden": x.why, "net_bp": round(x.net_bp, 1),
                         "R": None if np.isnan(x.R) else round(x.R, 2), "sonuç": ok})
        g = tr.groupby("rule").agg(n=("net_bp", "size"), kazanan=("net_bp", lambda v: int((v > 0).sum())), toplam_bp=("net_bp", "sum"))
        print("  gün özeti:", {k: f"{int(r.kazanan)}/{int(r.n)} kazandı, {r.toplam_bp:+.1f} bp" for k, r in g.iterrows()})
        import grafik
        k = 0
        hk = veri.h4_key(K.low_time(ev.iloc[[k]], q))[0]
        svg = grafik.full_chart(b, q, ev.iloc[k], st.iloc[k], tr[tr.setup == k], None,
                                f"17 Kas 2026 MT5 NAS100 (taze veri) — {name}", feed="MT5", h=h4.loc[hk] if hk in h4.index else None)
        f = f"bugun_17kasim_{'W14' if 'W14' in name else 'ANA'}.svg"
        (veri.RESULTS / f).write_text(svg)
        svgs.append((name, svg))
        out["pencereler"][name] = {"islemler": rows, "ozet": {k: {"n": int(r.n), "kazanan": int(r.kazanan), "toplam_bp": round(float(r.toplam_bp), 1)}
                                                            for k, r in g.iterrows()}}
    hw = history_winrate()
    print("\nGeçmiş (Dukascopy 2018–2026, ana kural, 232 olay):")
    print(hw.to_string(index=False))
    out["gecmis"] = hw.to_dict("records")
    html = "<!doctype html><meta charset='utf-8'><title>17 Kasım deneyi</title><body style='font-family:Helvetica;max-width:1000px;margin:auto;padding:0 16px;background:#fff'>"
    html += "".join(f"<h3>{n}</h3>{v}" for n, v in svgs)
    (veri.RESULTS / "bugun_17kasim.html").write_text(html)
    (veri.RESULTS / "bugun_17kasim.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
