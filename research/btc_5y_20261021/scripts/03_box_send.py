"""Bir box_*.py betiğini kutuya DOSYA YAZMADAN gönderir:
python -c "import zlib,base64;exec(zlib.decompress(base64.b64decode('...')))"
remote.py sh üzerinden (cmd.exe, ~8k karakter sınırı). Ek argümanlar
betikte ARGS değişkeni olarak görünür.

Kullanım: python3 03_box_send.py <box_script.py> [ARGS-json] > çıktı.txt
"""
from __future__ import annotations

import base64
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    src = Path(sys.argv[1]).read_text()
    args = sys.argv[2] if len(sys.argv) > 2 else "{}"
    src = f"ARGS = {args}\n" + src
    b64 = base64.b64encode(zlib.compress(src.encode(), 9)).decode()
    cmd = f'python -c "import zlib,base64;exec(zlib.decompress(base64.b64decode(\'{b64}\')))"'
    if len(cmd) > 7800:
        sys.exit(f"komut çok uzun: {len(cmd)}")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "remote.py"), "sh", cmd,
                    "--timeout", "600"], check=False)


if __name__ == "__main__":
    main()
