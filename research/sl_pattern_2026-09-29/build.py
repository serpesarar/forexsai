"""İşlem veri seti: bot_trades (+ canlı giriş satırları) + broker 1m yolu → trades.pkl

Zaman: bot_trades open/close_time BROKER saati (UTC+3) '+00' etiketli → −3s.
Log asctime kutu yereli (UTC−4, EDT) → +4s.
"""
import re
import numpy as np
import pandas as pd

BROKER_OFF = pd.Timedelta(hours=3)
BOX_OFF = pd.Timedelta(hours=4)
SYM = {"SpotCrude": "USOIL.FOREX", "NAS100": "NDX.INDX", "GER40": "GDAXI.INDX"}

bt = pd.read_pickle("bot_trades.pkl")
bt["position_id"] = bt["raw"].apply(lambda r: (r or {}).get("position_id"))
bt["reason"] = bt["raw"].apply(lambda r: (r or {}).get("reason"))
bt["open_utc"] = pd.to_datetime(bt["open_time"]) - BROKER_OFF
bt["close_utc"] = pd.to_datetime(bt["close_time"]) - BROKER_OFF
bt["sym"] = bt["symbol"].map(SYM)
bt = bt[bt["sym"].notna()].copy()

# canlı giriş satırları
rx = re.compile(r"^(\S+ \S+)\s+INFO\s+\[CANLI\] ✅ (LIMIT kuruldu|Açıldı|Reflex açıldı) "
                r"ticket=(\d+).*?→ (\S+) \| (\S+) (BUY|SELL)(?: LIMIT)? @ ([\d.]+) "
                r"TP=([\d.]+)(?:\[(\w+)\])? SL=([\d.]+) lot=([\d.]+)(.*)$")
rows = []
for ln in open("canli_lines.txt", encoding="utf-8"):
    m = rx.match(ln.strip())
    if not m:
        continue
    ts, kind, tk, scope, msym, d, px, tp, tpsrc, sl, lot, rest = m.groups()
    voters = re.search(r"oy: ([^)]*)", rest)
    fiyat = re.search(r"fiyat=([\d.]+)", rest)
    rows.append(dict(sig_utc=pd.Timestamp(ts.replace(",", ".")).tz_localize("UTC") + BOX_OFF,
                     entry_kind="limit" if "LIMIT" in kind else "market",
                     position_id=int(tk), scope=scope, plan_entry=float(px),
                     tp0=float(tp), sl0=float(sl), tp_src=tpsrc or "", lot0=float(lot),
                     voters=(voters.group(1) if voters else ""),
                     sig_price=float(fiyat.group(1)) if fiyat else np.nan))
cl = pd.DataFrame(rows)
print("canlı satır:", len(cl), "eşleşmeyen:", sum(1 for _ in open("canli_lines.txt")) - len(cl))

# parmak izleri (voters limit girişlerde burada)
fp = pd.read_pickle("fingerprints.pkl")
fpm = {int(r.ticket): r for r in fp.itertuples()}
cl["voters"] = [v if v else ("|".join(fpm[p].voters) if p in fpm and fpm[p].voters else "")
                for v, p in zip(cl["voters"], cl["position_id"])]

df = bt.merge(cl, on="position_id", how="left")
print("işlem:", len(df), "giriş satırı eşleşen:", df["scope"].notna().sum())
# eşleşmeyenlerde başlangıç SL/TP = kapanıştaki
df["tp0"] = df["tp0"].fillna(df["tp"])
df["sl0"] = df["sl0"].fillna(df["sl"])
df["dir"] = df["direction"]
sgn = np.where(df["dir"] == "BUY", 1.0, -1.0)
df["risk"] = (df["open_price"] - df["sl0"]) * sgn          # SL mesafesi (fiyat)
df["reward"] = (df["tp0"] - df["open_price"]) * sgn
df["rr"] = df["reward"] / df["risk"]
df["R_real"] = (df["close_price"] - df["open_price"]) * sgn / df["risk"]
df["exit"] = df["comment"].str.extract(r"\[(tp|sl)")[0].fillna("other")
df["dur_min"] = (df["close_utc"] - df["open_utc"]).dt.total_seconds() / 60
df.to_pickle("trades_base.pkl")
print(df.groupby(["sym", "dir"]).agg(n=("profit", "size"), pnl=("profit", "sum"),
                                      rr=("rr", "median"), win=("profit", lambda x: (x > 0).mean())))
print(df["exit"].value_counts())
print(df[df.position_id == 390567007][["open_utc", "close_utc", "open_price", "close_price",
                                         "tp0", "sl0", "rr", "R_real", "voters", "scope"]].T)
