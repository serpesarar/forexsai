"""Dondurulmuş kodu bağımsız döneme taşır: kaynak dosyaları BİREBİR kopyalar, yalnız veri yolu / tarih / bölme sabitlerini
tam-eşleşmeli dizge değişimiyle değiştirir (her değişim kaynakta TAM BİR KEZ geçmeli, aksi hâlde hata).
Çıktı: scripts/port/*.py + scripts/port/PORT_DIFF.txt (unified diff) + SHA256 manifest.
Kullanım: python -I -B 00_port.py
"""
from __future__ import annotations

import difflib
import hashlib
from pathlib import Path

R = Path("/Users/melihcanodacioglu/Desktop/panel/research")
ME = R / "btc_indep_2017_2021"
PORT = ME / "scripts" / "port"
PORT.mkdir(parents=True, exist_ok=True)
D = str(ME / "data")
CA = str(ME / "cache")
RS_ = str(ME / "results")

SRC: dict[str, tuple[Path, list[tuple[str, str]]]] = {
    "build_spot.py": (R / "btc_5y_20261021/scripts/02_build_binance.py", [
        ('START = pd.Timestamp("2021-06-01", tz="UTC")', 'START = pd.Timestamp("2017-08-01", tz="UTC")'),
        ('files = sorted((raw / "monthly").glob("*.zip")) + sorted((raw / "daily").glob("*.zip"))',
         'files = sorted((raw / "spot_klines").glob("*.zip"))'),
    ]),
    "build_futures.py": (R / "btc_scalp_20261021/scripts/02_build_futures.py", [
        ('START = pd.Timestamp("2021-06-01", tz="UTC")', 'START = pd.Timestamp("2020-01-01", tz="UTC")'),
        ('END = pd.Timestamp("2026-10-21", tz="UTC")', 'END = pd.Timestamp("2021-06-01", tz="UTC")'),
    ]),
    "macro_yf.py": (R / "btc_5y_20261021/scripts/04_macro_yf.py", [
        ('START, END = "2021-05-01", "2026-10-21"', 'START, END = "2017-01-01", "2021-07-01"'),
    ]),
    "lib_trend.py": (R / "btc_5y_20261021/fam_trend/lib_trend.py", [
        ('DATA = ROOT.parent / "data"', f'DATA = Path("{D}")'),
        ('CACHE = ROOT / "cache"', f'CACHE = Path("{CA}")'),
        ('''SPLITS = {
    "DISC": (m("2021-06-01"), m("2024-01-01")),
    "OOS": (m("2024-01-11"), m("2025-07-01")),
    "BLIND": (m("2025-07-01"), m("2026-10-21")),
}''', '''SPLITS = {
    "A": (m("2017-08-17"), m("2020-01-11")),
    "PERP": (m("2020-01-11"), m("2021-06-01")),
}'''),
        ('days = pd.date_range("2021-05-20", "2026-12-01", freq="D")', 'days = pd.date_range("2017-08-01", "2021-07-01", freq="D")'),
    ]),
    "lib_st.py": (R / "btc_scalp_20261021/strateji/lib_st.py", [
        ('sys.path.insert(0, str(ROOT / "btc_5y_20261021" / "fam_trend"))\nsys.path.insert(0, str(ROOT / "btc_scalp_20261021" / "feasibility"))',
         'sys.path.insert(0, str(Path(__file__).resolve().parent))'),
        ('RES = HERE / "results"', f'RES = Path("{RS_}")'),
        ('MAX_DELAY = 10', 'MAX_DELAY = 10\nHOT_THR = 29.298164936615546  # dondurulmuş: orijinal DISC p99 |1m log getiri| (bp)'),
        ('T0M = int(pd.Timestamp("2021-06-01", tz="UTC").value // 60_000_000_000)',
         'T0M = int(pd.Timestamp("2017-08-17", tz="UTC").value // 60_000_000_000)'),
        ('''SPLITS = {"DISC": (em("2021-06-01"), em("2024-01-01")),
          "OOS": (em("2024-01-11"), em("2025-07-01")),
          "BLIND": (em("2025-07-01"), em("2026-10-21"))}''',
         '''SPLITS = {"A": (em("2017-08-17"), em("2020-01-11")),
          "PERP": (em("2020-01-11"), em("2021-06-01"))}'''),
        ('''        a, b = SPLITS["DISC"]
        msk = (self.T >= a) & (self.T < b)
        self.hot_thr = float(np.nanpercentile(ar[msk], 99))''',
         '''        self.hot_thr = float(HOT_THR)'''),
    ]),
    "sleeves.py": (R / "btc_scalp_20261021/strateji/sleeves.py", [
        ('R5 = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021")', f'R5 = Path("{ME}")'),
        ('RS = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021")', f'RS = Path("{ME}")'),
        ('d0, d1 = L.em("2021-06-01") // DAYM, L.em("2026-10-21") // DAYM', 'd0, d1 = L.em("2017-08-17") // DAYM, L.em("2021-06-01") // DAYM'),
        ('keep = (dec > L.T0M + 30 * DAYM) & (dec < L.em("2026-10-20 12:00"))', 'keep = (dec > L.T0M + 30 * DAYM) & (dec < L.em("2021-05-31 12:00"))'),
        ('sys.path.insert(0, str(RS / "fam_orderflow"))', 'sys.path.insert(0, str(Path(__file__).resolve().parent))'),
        ('z = np.load(RS / "fam_orderflow" / "results" / "events.npz")', 'z = np.load(RS / "cache" / "events.npz")'),
        ('z = np.load(RS / "fam_turev" / "cache" / "out_H60.npz")', 'z = np.load(RS / "cache" / "out_H60.npz")'),
        ('S = pickle.load(open(RS / "fam_turev" / "cache" / "signals.pkl", "rb"))', 'S = pickle.load(open(RS / "cache" / "signals.pkl", "rb"))'),
    ]),
    "lib.py": (R / "btc_scalp_20261021/feasibility/lib.py", [
        ('DATA = "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data"', f'DATA = "{D}"'),
        ('OUT = "/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out"', f'OUT = "{CA}"'),
        ('T0 = pd.Timestamp("2021-06-01", tz="UTC")', 'T0 = pd.Timestamp("2017-08-17", tz="UTC")'),
        ('T_END = pd.Timestamp("2026-10-21", tz="UTC")', 'T_END = pd.Timestamp("2021-06-01", tz="UTC")'),
    ]),
    "ofl.py": (R / "btc_scalp_20261021/fam_orderflow/ofl.py", [
        ('sys.path.insert(0, os.path.join(HERE, "..", "feasibility"))', 'sys.path.insert(0, HERE)'),
        ('DATA = os.path.join(HERE, "..", "data")', f'DATA = "{D}"'),
        ('RES = os.path.join(HERE, "results")', f'RES = "{CA}"'),
        ('''SEG = {
    "DISC": (lib.tmin("2021-06-01"), lib.tmin("2024-01-01")),
    "OOS": (lib.tmin("2024-01-11"), lib.tmin("2025-07-01")),
    "BLIND": (lib.tmin("2025-07-01"), lib.tmin("2026-10-21")),
}''', '''SEG = {
    "A": (lib.tmin("2017-08-17"), lib.tmin("2020-01-11")),
    "PERP": (lib.tmin("2020-01-11"), lib.tmin("2021-06-01")),
}'''),
        ('days = pd.date_range("2021-05-31", "2026-10-22", freq="D")', 'days = pd.date_range("2017-08-15", "2021-06-02", freq="D")'),
    ]),
    "of_build.py": (R / "btc_scalp_20261021/fam_orderflow/01_build.py", [
        ('cut = ofl.lib.tmin("2023-06-15 12:00")', 'cut = ofl.lib.tmin("2020-09-15 12:00")'),
    ]),
    "common.py": (R / "btc_scalp_20261021/fam_turev/scripts/common.py", [
        ('ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021")', f'ROOT = Path("{ME}")'),
        ('FAM = ROOT / "fam_turev"\nCACHE = FAM / "cache"\nOUT = FAM / "out"', 'FAM = ROOT\nCACHE = ROOT / "cache"\nOUT = ROOT / "cache"'),
        ('T0 = pd.Timestamp("2021-06-01", tz="UTC")', 'T0 = pd.Timestamp("2017-08-17", tz="UTC")'),
        ('T_END = pd.Timestamp("2026-10-21", tz="UTC")', 'T_END = pd.Timestamp("2021-06-01", tz="UTC")'),
        ('''SEG = {
    "DISC": ("2021-06-01", "2024-01-01"),
    "OOS": ("2024-01-11", "2025-07-01"),
    "BLIND": ("2025-07-01", "2026-10-21"),
}''', '''SEG = {
    "DISC": ("2017-08-17", "2020-01-11"),
    "OOS": ("2020-01-11", "2021-06-01"),
    "BLIND": ("2021-06-01", "2021-06-01"),
}  # etiket adları korunur (kod 0/1/2 kullanır); anlamı: A / PERP / boş'''),
    ]),
    "selftest.py": (R / "btc_scalp_20261021/strateji/00_selftest.py", [
        ('sıcak dakika eşiği (DISC p99 |1m|)', 'sıcak dakika eşiği (dondurulmuş, orijinal DISC p99 |1m|)'),
    ]),
    "events.py": (R / "btc_scalp_20261021/strateji/01_events.py", [
        ('        for sp_ in ("DISC", "OOS", "BLIND"):', '        for sp_ in ("A", "PERP"):'),
        ('        m = m0 & df.split.isin(["OOS", "BLIND"]).to_numpy()', '        m = m0 & df.split.isin(["A", "PERP"]).to_numpy()'),
    ]),
    "portfolio.py": (R / "btc_scalp_20261021/strateji/03_portfolio.py", [
        ('WIN = {"DISC": ["DISC"], "POST": ["OOS", "BLIND"], "TAM": ["DISC", "OOS", "BLIND"]}',
         'WIN = {"IND": ["A", "PERP"], "PERP": ["PERP"], "A": ["A"]}'),
        ('d0 = max(L.em(f"{y}-01-01"), L.em("2021-06-01")) // DAYM', 'd0 = max(L.em(f"{y}-01-01"), L.em("2017-08-17")) // DAYM'),
        ('d1 = min(L.em(f"{y + 1}-01-01"), L.em("2026-10-20")) // DAYM', 'd1 = min(L.em(f"{y + 1}-01-01"), L.em("2021-05-31")) // DAYM'),
        ('        for win in ("DISC", "POST", "TAM"):', '        for win in ("IND", "PERP", "A"):'),
        ('a, b = L.SPLITS["OOS"][0] // DAYM, L.SPLITS["BLIND"][1] // DAYM', 'a, b = L.SPLITS["A"][0] // DAYM, L.SPLITS["PERP"][1] // DAYM'),
        ('    d = SETS[k][SETS[k].split.isin(["OOS", "BLIND"])]', '    d = SETS[k][SETS[k].split.isin(["A", "PERP"])]'),
        ('        for win in ("DISC", "POST"):', '        for win in ("IND",):'),
    ]),
}


def main() -> None:
    diff_all, man = [], []
    for name, (src, reps) in SRC.items():
        txt = src.read_text()
        new = txt
        for a, b in reps:
            c = new.count(a)
            assert c == 1, f"{name}: '{a[:60]}' {c} kez geçiyor"
            new = new.replace(a, b)
        (PORT / name).write_text(new)
        man.append(f"{hashlib.sha256(txt.encode()).hexdigest()}  {src}  ->  port/{name}  ({len(reps)} değişim)")
        diff_all += list(difflib.unified_diff(txt.splitlines(True), new.splitlines(True), str(src), f"port/{name}"))
    (PORT / "PORT_DIFF.txt").write_text("".join(diff_all))
    (PORT / "MANIFEST.txt").write_text("\n".join(man) + "\n")
    print("\n".join(man))
    print("diff satırı:", len(diff_all))


if __name__ == "__main__":
    main()
