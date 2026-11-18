"""oz_test.py — sentetik mumlarla kural birim testleri (elle hesaplanan beklenen sonuçlar)."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

import kurallar as K
import veri

T0 = int(pd.Timestamp("2025-03-04 10:30", tz="America/New_York").timestamp())   # 210m dilimi 10:30–14:00
SPR = 1.0

# (O, H, L, C) 15m mumları, 10:30'dan başlayarak
BARS = [(20300, 20305, 19995, 20000)]                       # 10:30 büyük kırmızı (300) — yalnız W14 görür
BARS += [(20000, 20010, 19990, 20000)] * 7                    # 10:45–12:15 yatay
BARS += [(20000, 20005, 19700, 19800),                        # 12:30 ana mum (L6): BT 20000, BB 19800
         (19800, 19860, 19790, 19850),                        # 12:45
         (19850, 19855, 19825, 19830),                        # 13:00 küçük kırmızı
         (19830, 19885, 19825, 19880),                        # 13:15
         (19880, 19915, 19875, 19910),                        # 13:30
         (19910, 19915, 19895, 19900)]                        # 13:45 → olay kapanışı 19900, fitil 200/19900 = %1,0
BARS += [(19900, 19920, 19890, 19910),                        # 14:00 bölge içi, C > L48 (19896) → S2 + S3
         (19910, 19950, 19880, 19890),                        # 14:15 H > L50, C < L50, üst fitil → S2 + S4
         (19890, 20100, 19885, 20100)]                        # 14:30 bölge dışı → kurulum biter
BARS += [(20100, 20110, 20090, 20100)] * 6                    # sonrası


def synth_path() -> veri.PathBars:
    t, o, h, l, c = [], [], [], [], []
    for k, (O, H, L, C) in enumerate(BARS):
        pts = np.r_[np.linspace(O, L, 6)[:-1], np.linspace(L, H, 6)[:-1], np.linspace(H, C, 6)]   # O→L→H→C, 16 nokta
        for m in range(15):
            a, b = pts[m], pts[m + 1]
            t.append(T0 + k * 900 + m * 60)
            o.append(a); c.append(b); h.append(max(a, b)); l.append(min(a, b))
    n = len(t)
    return veri.PathBars(np.array(t, np.int64), np.array(o), np.array(h), np.array(l), np.array(c), np.full(n, SPR), 60, "sentetik")


def main() -> None:
    p = synth_path()
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    assert len(q) == len(BARS), len(q)
    ev = K.events(b, 0.50)
    assert len(ev) == 1 and abs(ev.lw_pct.iloc[0] - 200 / 19900 * 100) < 1e-9, ev
    assert int(ev.tend.iloc[0]) == T0 + 14 * 900, "karar anı = 14:00"

    j6, start, du = K.pick_main(q, ev.iloc[0], "L6")
    assert du == "ok"
    assert q.t[j6] == T0 + 8 * 900 and start == 14, (j6, start)
    j14, _, _ = K.pick_main(q, ev.iloc[0], "L14")
    assert q.t[j14] == T0, "W14 10:30 mumunu seçmeli"

    cfg = K.Cfg()
    sigs, setups = K.setup_signals(q, ev, cfg)
    got = [(s.strat, (s.t_sig - T0) // 900) for s in sigs]
    assert got == [("S2", 15), ("S3", 15), ("S2", 16), ("S4", 16)], got
    assert setups.bitis.iloc[0] == "bolge_disi" and setups.n_bar.iloc[0] == 2
    for s in sigs:
        assert s.t_sig >= int(q.tend[q.t == s.t_sig - 900].iloc[0]), "karar yalnız kapanmış mumla"

    tr = K.execute(p, sigs + K.s1_signals(ev, cfg))
    assert (tr.t_in >= tr.t_sig).all(), "giriş karar anından önce olamaz"
    r = {(x.rule, (x.t_in - T0) // 900): x for x in tr.itertuples()}
    s2a, s2b = r[("S2", 15)], r[("S2", 16)]
    assert s2a.why == "tp" and abs(s2a.px_in - 19911) < 1e-9 and abs(s2a.px_out - 19911 * 1.0018) < 1e-6, s2a
    assert s2b.why == "tp", "ilk S2 kapandı → ikinci S2 açılabilir"
    s3 = r[("S3", 15)]
    assert s3.why == "stop" and s3.px_in == 19910 and s3.px_out == 20000, s3
    assert abs(s3.R - (-(20000 / 19910 - 1) * 1e4 / 1e4 * 19910 / 90)) < 1e-9
    s4 = r[("S4", 16)]
    assert s4.why == "stop" and s4.px_in == 19890, s4
    s1 = r[("S1", 14)]
    assert s1.why == "time" and s1.px_in == 19901 and s1.px_out == 19890 and s1.t_out == T0 + 14 * 900 + 1800, s1

    # aynı barda TP ve SL → SL
    pb = veri.PathBars(np.array([0, 60]), np.array([100.0, 100]), np.array([110.0, 100]), np.array([90.0, 100]),
                       np.array([100.0, 100]), np.zeros(2), 60, "x")
    assert K.walk(pb, 0, 120, +1, 95, 105)[2] == "stop"
    assert K.walk(pb, 0, 120, -1, 105, 95)[2] == "stop"

    # tek pozisyon: ilk S3 açıkken ikinci S3 atlanır
    extra = [K.Signal("S3", sigs[1].t_sig + 60, -1, 20000, 19850, None, 0, 19910)]
    tr2 = K.execute(p, [sigs[1]] + extra)
    assert len(tr2) == 1 and tr2.attrs["skip"]["mesgul"] == 1

    # iyimser icra: giriş = sinyal kapanışı, spread 0
    tro = K.execute(p, [sigs[1]], optimistic=True)
    assert tro.px_in.iloc[0] == 19910 and tro.px_out.iloc[0] == 20000

    # S2f yalnız ilk mum; F3 penceresi
    sf, _ = K.setup_signals(q, ev, replace(cfg, s2_first_only=True))
    assert [s.strat for s in sf].count("S2") == 1
    jf, stf, _ = K.pick_main(q, ev.iloc[0], "F3")
    assert stf == 17 and jf is None or q.close[jf] < q.open[jf]

    # EK-1: üst fitil kuralı (alt %1,0, üst ≈ %0,02 → geçer; üst fitili büyüt → elenir)
    assert abs(ev.uw_pct.iloc[0] - 5 / 20300 * 100) < 1e-9
    assert len(K.events(b, 0.50, uw_ratio=0.5)) == 1
    b2 = b.copy()
    b2.loc[b2.t == T0, "uw_pct"] = 0.9                           # üst fitil %0,9 > alt %1,0 / 2
    assert len(K.events(b2, 0.50, uw_ratio=0.5)) == 0 and len(K.events(b2, 0.50, uw_ratio=1.0)) == 1
    b3 = b.copy()
    b3.loc[b3.t == T0, "gv_pct"] = 1.5                           # gövde > alt fitil → G1 eler
    assert len(K.events(b3, 0.50, body_rule=True)) == 0
    # iki besleme teyidi: broker mumu kuralı sağlamazsa olay düşer; MT5_def broker mumuyla tanımlar
    conf_bad = b.copy(); conf_bad["lw_pct"] = 0.2
    assert len(K.events(b, 0.50, uw_ratio=0.5, conf=conf_bad, confirm="MT5")) == 0
    assert len(K.events(b, 0.50, uw_ratio=0.5, conf=conf_bad, confirm="none")) == 1
    b_weak = b.copy(); b_weak["lw_pct"] = 0.45
    assert len(K.events(b_weak, 0.50, uw_ratio=0.5, conf=b, confirm="MT5_def")) == 1
    # pencere eksiksizliği: son 6 mumdan biri eksikse S2–S4 kurulumu yok
    qx = q.drop(index=11).reset_index(drop=True)                  # 13:15 mumu yok
    bx = veri.build_210m(qx)
    evx = K.events(bx, 0.50)
    assert K.pick_main(qx, evx.iloc[0], "L6")[2] == "eksik_15m"
    # EK-2: H4 görünüm teyidi — dip 12:30 NY (EST) → sunucu 19:30 → H4 16:00 mumu
    assert K.low_time(ev, q)[0] == T0 + 8 * 900
    key = pd.Timestamp("2025-03-04 16:00")
    h4ok = pd.DataFrame({"lw_pct": [0.8], "uw_pct": [0.1], "gv_pct": [0.3]}, index=[key])
    h4bad = pd.DataFrame({"lw_pct": [0.8], "uw_pct": [0.6], "gv_pct": [0.3]}, index=[key])   # üst fitil büyük
    assert len(K.events(b, 0.50, uw_ratio=0.5, body_rule=False, q=q, h4=h4ok)) == 1
    assert len(K.events(b, 0.50, uw_ratio=0.5, body_rule=False, q=q, h4=h4bad)) == 0
    print("oz_test: tüm kontroller geçti")


if __name__ == "__main__":
    main()
