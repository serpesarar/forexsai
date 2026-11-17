"""Kutuda çalışır — SALT OKUMA: MT5 terminalinin veri klasöründeki NAS100 geçmiş dosyalarını listeler.

Terminal ayarına, sembole, emre dokunmaz. Amaç: 'grafikteki azami bar' (100.000) sınırının ötesinde diskte ne kadar
M1 geçmişi (history/NAS100/*.hcc, yıl başına bir dosya) durduğunu görmek. `--yukle` verilirse dosyaları ham hâliyle
özel 'research-xfer' deposuna `tfy_hcc_<ad>` olarak yükler (panelde ayrıştırılır).
Çalıştırma: python3 scripts/remote.py sh "python calistir/arac_mt5_gecmis_liste.py [--yukle]"
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "remote_agent")
import agent_config as cfg  # noqa: E402
import MetaTrader5 as mt5  # noqa: E402

SYMBOL = "NAS100"
BUCKET = "research-xfer"


def main() -> None:
    if not mt5.initialize(getattr(cfg, "MT5_TERMINAL_PATH", None)):
        raise SystemExit(f"MT5 başlatılamadı: {mt5.last_error()}")
    ti, acc = mt5.terminal_info(), mt5.account_info()
    print("veri klasörü:", ti.data_path, "| sunucu:", acc.server, "| maxbars:", ti.maxbars)
    mt5.shutdown()
    roots = [Path(ti.data_path) / "bases", Path(ti.commondata_path) / "bases"] if hasattr(ti, "commondata_path") else [Path(ti.data_path) / "bases"]
    files = []
    for root in roots:
        if root.exists():
            files += [p for p in root.rglob("*") if p.is_file() and SYMBOL.lower() in str(p).lower()]
    for p in sorted(files):
        print(f"{p.stat().st_size:>12}  {p}")
    if "--yukle" in sys.argv:
        import requests
        url, key = cfg.SUPABASE_URL.rstrip("/"), cfg.SUPABASE_SERVICE_KEY
        h = {"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true", "Content-Type": "application/octet-stream"}
        for p in files:
            if p.suffix.lower() in (".hcc", ".hc"):
                name = f"tfy_hcc_{p.parent.name}_{p.name}"
                r = requests.post(f"{url}/storage/v1/object/{BUCKET}/{name}", headers=h, data=p.read_bytes(), timeout=600)
                print("yüklendi", name, r.status_code)


if __name__ == "__main__":
    main()
