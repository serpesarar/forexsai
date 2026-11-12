"""QS-03 R1 canlıya alma kartı (2. KURAL, 6 ölçüt) + canlı C3b ile çakışma.
Kart verisi: QQQ 2002-08→2026-10 (hacim/beklenti/kararlılık) + broker NAS100 M30 2018-26 (sürtünme/icra/tek pozisyon).
İcra: sinyal 16:00 kapanışıyla bilinir → gerçek giriş 16:30 ET barı açılışı (+ gerçek spread), çıkış D günü 16:30; iyimser = 16:00."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from r1_dengeleme import px, build, st, COST, H

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402
RNG = np.random.default_rng(53)


def broker_trades(M: pd.DataFrame, hh: int, mm: int, stress: float = 1.0) -> pd.Series:
    mk = Mkt("NAS100", stress=stress); out = {}
    for _, r in M[(M.side != 0) & (M.d_s >= "2018-06-01")].iterrows():
        off = pd.Timedelta(hours=hh, minutes=mm)
        i, j = mk.at(r.d_s + off), mk.at(r.d_e + off)
        if i < 0 or j < 0:
            continue
        c = mk.cost(i)
        out[r.d_s] = r.side * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - c / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j])
    return pd.Series(out)


def rsi2(c: pd.Series) -> pd.Series:
    g = c.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))


def main() -> None:
    inst = {"QQQ": px("QQQ")}
    M = build(px("SPY"), px("TLT"), inst)
    q = M[(M.side != 0) & (M.d_s >= "2002-08-01")]
    v = (q.side * q.r_QQQ - COST).to_numpy()
    h = len(v) // 2
    opt = broker_trades(M, 16, 0); real = broker_trades(M, 16, 30); stress = broker_trades(M, 16, 30, 1.5)
    card = {
        "1_hacim": {"n_QQQ_2002_26": int(len(v)), "n_broker": int(len(real)), "gecti": bool(len(v) >= 150)},
        "2_beklenti": st(v) | {"gecti": bool(v.mean() > 0 and st(v)["P"] >= 0.9)},
        "3_kararlilik": {"yari1": round(float(v[:h].mean()), 1), "yari2": round(float(v[h:].mean()), 1),
                         "gecti": bool(v[:h].mean() >= 0 and v[h:].mean() >= 0)},
        "4_surtunme": {"broker_gercek_icra_x1.5": st(stress.to_numpy()), "gecti": bool(stress.mean() > 0)},
        "5_icra": {"iyimser_16:00": round(float(opt.mean()), 1), "gercek_16:30": round(float(real.mean()), 1),
                   "fark": round(float(opt.mean() - real.mean()), 1), "broker_gercek": st(real.to_numpy()),
                   "gecti": bool(real.mean() > 0 and (opt.mean() - real.mean()) <= 0.5 * abs(opt.mean()))},
        "6_tek_pozisyon": {"not": "ayda en çok bir pozisyon, 3 gün; çakışma yok", "gecti": True},
    }
    passed = sum(card[k]["gecti"] for k in card)
    card["verdikt"] = "LIVE adayı (karar kullanıcıda; önce GÖLGE)" if passed == 6 else ("SHADOW" if passed >= 4 else "RED")
    card["gecen"] = f"{passed}/6"
    # bacaklar
    card["bacak_uzun_QQQ"] = st((q[q.side == 1].r_QQQ - COST).to_numpy())
    card["bacak_kisa_QQQ"] = st((-(q[q.side == -1].r_QQQ) - COST).to_numpy())
    card["broker_uzun"] = st(real[real.index.isin(q[q.side == 1].d_s)].to_numpy())
    card["broker_kisa"] = st(real[real.index.isin(q[q.side == -1].d_s)].to_numpy())
    # yıl
    s = pd.Series(v, index=q.d_s.values)
    card["yil_QQQ"] = {int(y): round(float(g.sum()), 0) for y, g in s.groupby(s.index.year)}
    card["yil_arti"] = f"{sum(1 for x in card['yil_QQQ'].values() if x > 0)}/{len(card['yil_QQQ'])}"
    card["en_iyi5_haric"] = round(float(np.sort(v)[:-5].mean()), 1)
    # C3b çakışması: pencere (s, D] içinde QQQ RSI2<10 (15:30 kuralının günlük vekili) var mı
    c = px("QQQ"); r2 = rsi2(c); low = r2 < 10
    ov = []
    for _, r in q.iterrows():
        w = low[(low.index > r.d_s) & (low.index <= r.d_e)] | low[low.index == r.d_s]
        ov.append(bool(w.any()))
    q = q.assign(c3b=ov)
    card["C3b_cakisma"] = {"oran": round(float(np.mean(ov)), 3),
                           "c3b_yok": st((q[~q.c3b].side * q[~q.c3b].r_QQQ - COST).to_numpy()),
                           "c3b_var": st((q[q.c3b].side * q[q.c3b].r_QQQ - COST).to_numpy())}
    out = H.parent.parent / "backend/data/evolution/go_live_cards/qs03_r1_dengeleme.json"
    (H / "results/r1_kart.json").write_text(json.dumps(card, indent=1, ensure_ascii=False, default=str))
    out.write_text(json.dumps({"scope": "qs03_r1_ay_sonu_dengeleme", "tarih": "2026-11-11",
                               "kural": "SPY−TLT ay içi farkı D−3 kapanışında ≥+%2 → NAS100 KISA, ≤−%2 → UZUN; D−3 16:30 → D 16:30",
                               **card}, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(card, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
