"""canli_mum.py — "canlı mum" varyantı (EK-5): 3,5 saatlik mum OLUŞURKEN her 15m kapanışta, o ana kadarki mum
(açılış, şimdiye kadarki tepe/dip, son kapanış) tespit kuralını sağlıyorsa kurulum hemen kurulur.

Neden: kullanıcı 17 Kas grafiğinde 10:30 ana mumundan sonra, 3,5 sa kapanışından ÖNCE (11:00–13:45) işlem bekledi.
Sızıntı yok: karar anı = o 15m mumun kapanışı; ana mum = 3,5 sa mumunun o ana kadar kapanmış 15m mumları içinde gövdesi en
büyük kırmızı mum (kullanıcının çizimi, W14 mantığı). Tespit mumu ana mumdan sonraysa tespit mumunun kendi kapanışı da ilk
tarama mumudur (kullanıcının "bir sonraki mum" kuralı). Kurulum: bölge dışı kapanışa veya bir sonraki canlı tespite kadar.
H4 ve broker teyidi canlıda yapılamaz (mumlar da oluşuyor) → kullanılmaz. S1 değişmez (mum kapanışında AL).

Çıktı: results/canli_ozet.json, results/canli_bugun.html (+ .svg), konsol özeti.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import grafik
import kosu
import kurallar as K
import veri

STRATS = ["S2", "S3", "S4"]


def live_events(q: pd.DataFrame, b: pd.DataFrame, thr: float = 0.50, uw_ratio: float = 0.5, body_rule: bool = True,
                exclude_t: set[int] | None = None) -> pd.DataFrame:
    """Her 210m mumu için oluşurken kuralı ilk sağladığı 15m kapanış. Ana mum ve tarama başlangıcı önceden hesaplanır."""
    O, H, L, C, T, TE = (q[c].values for c in ("open", "high", "low", "close", "t", "tend"))
    rows = []
    for r in b.itertuples():
        if exclude_t and int(r.t) in exclude_t:
            continue
        a, z = int(r.i_first), int(r.i_last)
        o0, hh, ll = O[a], -np.inf, np.inf
        for j in range(a, z + 1):
            hh, ll = max(hh, H[j]), min(ll, L[j])
            bb, tt = min(o0, C[j]), max(o0, C[j])
            lw, uw, gv = (bb - ll) / bb * 100, (hh - tt) / tt * 100, (tt - bb) / bb * 100
            if lw >= thr and uw <= uw_ratio * lw and (lw >= gv or not body_rule):
                seg = np.arange(a, j + 1)
                body = np.where(C[seg] < O[seg], O[seg] - C[seg], -1.0)
                jm = int(seg[np.argmax(body)]) if body.max() > 0 else None
                start = j if (jm is not None and jm < j) else j + 1
                rows.append({"t": int(r.t), "tend": int(TE[j]), "t_det": int(T[j]), "slot": int(r.slot), "year": int(r.year),
                             "i_first": a, "i_last": z, "i_det": j, "j_main_pre": jm, "start_pre": start,
                             "lw_pct": lw, "uw_pct": uw, "gv_pct": gv, "close": C[j],
                             "final_ok": bool(r.lw_pct >= thr and r.uw_pct <= uw_ratio * r.lw_pct and (r.lw_pct >= r.gv_pct or not body_rule)),
                             "dk_once": int((int(r.t_end_nom) - int(TE[j])) / 60)})
                break
    ev = pd.DataFrame(rows).sort_values("tend").reset_index(drop=True)
    ev["j_main_pre"] = ev.j_main_pre.astype("float")
    return ev


def run(p: veri.PathBars, q: pd.DataFrame, ev: pd.DataFrame, optimistic: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = K.Cfg(window="L14", name="CANLI")
    sigs, st = K.setup_signals(q, ev, cfg)
    tr = K.execute(p, sigs, optimistic=optimistic, tags={"cfg": "CANLI"})
    return tr, st


def main() -> None:
    out: dict = {}
    # ── Dukascopy 2018-26 ──
    p = veri.duka_path()
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    excl = veri.check_vs_file(b)["supheli_t"]
    ev = live_events(q, b, exclude_t=excl)
    tr, st = run(p, q, ev)
    opt, _ = run(p, q, ev, optimistic=True)
    out["DUKA"] = {"olay": len(ev), "kapanista_da_tutan_%": round(100 * ev.final_ok.mean(), 1),
                   "kapanistan_ort_dk_once": int(ev.dk_once.median()), "bitis": st.bitis.value_counts().to_dict(),
                   **{s: kosu.by_era(tr, s) for s in STRATS}, "iyimser": {s: kosu.stats(opt, s) for s in STRATS}}
    tr.assign(d=tr.d.astype(str)).to_csv(veri.RESULTS / "islemler_DUKA_CANLI.csv", index=False)
    # ── MT5 bağımsız (M15, 2022-08 →) ──
    veri.KUTU = veri.HERE / "data/kutu_1117"
    pm = veri.mt5_path("M15")
    qm = veri.build_15m(pm)
    bm = veri.build_210m(qm)
    evm = live_events(qm, bm)
    trm, stm = run(pm, qm, evm)
    out["MT5"] = {"olay": len(evm), "kapanista_da_tutan_%": round(100 * evm.final_ok.mean(), 1),
                  **{s: kosu.by_era(trm, s) for s in STRATS}}
    # ── 17 Kasım (MT5 M1 taze) ──
    p1 = veri.mt5_path("M1")
    q1 = veri.build_15m(p1)
    b1 = veri.build_210m(q1)
    lo = int(pd.Timestamp("2026-11-17 00:00", tz=veri.NY).timestamp())
    ev1 = live_events(q1, b1[b1.t >= lo].reset_index(drop=True))
    tr1, st1 = run(p1, q1, ev1)
    fm = lambda t: pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(veri.NY).strftime("%H:%M")   # noqa: E731
    print("17 Kasım canlı tespit:")
    for e, s in zip(ev1.itertuples(), st1.itertuples()):
        print(f"  3,5 sa {fm(e.t)} mumu, tespit {fm(e.tend)} (o ana kadar alt %{e.lw_pct:.2f} üst %{e.uw_pct:.2f} gövde %{e.gv_pct:.2f}), "
              f"ana mum {fm(q1.t[int(e.j_main_pre)]) if e.j_main_pre == e.j_main_pre else '-'}, kurulum bitişi {s.bitis} ({s.n_bar} mum), "
              f"kapanışta kural {'tuttu' if e.final_ok else 'TUTMADI'}")
    rows = []
    for x in tr1.sort_values("t_in").itertuples():
        print(f"  {x.rule} {'AL ' if x.side > 0 else 'SAT'} giriş {fm(x.t_in)} @ {x.px_in:.1f} → {x.why:5s} {fm(x.t_out)} @ {x.px_out:.1f}  "
              f"net {x.net_bp:+6.1f} bp  R {x.R:+.2f}  {'KAZANDI' if x.net_bp > 0 else 'KAYBETTİ'}")
        rows.append({"kural": x.rule, "giriş": fm(x.t_in), "giriş_fiyat": round(x.px_in, 1), "çıkış": fm(x.t_out),
                     "neden": x.why, "net_bp": round(x.net_bp, 1), "R": round(x.R, 2)})
    g = tr1.groupby("rule").agg(n=("net_bp", "size"), kaz=("net_bp", lambda v: int((v > 0).sum())), bp=("net_bp", "sum"))
    print("  gün özeti:", {k: f"{int(r.kaz)}/{int(r.n)} kazandı, {r.bp:+.1f} bp" for k, r in g.iterrows()})
    out["bugun"] = {"islemler": rows, "ozet": {k: {"n": int(r.n), "kazanan": int(r.kaz), "bp": round(float(r.bp), 1)} for k, r in g.iterrows()}}
    # grafik — her canlı tespit için; kesik çizgi tespit anında (3,5 sa kapanışında değil)
    svgs = []
    for k in sorted(range(len(ev1)), key=lambda i: -int(ev1.t.iloc[i])):
        e = ev1.iloc[k]
        ev_row = b1[b1.t == e.t].iloc[0].copy()
        ev_row["i_last"] = int(e.i_det)
        svg = grafik.full_chart(b1, q1, ev_row, st1.iloc[k].copy(), tr1[tr1.setup == k], None,
                                f"17 Kas 2026 — CANLI MUM: {fm(e.t)} mumu, tespit {fm(e.tend)} (3,5 sa kapanmadan)", feed="MT5")
        svg = svg.replace("3,5 sa kapanış", f"canlı tespit {fm(e.tend)}")
        svgs.append(svg)
    (veri.RESULTS / "canli_bugun.svg").write_text(svgs[0])
    (veri.RESULTS / "canli_bugun.html").write_text("<!doctype html><meta charset='utf-8'><title>Canlı mum 17 Kasım</title>"
                                                   "<body style='font-family:Helvetica;max-width:1000px;margin:auto;background:#fff'>"
                                                   + "<hr>".join(svgs))
    # özet tablo
    for f in ("DUKA", "MT5"):
        r = out[f]
        print(f"\n{f}: canlı olay {r['olay']}, kapanışta da kuralı tutan %{r['kapanista_da_tutan_%']}")
        for s_ in STRATS:
            a = r[s_]
            print(f"  {s_}: n {a['TUM'].get('n')} ort R {a['TUM'].get('mean', float('nan')):+.3f}  win %{100 * a['TUM'].get('hit', float('nan')):.1f}  "
                  f"KEŞİF {a['KESIF'].get('mean', float('nan')):+.3f} TEST {a['TEST'].get('mean', float('nan')):+.3f}  "
                  f"küme P {a['TUM'].get('P_kume')}  spread×1,5 {a['TUM'].get('mean_s15', float('nan')):+.3f}"
                  + (f"  iyimser {r['iyimser'][s_].get('mean', float('nan')):+.3f}" if "iyimser" in r else ""))
    (veri.RESULTS / "canli_ozet.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
