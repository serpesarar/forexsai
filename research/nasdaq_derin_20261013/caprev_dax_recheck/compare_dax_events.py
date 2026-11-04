"""DAX olay karşılaştırması: ORJ (etiketler gerçeğe çevrilerek) ↔ DAXfix. Her olay için: tarih, tetik barı (gerçek UTC
ve Berlin), pdl, r1/r5/dvol, R_d0 değişimi."""
from pathlib import Path
import numpy as np, pandas as pd
R = Path(__file__).resolve().parent / "results"
H = pd.Timedelta(minutes=60)
def load(k):
    x = pd.read_csv(R / f"trades_{k}.csv", parse_dates=["nyd", "trig_ts", "entry_ts", "exit_ts"])
    return x[x.m == "DAX"].set_index("nyd")
o, f = load("ORJ"), load("DAXfix")
for c in ("trig_ts", "entry_ts", "exit_ts"):          # ORJ etiketini gerçeğe çevir
    std = ~o[c].dt.tz_convert("America/New_York").map(lambda t: bool(t.dst()))
    o[c + "_gercek"] = o[c] + pd.to_timedelta(np.where(std.to_numpy(), 60, 0), unit="min")
    if c == "trig_ts":
        o["kis"] = std.to_numpy()
dates = sorted(set(o.index) | set(f.index))
rows = []
for d in dates:
    a, b = (o.loc[d] if d in o.index else None), (f.loc[d] if d in f.index else None)
    r = {"tarih": d.date(), "kis(NYstd)": bool(a.kis) if a is not None else None}
    if a is None or b is None:
        r["durum"] = "yalnız ORJ" if b is None else "yalnız DÜZELTİLMİŞ"
    else:
        same_bar = a.trig_ts_gercek == b.trig_ts
        r["durum"] = "aynı" if (same_bar and np.isclose(a.pdl, b.pdl) and np.isclose(a.dvol, b.dvol) and np.isclose(a.R_d0, b.R_d0, atol=1e-6)) else "değişti"
        r["tetik_ayni"] = bool(same_bar); r["pdl_ayni"] = bool(np.isclose(a.pdl, b.pdl)); r["dvol_ayni"] = bool(np.isclose(a.dvol, b.dvol))
    for nm, z in (("orj", a), ("fix", b)):
        if z is not None:
            t = z.trig_ts_gercek if nm == "orj" else z.trig_ts
            r[f"tetik_Berlin_{nm}"] = t.tz_convert("Europe/Berlin").strftime("%H:%M")
            r[f"pdl_{nm}"] = round(float(z.pdl), 1); r[f"R_{nm}"] = round(float(z.R_d0), 3)
            r[f"r1_{nm}"] = round(float(z.r1), 4)
    if a is not None:
        r["orj_cikis_Berlin_gercek"] = a.exit_ts_gercek.tz_convert("Europe/Berlin").strftime("%H:%M")
    rows.append(r)
t = pd.DataFrame(rows)
t.to_csv(R / "dax_event_diff.csv", index=False)
print(t.durum.value_counts().to_string())
print("kış olayları:", int(t["kis(NYstd)"].fillna(False).sum()))
print(t[t.durum != "aynı"].to_string(index=False))
ch = t[t.durum == "değişti"]
nb = lambda col: int((ch[col].astype(bool) == False).sum())
print("\ndeğişen olaylarda: tetik farklı", nb("tetik_ayni"), "pdl farklı", nb("pdl_ayni"), "dvol farklı", nb("dvol_ayni"))
kis = t["kis(NYstd)"].fillna(False).astype(bool)
print("kış (NY std) olayları durum:", t[kis].durum.value_counts().to_dict(), "| yaz:", t[~kis].durum.value_counts().to_dict())
ch2 = ch.assign(dR=ch.R_fix - ch.R_orj)
print("değişen olayların R farkı: kış toplam", round(ch2[kis[ch.index]].dR.sum(), 2), "yaz toplam", round(ch2[~kis[ch.index]].dR.sum(), 2))
print("R toplamı ORJ", round(o.R_d0.sum(), 2), "FIX", round(f.R_d0.sum(), 2))
print("ORJ gerçek çıkış Berlin saatleri:", o.exit_ts_gercek.dt.tz_convert("Europe/Berlin").dt.strftime("%H:%M").value_counts().to_dict())
print("ORJ gerçek tetik Berlin saatleri (kış):", o[o.kis].trig_ts_gercek.dt.tz_convert("Europe/Berlin").dt.strftime("%H:%M").value_counts().sort_index().to_dict())
print("FIX çıkış Berlin:", f.exit_ts.dt.tz_convert("Europe/Berlin").dt.strftime("%H:%M").value_counts().to_dict())
