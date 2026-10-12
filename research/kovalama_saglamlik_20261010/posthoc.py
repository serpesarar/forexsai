"""Ön-kayıt SONRASI (keşif, kanıt değil): örtüşme ve seans karıştırıcıları. python3 research/kovalama_saglamlik_20261010/posthoc.py"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ks_run", HERE / "run.py")
K = importlib.util.module_from_spec(spec)
sys.modules["ks_run"] = K
spec.loader.exec_module(K)


def sess(t: pd.Series) -> np.ndarray:
    h = t.dt.hour.to_numpy()
    return np.where((h >= 13) & (h < 20), "US 13-20", np.where((h >= 7) & (h < 13), "EU 07-13", "ASYA/gece"))


def main() -> None:
    L = ["# Ön-kayıt sonrası keşif kontrolleri (kanıt sınıfı düşürücü/yükseltici değil, yorum için)"]
    bot = K.bot_df()
    mk = K.Market()
    bt = bot.t.to_numpy(dtype="datetime64[ns]")
    pn_ts, pn_ex = K.panel_events()
    pn = mk.table(pn_ts, "G1", pn_ex)
    near = np.array([np.abs((bt - np.datetime64(t.tz_convert(None))).astype("timedelta64[m]").astype(float)).min() <= 30
                     for t in pn.t])
    pn["bot_yakin"] = near
    K.block(pn[~near].reset_index(drop=True), "C-x) Panel SELL, bot SELL girişinin ±30 dk'sı HARİÇ", L)
    K.block(pn[near].reset_index(drop=True), "C-y) Panel SELL, bot SELL girişine ±30 dk YAKIN", L)
    sk_ts, sk_ex = K.skipped_events(bot)
    sk = mk.table(sk_ts, "G1", sk_ex)
    gen = mk.table(K.generic_events(mk), "G1")
    gen_all = mk.table([t for t in mk.sb.m1.index[(mk.sb.m1.index.minute == 0) & (mk.sb.m1.index.dayofweek < 5)]
                        if K.P_START <= t <= K.P_END], "G1")
    for nm, d in (("bot", bot), ("engellenen", sk), ("panel", pn), ("piyasa 24s", gen_all)):
        d = d.copy()
        d["seans"] = sess(d.t)
        L.append(f"\n## {nm} — seansa göre (n: " + str(d.seans.value_counts().to_dict()) + ")")
        for s, g in d.groupby("seans"):
            for c in ("C1", "C2"):
                L.append(K.line(g.reset_index(drop=True), c, s))
    L.append("\n## F') Fark-içinde-fark: panel SELL (bot-yakın HARİÇ) vs aynı dönem piyasa (06-20 UTC)")
    K.did(pn[~near].reset_index(drop=True), gen, "C1", L)
    K.did(pn[~near].reset_index(drop=True), gen, "C2", L)
    txt = "\n".join(L)
    (K.OUT / "posthoc.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
