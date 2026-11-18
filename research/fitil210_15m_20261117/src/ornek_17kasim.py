"""ornek_17kasim.py — kullanıcının 17 Kas 2026 ekran görüntülerini kutu MT5 NAS100 M1 ile motordan yeniden üretir."""
from __future__ import annotations

import json
from dataclasses import replace

import pandas as pd

import kurallar as K
import veri

USER_LINES = {"BT": 27058.3, "BB": 26778.2, "L50": 26920.9}


def fmt(t: int) -> str:
    return pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(veri.NY).strftime("%m-%d %H:%M")


def main() -> None:
    p = veri.mt5_path("M1")
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    lo = int(pd.Timestamp("2026-11-17 07:00", tz=veri.NY).timestamp())
    ev_all = K.events(b, 0.50)
    out = {}
    for name, cfg in [("ANA_L6", K.Cfg()), ("W14", replace(K.Cfg(), window="L14", name="W14"))]:
        ev = ev_all[ev_all.t >= lo].reset_index(drop=True)
        sigs, setups = K.setup_signals(q, ev, cfg)
        tr = K.execute(p, sigs + K.s1_signals(ev, cfg))
        print(f"\n=== {name} ===")
        for e, s in zip(ev.itertuples(), setups.itertuples()):
            print(f"olay {fmt(e.t)}–{fmt(e.tend)} NY  O {e.open:.1f} H {e.high:.1f} L {e.low:.1f} C {e.close:.1f}  alt fitil %{e.lw_pct:.2f}")
            if s.j_main is not None and s.j_main == s.j_main:
                j = int(s.j_main)
                print(f"  ana mum {fmt(q.t[j])}  BT {s.BT:.1f}  BB {s.BB:.1f}  B {s.B:.1f}  L48 {s.BB + 0.48 * s.B:.1f}  "
                      f"L50 {s.L50:.1f}  L25 {s.BB + 0.25 * s.B:.1f}  bitiş {s.bitis} ({s.n_bar} mum)")
        for x in tr.itertuples():
            print(f"  {x.rule} {'AL ' if x.side > 0 else 'SAT'} sinyal {fmt(x.t_sig)} giriş {fmt(x.t_in)} @ {x.px_in:.1f} → "
                  f"{x.why} {fmt(x.t_out)} @ {x.px_out:.1f}  net {x.net_bp:+.1f} bp  R {x.R:+.2f}")
        out[name] = {"setups": setups.to_dict("records"), "trades": tr.drop(columns=["d"]).to_dict("records")}
    s14 = pd.DataFrame(out["W14"]["setups"])
    s14 = s14[s14.t_ev == int(pd.Timestamp("2026-11-17 10:30", tz=veri.NY).timestamp())].iloc[0]
    fark = {k: round(float(s14[k]) - v, 1) for k, v in USER_LINES.items()}
    print("\nkullanıcı çizgileri ↔ motor (W14):", fark)
    out["kullanici_cizgi_farki_W14"] = fark
    veri.RESULTS.mkdir(exist_ok=True)
    (veri.RESULTS / "ornek_17kasim.json").write_text(json.dumps(out, default=str, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
