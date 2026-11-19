"""Kutuda çalışır — KULLANICI ONAYIYLA (2026-11-19): Pepperstone MT5 terminalini kısa süre kapatıp kilitli
history/NAS100/<YIL>.hcc dosyasını kopyalar, terminali yeniden açar, kopyayı 'research-xfer'e `tfy_hcc_NAS100_<YIL>.hcc`
olarak yükler.

Yalnız yolu PEPPERSTONE_EXE olan terminale dokunur (DBG izleyicinin ikinci MT5'i etkilenmez). Önce düzgün kapatma
(taskkill /PID, /F değil → terminal geçmişi diske yazar), 60 sn içinde kapanmazsa vazgeçer, zorla öldürmez.
Emir açmaz/kapatmaz; açık pozisyonlar broker sunucusunda kalır.
  python calistir/arac_hcc_kapat_kopyala.py 2026
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "remote_agent")
import agent_config as cfg  # noqa: E402

PEPPERSTONE_EXE = r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"
DATA = Path(os.environ["APPDATA"]) / "MetaQuotes/Terminal/73B7A2420D6397DFF9014A20F1201F97"
HIST = DATA / "bases/Pepperstone-Demo/history/NAS100"
BUCKET = "research-xfer"
CLOSE_WAIT_S = 60


def pids() -> list[int]:
    out = subprocess.run(["wmic", "process", "where", "name='terminal64.exe'", "get", "ProcessId,ExecutablePath", "/format:csv"],
                         capture_output=True, text=True).stdout
    res = []
    for line in out.splitlines():
        parts = line.strip().split(",")
        if len(parts) >= 3 and parts[1].lower() == PEPPERSTONE_EXE.lower():
            res.append(int(parts[2]))
    return res


def main() -> None:
    year = sys.argv[1] if len(sys.argv) > 1 else "2026"
    src = HIST / f"{year}.hcc"
    if not src.exists():
        raise SystemExit(f"yok: {src}")
    dst = Path(tempfile.gettempdir()) / f"tfy_{year}.hcc"
    ps = pids()
    print("pepperstone terminal pid:", ps, flush=True)
    t0 = time.time()
    for p in ps:
        subprocess.run(["taskkill", "/PID", str(p)], capture_output=True)
    while pids() and time.time() - t0 < CLOSE_WAIT_S:
        time.sleep(1)
    if pids():
        raise SystemExit("terminal 60 sn içinde kapanmadı; zorlanmadı, dosya kopyalanmadı")
    try:
        shutil.copy2(src, dst)
        print("kopyalandı", dst, dst.stat().st_size, f"{time.time() - t0:.1f} sn", flush=True)
    finally:
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([PEPPERSTONE_EXE], creationflags=flags, close_fds=True)
        time.sleep(15)
        print("yeniden açıldı:", pids(), f"toplam kapalı ≈{time.time() - t0:.0f} sn", flush=True)
    import requests
    url, key = cfg.SUPABASE_URL.rstrip("/"), cfg.SUPABASE_SERVICE_KEY
    h = {"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true", "Content-Type": "application/octet-stream"}
    r = requests.post(f"{url}/storage/v1/object/{BUCKET}/tfy_hcc_NAS100_{year}.hcc", headers=h, data=dst.read_bytes(), timeout=600)
    print("yüklendi", r.status_code, flush=True)


if __name__ == "__main__":
    main()
