"""Komut satırı: python3 -m scripts.islem_otopsi [--symbol NDX] [--days 14] ...

Salt-okuma: Supabase'ten okur, yerel klasöre yazar. Emir/süreç/kapı DEĞİŞTİRMEZ.
Çıkış kodu: 0 tamam · 2 saat ekseni MISALIGNED (rapor yazılır, analiz yapılmaz) · 3 veri yok.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import align, analogs, build, charts, compare, data, dynamics, narrative, placebo, report
from . import settings as S
from .indicators import SymbolBars

log = logging.getLogger("islem_otopsi")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bot işlemleri için derin SL/TP otopsisi")
    p.add_argument("--symbol", default="all", help="NDX, DAX, USOIL, XAU (virgülle) veya all")
    p.add_argument("--family", default="", help="VIXREG, MOMSR, CHREV, DAYCOMBO, REENTRY, DECIDER… (virgülle)")
    p.add_argument("--days", type=int, default=S.DEFAULT_FOCUS_DAYS, help="odak penceresi (son N gün)")
    p.add_argument("--base-days", type=int, default=S.DEFAULT_BASE_DAYS, help="kıyas tabanı (toplam geçmiş)")
    p.add_argument("--since", default="", help="odak başlangıcı (ISO, UTC) — --days yerine")
    p.add_argument("--until", default="", help="bu andan sonra AÇILAN işlemleri dışla (ISO, UTC)")
    p.add_argument("--max-cards", type=int, default=40)
    p.add_argument("--trade-charts", type=int, default=8, help="grafikli işlem kartı sayısı (önce SL'ler)")
    p.add_argument("--refresh", action="store_true", help="mum önbelleğini yok say")
    p.add_argument("--no-vix", action="store_true")
    p.add_argument("--force", action="store_true", help="MISALIGNED olsa da devam et (önerilmez)")
    p.add_argument("--out", default="")
    p.add_argument("--pid", default="", help="bu pozisyon(lar) için ayrıntılı tekil otopsi dosyası (virgülle)")
    return p.parse_args(argv)


def _symbols(arg: str) -> list[str] | None:
    if arg.lower() in ("", "all", "hepsi"):
        return None
    syms = [S.SYMBOL_ALIASES.get(x.strip().upper()) for x in arg.split(",")]
    bad = [x for x, s in zip(arg.split(","), syms) if s is None]
    if bad:
        sys.exit(f"Bilinmeyen sembol: {bad} — seçenekler: NDX, DAX, USOIL, XAU")
    return syms


def _filter(tr: pd.DataFrame, a: argparse.Namespace) -> pd.DataFrame:
    syms = _symbols(a.symbol)
    if syms:
        tr = tr[tr["symbol"].isin(syms)]
    if a.family:
        fams = {x.strip().upper() for x in a.family.split(",")}
        tr = tr[tr["family"].str.upper().isin(fams)]
    return tr.reset_index(drop=True)


def _need_ranges(tr: pd.DataFrame) -> dict:
    need = {}
    pad = pd.Timedelta(minutes=S.POST_EXIT_MIN + 60)
    for sym, g in tr.groupby("symbol"):
        need[sym] = (g["open_raw"].min() - pd.Timedelta(days=S.WARMUP_DAYS) - pd.Timedelta(hours=4),
                     g["close_raw"].max() + pad)
    return need


def _scope(a: argparse.Namespace) -> str:
    s = a.symbol.upper() if a.symbol.lower() != "all" else "TÜM SEMBOLLER"
    return s + (f" · {a.family.upper()}" if a.family else "")


def load_everything(a: argparse.Namespace, now: pd.Timestamp) -> tuple:
    base_since = now - pd.Timedelta(days=a.base_days)
    client = data.get_client()
    tr = _filter(data.load_trades(client, base_since), a)
    if tr.empty:
        return None, None, None, None, None
    bars = data.load_bars(sorted(tr["symbol"].unique()), _need_ranges(tr), a.refresh)
    al = align.align_trades(tr, bars)
    fps = data.load_fingerprints(client, base_since)
    vix = pd.Series(dtype=float) if a.no_vix else data.load_vix(base_since, now)
    return al, bars, fps, vix, base_since


def analyse(t: pd.DataFrame, sbs: dict, a: argparse.Namespace, out_dir: Path) -> dict:
    fc = compare.feature_compare(t)
    ctx: dict = {"t": t, "fc": fc, "mix": compare.outcome_mix(t), "anatomy": compare.anatomy(t),
                 "binary": compare.binary_conditionals(t), "interactions": compare.interactions(t, fc),
                 "candidates": compare.veto_candidates(t, fc), "max_cards": a.max_cards}
    ctx["summaries"] = {"odak": compare.period_summary(t[t["period"] == "focus"]) if (t["period"] == "focus").any() else {},
                        "keşif": compare.period_summary(t[t["period"] == "disc"]) if (t["period"] == "disc").any() else {},
                        "tümü": compare.period_summary(t)}
    ctx["groups"] = {"Strateji ailesi": compare.group_table(t, "family"), "Sembol · yön": compare.group_table(t, "side"),
                     "Seans": compare.group_table(t, "session"),
                     "Strateji · sembol-yön": compare.group_table(t, ["family", "side"])}
    ctx["tags"] = compare.tag_frequency(t)
    t = narrative.add_flag_weights(t, ctx["tags"])
    ctx["t"] = t
    ctx["verdicts"] = compare.verdict_table(t)
    ctx["placebo"] = placebo.summarize(placebo.run(t, sbs))
    ep = dynamics.entry_paths(t, sbs)
    ctx["divergence"] = dynamics.divergence_minute(ep)
    ctx["early"] = dynamics.early_warning(ep)
    ctx["exit_profile_md"] = report.md_table(dynamics.exit_volume_profile(t, sbs),
                                             {"SL n": report.INT, "TP n": report.INT})
    ctx["geometry"] = dynamics.geometry_whatif(t, sbs)
    _make_charts(ctx, t, sbs, ep, a, out_dir)
    return ctx


def _add_analog_lines(t: pd.DataFrame) -> pd.DataFrame:
    """Odak penceresindeki her işlemin kartına 'geçmiş benzerleri' satırı (sızıntısız kNN)."""
    t = t.copy()
    for i, r in t[t["period"] == "focus"].iterrows():
        nb = analogs.nearest(t, r)
        line = "- **Geçmiş benzerleri:** " + analogs.summary_line(nb, analogs.pool_sl_rate(t, r))
        t.at[i, "kart"] = t.at[i, "kart"].replace("\n- Etiketler:", "\n" + line + "\n- Etiketler:")
    return t


def _make_charts(ctx: dict, t: pd.DataFrame, sbs: dict, ep: dict, a: argparse.Namespace, out_dir: Path) -> None:
    img = out_dir / "grafikler"
    img.mkdir(exist_ok=True)
    if charts.divergence_chart(ep, ctx["divergence"], img / "ayrisma.png"):
        ctx["chart_divergence"] = "grafikler/ayrisma.png"
    if charts.exit_volume_chart(charts.exit_volume_curves(t, sbs), img / "hacim_cikis.png"):
        ctx["chart_exit_volume"] = "grafikler/hacim_cikis.png"
    if charts.auc_chart(ctx["fc"], img / "ozellik_ayrim.png"):
        ctx["chart_auc"] = "grafikler/ozellik_ayrim.png"
    focus = t[t["period"] == "focus"].sort_values("entry_utc", ascending=False)
    pick = pd.concat([focus[focus["outcome"] == "SL"], focus[focus["outcome"] != "SL"]]).head(a.trade_charts)
    ctx["trade_charts"] = {}
    for _, r in pick.iterrows():
        p = img / f"islem_{r['pid']}.png"
        if charts.trade_chart(r, sbs[r["symbol"]], p):
            ctx["trade_charts"][r["pid"]] = f"grafikler/{p.name}"


def _context_meta(ctx: dict, t: pd.DataFrame, al, a: argparse.Namespace, now: pd.Timestamp, focus_since) -> None:
    vs = t["pre_vol_seas_15"].dropna()
    ctx.update({
        "align": al, "scope": _scope(a), "generated": f"{now:%Y-%m-%d %H:%M} UTC", "focus_days": a.days,
        "base_days": a.base_days, "command": "python3 -m scripts.islem_otopsi " + " ".join(sys.argv[1:]),
        "vol_range": f"×{narrative.tr_num(vs.quantile(0.1))}–×{narrative.tr_num(vs.quantile(0.9))}" if len(vs) else "—",
        "stale_n": int((t["pre_stale_min"] > 10).sum()),
        "disc_span": _span(t[t["period"] == "disc"]), "focus_span": _span(t[t["period"] == "focus"]),
    })


def _span(d: pd.DataFrame) -> str:
    if d.empty:
        return "(işlem yok)"
    return f"{d['entry_utc'].min():%Y-%m-%d} → {d['entry_utc'].max():%Y-%m-%d} ({len(d)} işlem)"


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for noisy in ("httpx", "httpcore", "hpack", "yfinance", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    a = parse_args(argv)
    now = data.utc_now()
    out_dir = Path(a.out) if a.out else S.OUT_ROOT / f"{now:%Y-%m-%d_%H%M}_{a.symbol.lower()}{('_' + a.family.lower()) if a.family else ''}"
    out_dir.mkdir(parents=True, exist_ok=True)
    al, bars, fps, vix, base_since = load_everything(a, now)
    if al is None:
        print("VERİ YOK: filtreye uyan kapanmış işlem bulunamadı.")
        return 3
    print(f"Saat ekseni: {al.status} (%{al.aligned_frac * 100:.1f}, kaymalar {al.offset_counts}, dışlanan {len(al.excluded)})")
    if al.status != "ALIGNED" and not a.force:
        (out_dir / "rapor.md").write_text(report.sec_gate({"align": al, "geometry": {}, "vol_range": "—", "stale_n": 0,
                                                           "disc_span": "—", "focus_span": "—", "command": " ".join(sys.argv)}))
        print(f"DUR: saat ekseni doğrulanamadı → {out_dir / 'rapor.md'}")
        return 2
    t = al.trades
    t = t[t["entry_utc"] >= base_since]
    if a.until:
        t = t[t["entry_utc"] < pd.Timestamp(a.until)]
    sbs = {k: SymbolBars(k, v) for k, v in bars.items() if len(v)}
    t, skipped = build.build_table(t.reset_index(drop=True), sbs, fps, vix, now)
    if t.empty:
        print("VERİ YOK: özellik çıkarılabilen işlem yok.", skipped[:5])
        return 3
    al.excluded += skipped
    focus_since = pd.Timestamp(a.since) if a.since else now - pd.Timedelta(days=a.days)
    t["period"] = np.where(t["entry_utc"] >= focus_since, "focus", "disc")
    t["decision_id"] = align.assign_decisions(t)
    t = narrative.annotate(t)
    ctx = analyse(t, sbs, a, out_dir)
    t = _add_analog_lines(ctx["t"])
    ctx["t"] = t
    for pid in [int(x) for x in a.pid.split(",") if x.strip()]:
        path = report.write_trade_autopsy(t, pid, sbs, out_dir)
        print(f"TEKİL OTOPSİ: {path}")
    _context_meta(ctx, t, al, a, now, focus_since)
    t.drop(columns=[c for c in t.columns if c.startswith("_")]).to_csv(out_dir / "islemler.csv", index=False)
    ctx["fc"].to_csv(out_dir / "ozellik_kiyas.csv", index=False)
    rp = report.write_report(ctx, out_dir)
    report.write_summary_json(ctx, out_dir)
    s = ctx["summaries"]["odak"] or ctx["summaries"]["tümü"]
    print(f"İşlem {len(t)} (odak {int((t['period'] == 'focus').sum())}) · TP {s.get('tp')} / SL {s.get('sl')} · "
          f"net {s.get('net_usd', 0):,.0f} $ · ort R {s.get('ort_r', float('nan')):+.3f}")
    print(f"RAPOR: {rp}")
    return 0
