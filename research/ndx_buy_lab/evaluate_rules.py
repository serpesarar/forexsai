"""evaluate_rules.py — aday kuralların BAĞIMSIZ ve TEK SEFERLİK denetimi.

Beş kapı (hepsinden geçmeyen kural rapora "doğrulandı" diye giremez):

  K1 ÜRETİLEBİLİRLİK  Ajanın bildirdiği TRAIN/VAL sayıları burada YENİDEN
                      hesaplanır. Sapma varsa kural "sayı uyuşmuyor" damgası yer.
  K2 ETKİN ÖRNEKLEM   n değil, BENZERSİZ GÜN sayısı. Makro/günlük özellikler tüm
                      günü aynı değere sabitler → n=1500 ama etkin n=25 olabilir.
  K3 KÖR TEST         Birincil ızgaranın TEST bölümü (2026-06-12 → 07-25).
                      Buraya SADECE BİR KEZ bakılır.
  K4 UZUN GEÇMİŞ      2023-03 → 2026-02-22: madencilerin HİÇ görmediği 3 yıl.
                      Farklı rejimler, farklı volatilite, farklı faiz ortamı.
  K5 GERÇEK SİNYAL    Botun asıl tükettiği pulse BUY epizodları (canlı akış).

Ek: gün-bloklu bootstrap %5-%95 aralığı, placebo p-değeri, sürtünme duyarlılığı.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from miner import DATA, Lab, _stat

SAFE = re.compile(r"^[A-Za-z0-9_\.\s\(\)\&\|\~\<\>\=\!\+\-\*\/,%\']+$")
LONG_MINE_CUTOFF = pd.Timestamp("2026-02-23", tz="UTC")


def mask_of(df: pd.DataFrame, expr: str) -> pd.Series | None:
    if not SAFE.match(expr):
        print(f"  ! güvensiz ifade atlandı: {expr}")
        return None
    try:
        m = eval(expr, {"__builtins__": {}}, {"d": df, "np": np, "pd": pd})
    except Exception as e:
        print(f"  ! ifade hatası ({e}): {expr}")
        return None
    if not isinstance(m, pd.Series):
        return None
    return m.fillna(False).astype(bool)


def eff_n(x: pd.DataFrame) -> int:
    return int(x.day.nunique()) if len(x) else 0


def block_ci(x: pd.DataFrame, n_boot: int = 2000, seed: int = 7) -> tuple[float, float, float]:
    if len(x) == 0:
        return (np.nan,) * 3
    rng = np.random.default_rng(seed)
    days = x.day.unique()
    by = {d: x.r.values[x.day.values == d] for d in days}
    ev = np.empty(n_boot)
    for i in range(n_boot):
        pick = rng.choice(days, size=len(days), replace=True)
        ev[i] = np.concatenate([by[d] for d in pick]).mean()
    return float(np.quantile(ev, 0.05)), float(np.median(ev)), float(np.quantile(ev, 0.95))


def load_long() -> pd.DataFrame:
    lg = pd.read_parquet(DATA / "long_grid.parquet")
    lg["ts"] = pd.to_datetime(lg["ts"], utc=True)
    lg = lg[lg.direction == "BUY"].copy()
    lg["day"] = lg.ts.dt.tz_convert("America/New_York").dt.date
    return lg


def evaluate(rules: list[dict], out_path: Path) -> pd.DataFrame:
    lab = Lab(direction="BUY", source="grid")
    epi = Lab(direction="BUY", source="episodes")
    lg = load_long()
    lg_hold = lg[lg.ts < LONG_MINE_CUTOFF]

    base = lab.base()
    base_hold = _stat(lg_hold)
    base_epi = epi.base()
    print(f"TABANLAR  grid: train {base['train']} | val {base['val']} | test {base['test']}")
    print(f"          uzun holdout (2023-03→2026-02-22): {base_hold}  gün={eff_n(lg_hold)}")
    print(f"          pulse epizod test: {base_epi['test']}\n")

    rows = []
    for r in rules:
        expr, name = r["expr"], r["name"]
        m = mask_of(lab.df, expr)
        if m is None:
            continue
        st = lab.eval_mask(m)
        # K1 üretilebilirlik
        d_tr = abs(st["train"].ev - r.get("ev_train", np.nan))
        d_va = abs(st["val"].ev - r.get("ev_val", np.nan))
        repro = "OK" if (d_tr < 0.02 and d_va < 0.02) else f"SAPMA tr{d_tr:.3f}/val{d_va:.3f}"

        test = lab.df[m & (lab.df.split == "test")]
        lo, med, hi = block_ci(test)
        plac = lab.placebo_p(m, "test", n_iter=1000)

        # K4 uzun holdout
        mh = mask_of(lg_hold, expr)
        if mh is None:
            st_h, ci_h, effh = None, (np.nan,) * 3, 0
        else:
            st_h = _stat(lg_hold[mh])
            ci_h = block_ci(lg_hold[mh])
            effh = eff_n(lg_hold[mh])

        # K5 gerçek pulse epizodları (tüm dönem — n zaten çok küçük)
        me = mask_of(epi.df, expr)
        st_e = _stat(epi.df[me]) if me is not None else None

        rows.append(dict(
            aile=r.get("family", ""), ad=name, expr=expr, uretilebilir=repro,
            n_tr=st["train"].n, ev_tr=st["train"].ev,
            n_val=st["val"].n, ev_val=st["val"].ev,
            n_test=st["test"].n, wr_test=st["test"].wr, ev_test=st["test"].ev,
            lift_test=st["test"].ev - base["test"].ev,
            eff_gun_test=eff_n(test), boot_p05=lo, boot_p95=hi, placebo_p=plac,
            n_long=st_h.n if st_h else 0, wr_long=st_h.wr if st_h else np.nan,
            ev_long=st_h.ev if st_h else np.nan,
            lift_long=(st_h.ev - base_hold.ev) if st_h else np.nan,
            eff_gun_long=effh, long_p05=ci_h[0], long_p95=ci_h[2],
            n_epi=st_e.n if st_e else 0, wr_epi=st_e.wr if st_e else np.nan,
            ev_epi=st_e.ev if st_e else np.nan,
        ))
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    return df


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "mining_round1.json"
    fams = json.loads(src.read_text())
    rules = []
    for f in fams:
        if not isinstance(f, dict):
            continue
        for kind in ("entry_rules", "avoid_rules"):
            for r in f.get(kind, []):
                r = dict(r)
                r["family"] = f.get("family", "")
                r["kind"] = kind
                rules.append(r)
    print(f"{len(rules)} aday kural değerlendiriliyor…\n")
    df = evaluate(rules, DATA / "rule_eval.csv")
    pd.set_option("display.width", 250)
    show = df[["aile", "ad", "uretilebilir", "n_test", "ev_test", "lift_test",
               "eff_gun_test", "placebo_p", "n_long", "ev_long", "lift_long",
               "eff_gun_long", "n_epi", "ev_epi"]]
    print(show.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
