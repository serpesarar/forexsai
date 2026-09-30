"""indicator_snapshots zaman ekseni onarımı: etiket < 2026-07-28 18:00 → broker saati (−3s);
2026-07-28 18:00–21:00 arası belirsiz → at; sonrası UTC."""
import pandas as pd
CUT1 = pd.Timestamp("2026-07-28 18:00", tz="UTC"); CUT2 = pd.Timestamp("2026-07-28 21:00", tz="UTC")
def load(sym, tf):
    m = pd.read_pickle(f"is_{sym}_{tf}.pkl")
    m["t"] = pd.to_datetime(m["candle_time"])
    m = m[(m.t < CUT1) | (m.t >= CUT2)].copy()
    m.loc[m.t < CUT1, "t"] = m.loc[m.t < CUT1, "t"] - pd.Timedelta(hours=3)
    return m.drop_duplicates("t", keep="last").set_index("t").sort_index()
if __name__ == "__main__":
    for s in ["USOIL.FOREX", "NDX.INDX", "GDAXI.INDX"]:
        for tf in ["1m", "5m", "15m", "1h"]:
            load(s, tf).to_pickle(f"fx_{s}_{tf}.pkl")
    print("ok")
