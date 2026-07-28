"""miner.py — filtre madenciliğinin istatistik omurgası (dürüstlük burada yaşar).

Kullanım (araştırmacı ajanlar bunu import eder):
    from miner import Lab
    lab = Lab(direction="BUY")               # grid evreni
    lab.base()                               # taban istatistik (TRAIN/VAL/TEST)
    lab.eval_mask(mask)                      # bir kuralın üç bölümdeki karnesi
    lab.scan_single(cols)                    # tek-koşullu tarama (SADECE TRAIN'de eşik seçer)
    lab.verify(mask, label)                  # tam denetim: OOS + blok-bootstrap + placebo

DÜRÜSTLÜK KURALLARI
-------------------
* Bölünme KRONOLOJİK: TRAIN → (purge) → VAL → (purge) → TEST. Purge = 2 gün,
  çünkü bir işlem en fazla 1440 piyasa dakikası (~1 gün) açık kalır; böylece
  bölümler arasında etiket örtüşmesi kalmaz.
* Eşik/kural SEÇİMİ yalnız TRAIN'de; ön eleme VAL'de; TEST'e yalnız BİR KEZ
  bakılır ve sonuç ne olursa olsun raporlanır.
* Örtüşen etiketler → i.i.d. DEĞİL. Tüm güven aralıkları ve p-değerleri
  GÜN BLOKLU bootstrap/permütasyon ile hesaplanır (aynı günün işlemleri
  birlikte örneklenir).
* Placebo: aynı seçiciliğe sahip RASTGELE maskeler (gün blokları korunarak)
  → gerçek kuralın EV'si rastgele alt kümelerin kaçını geçiyor?
* Hiçbir metrik "kazanan" seçilmeden önce TEST'ten okunamaz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
RNG = np.random.default_rng(20260728)

PURGE_DAYS = 2
# Kronolojik sınırlar (veri 2026-02-23 → 2026-07-26 ızgarada)
SPLIT_TRAIN_END = pd.Timestamp("2026-05-05", tz="UTC")
SPLIT_VAL_END = pd.Timestamp("2026-06-12", tz="UTC")

# TP80/SL110 + 1p sürtünme geometrisinin başabaş kazanma oranı
WIN_R = (80 - 1) / 110
LOSS_R = -(110 + 1) / 110
BREAKEVEN_WR = -LOSS_R / (WIN_R - LOSS_R)


@dataclass
class Stat:
    n: int
    wr: float
    ev: float
    total_r: float

    def __str__(self) -> str:
        return f"n={self.n:5d} WR={self.wr*100:5.1f}% EV={self.ev:+.4f}R tot={self.total_r:+7.1f}R"


def _stat(x: pd.DataFrame) -> Stat:
    if len(x) == 0:
        return Stat(0, float("nan"), float("nan"), 0.0)
    return Stat(len(x), float(x.outcome.mean()), float(x.r.mean()), float(x.r.sum()))


@dataclass
class Lab:
    direction: str = "BUY"
    source: str = "grid"            # "grid" (evren) | "episodes" (gerçek pulse)
    df: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        f = "grid.parquet" if self.source == "grid" else "episodes.parquet"
        d = pd.read_parquet(DATA / f)
        d["ts"] = pd.to_datetime(d["ts"], utc=True)
        d = d[d.direction == self.direction].sort_values("ts").reset_index(drop=True)
        d["day"] = d.ts.dt.tz_convert("America/New_York").dt.date
        d["split"] = np.where(
            d.ts < SPLIT_TRAIN_END - pd.Timedelta(days=PURGE_DAYS), "train",
            np.where(d.ts < SPLIT_TRAIN_END, "purge",
                     np.where(d.ts < SPLIT_VAL_END - pd.Timedelta(days=PURGE_DAYS), "val",
                              np.where(d.ts < SPLIT_VAL_END, "purge", "test"))))
        self.df = d

    # ── temel ──────────────────────────────────────────────────────────────
    def part(self, split: str) -> pd.DataFrame:
        return self.df[self.df.split == split]

    def base(self) -> dict[str, Stat]:
        return {s: _stat(self.part(s)) for s in ("train", "val", "test")}

    def eval_mask(self, mask: pd.Series) -> dict[str, Stat]:
        m = mask.reindex(self.df.index).fillna(False).astype(bool)
        return {s: _stat(self.df[m & (self.df.split == s)])
                for s in ("train", "val", "test")}

    # ── tek koşullu tarama (yalnız TRAIN'de eşik seçer) ────────────────────
    def scan_single(self, cols: list[str], quantiles=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8),
                    min_n_train: int = 300, min_n_val: int = 80) -> pd.DataFrame:
        tr = self.part("train")
        base_tr = _stat(tr)
        rows = []
        for c in cols:
            if c not in self.df.columns:
                continue
            v = pd.to_numeric(self.df[c], errors="coerce")
            if v.notna().sum() < len(v) * 0.5 or v.nunique() < 5:
                continue
            for q in quantiles:
                thr = float(np.nanquantile(v[self.df.split == "train"], q))
                for op in (">", "<"):
                    mask = (v > thr) if op == ">" else (v < thr)
                    mask = mask.fillna(False)
                    st = self.eval_mask(mask)
                    if st["train"].n < min_n_train or st["val"].n < min_n_val:
                        continue
                    rows.append(dict(col=c, op=op, thr=thr, q=q,
                                     n_tr=st["train"].n, ev_tr=st["train"].ev,
                                     wr_tr=st["train"].wr,
                                     n_val=st["val"].n, ev_val=st["val"].ev,
                                     wr_val=st["val"].wr,
                                     lift_tr=st["train"].ev - base_tr.ev))
        r = pd.DataFrame(rows)
        return r.sort_values("lift_tr", ascending=False) if len(r) else r

    # ── blok bootstrap (gün bazlı) ─────────────────────────────────────────
    def block_bootstrap_ev(self, x: pd.DataFrame, n_boot: int = 3000) -> tuple[float, float, float]:
        if len(x) == 0:
            return (float("nan"),) * 3
        days = x.day.unique()
        by_day = {d: x.r.values[x.day.values == d] for d in days}
        evs = np.empty(n_boot)
        for i in range(n_boot):
            pick = RNG.choice(days, size=len(days), replace=True)
            vals = np.concatenate([by_day[d] for d in pick])
            evs[i] = vals.mean()
        return float(np.quantile(evs, 0.05)), float(np.median(evs)), float(np.quantile(evs, 0.95))

    def p_ev_positive(self, x: pd.DataFrame, n_boot: int = 3000) -> float:
        if len(x) == 0:
            return float("nan")
        days = x.day.unique()
        by_day = {d: x.r.values[x.day.values == d] for d in days}
        cnt = 0
        for _ in range(n_boot):
            pick = RNG.choice(days, size=len(days), replace=True)
            vals = np.concatenate([by_day[d] for d in pick])
            cnt += vals.mean() > 0
        return cnt / n_boot

    # ── placebo: aynı seçicilikte rastgele GÜN-BLOKLU maskeler ─────────────
    def placebo_p(self, mask: pd.Series, split: str = "test",
                  n_iter: int = 2000) -> float:
        """Kuralın EV'si, aynı büyüklükteki rastgele alt kümelerin kaçından iyi?

        Rastgelelik gün bloklu: aynı sayıda İŞLEM seçilir ama günler rastgele
        sıralanıp ardışık alınır → zaman kümelenmesi korunur (naif i.i.d.
        permütasyon kenarı olmayan kuralları bile 'anlamlı' gösterebilir).
        """
        d = self.df[self.df.split == split]
        m = mask.reindex(self.df.index).fillna(False).astype(bool)
        sel = d[m.loc[d.index]]
        k = len(sel)
        if k == 0 or len(d) == 0:
            return float("nan")
        real = sel.r.mean()
        days = list(d.day.unique())
        by_day = {dd: d.r.values[d.day.values == dd] for dd in days}
        worse = 0
        for _ in range(n_iter):
            order = RNG.permutation(len(days))
            acc, tot = [], 0
            for idx in order:
                v = by_day[days[idx]]
                acc.append(v)
                tot += len(v)
                if tot >= k:
                    break
            vals = np.concatenate(acc)[:k]
            worse += vals.mean() >= real
        return worse / n_iter

    # ── tam denetim ────────────────────────────────────────────────────────
    def verify(self, mask: pd.Series, label: str, verbose: bool = True) -> dict:
        st = self.eval_mask(mask)
        base = self.base()
        m = mask.reindex(self.df.index).fillna(False).astype(bool)
        test = self.df[m & (self.df.split == "test")]
        lo, med, hi = self.block_bootstrap_ev(test)
        p_pos = self.p_ev_positive(test)
        p_plac = self.placebo_p(mask, "test")
        res = dict(label=label,
                   train=str(st["train"]), val=str(st["val"]), test=str(st["test"]),
                   base_test=str(base["test"]),
                   lift_test=(st["test"].ev - base["test"].ev) if st["test"].n else float("nan"),
                   boot_ev_p05=lo, boot_ev_med=med, boot_ev_p95=hi,
                   p_ev_positive=p_pos, placebo_p=p_plac,
                   coverage_test=st["test"].n / max(base["test"].n, 1))
        if verbose:
            print(f"\n── {label}")
            print(f"   TRAIN {st['train']}")
            print(f"   VAL   {st['val']}")
            print(f"   TEST  {st['test']}   (taban {base['test']})")
            print(f"   TEST lift={res['lift_test']:+.4f}R  kapsam=%{res['coverage_test']*100:.0f}")
            print(f"   blok-bootstrap EV [5%,50%,95%] = [{lo:+.3f}, {med:+.3f}, {hi:+.3f}]  "
                  f"P(EV>0)={p_pos*100:.1f}%")
            print(f"   placebo p={p_plac:.3f}  (aynı boyda rastgele alt kümelerin oranı)")
        return res

    # ── purge'lü yürüyen-ileri (kural SABİT, zaman dilimlerinde kararlılık) ─
    def stability(self, mask: pd.Series, k: int = 6) -> pd.DataFrame:
        m = mask.reindex(self.df.index).fillna(False).astype(bool)
        edges = pd.qcut(self.df.ts.rank(method="first"), k, labels=False)
        rows = []
        for i in range(k):
            blk = self.df[edges == i]
            sel = blk[m.loc[blk.index]]
            base = _stat(blk)
            s = _stat(sel)
            rows.append(dict(fold=i, start=blk.ts.min().date(), end=blk.ts.max().date(),
                             n=s.n, wr=s.wr, ev=s.ev,
                             base_ev=base.ev, lift=(s.ev - base.ev) if s.n else np.nan))
        return pd.DataFrame(rows).round(4)

    def wf_select_eval(self, col: str, op: str, k: int = 5,
                       quantiles=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8),
                       min_n: int = 100) -> pd.DataFrame:
        """GERÇEK yürüyen-ileri: her katmanda eşik SADECE geçmişten seçilir,
        sonra bir sonraki dilimde (purge'lü) körlemesine uygulanır."""
        v = pd.to_numeric(self.df[col], errors="coerce")
        edges = pd.qcut(self.df.ts.rank(method="first"), k, labels=False)
        rows = []
        for i in range(1, k):
            past = self.df[edges < i]
            fut = self.df[edges == i]
            cut = fut.ts.min() - pd.Timedelta(days=PURGE_DAYS)
            past = past[past.ts < cut]
            if len(past) < 500:
                continue
            best, best_ev = None, -9e9
            for q in quantiles:
                thr = float(np.nanquantile(v.loc[past.index], q))
                m = (v.loc[past.index] > thr) if op == ">" else (v.loc[past.index] < thr)
                sel = past[m.fillna(False)]
                if len(sel) < min_n:
                    continue
                if sel.r.mean() > best_ev:
                    best, best_ev = thr, sel.r.mean()
            if best is None:
                continue
            mf = (v.loc[fut.index] > best) if op == ">" else (v.loc[fut.index] < best)
            sel_f = fut[mf.fillna(False)]
            rows.append(dict(fold=i, thr=round(best, 4), n=len(sel_f),
                             wr=sel_f.outcome.mean() if len(sel_f) else np.nan,
                             ev=sel_f.r.mean() if len(sel_f) else np.nan,
                             base_ev=fut.r.mean(),
                             lift=(sel_f.r.mean() - fut.r.mean()) if len(sel_f) else np.nan))
        return pd.DataFrame(rows).round(4)

    # ── zaman dilimi kararlılığı ───────────────────────────────────────────
    def by_month(self, mask: pd.Series) -> pd.DataFrame:
        m = mask.reindex(self.df.index).fillna(False).astype(bool)
        x = self.df[m].copy()
        x["ay"] = x.ts.dt.to_period("M")
        return x.groupby("ay").agg(n=("r", "size"), wr=("outcome", "mean"),
                                   ev=("r", "mean"), tot=("r", "sum")).round(3)


def friction_sensitivity(mask: pd.Series, direction: str, frictions=(0.0, 1.0, 2.0, 4.0)) -> pd.DataFrame:
    """Aynı maskeyi farklı sürtünme varsayımlarıyla yeniden fiyatla.

    Sonuç TP/SL vuruş sırasını değiştirmez (fiyat seviyeleri kayar ama etki
    küçüktür); burada muhafazakâr yaklaşım: kazanç −f, kayıp −f eklenir.
    """
    lab = Lab(direction=direction)
    m = mask.reindex(lab.df.index).fillna(False).astype(bool)
    out = []
    for f in frictions:
        x = lab.df[m & (lab.df.split == "test")].copy()
        r = np.where(x.outcome == 1, (80 - f) / 110, -(110 + f) / 110)
        out.append(dict(friction=f, n=len(x), wr=x.outcome.mean(),
                        ev=r.mean(), total=r.sum()))
    return pd.DataFrame(out)
