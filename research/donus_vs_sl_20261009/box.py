"""MT5 kutusuna salt-okuma iş gönderme (base64 kod veya repo betiği) + çıktıyı işaretler arasından ayıklama."""
from __future__ import annotations

import base64
import json
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.remote import _client, submit  # noqa: E402

BEGIN, END = "TICK_DATA_BEGIN", "TICK_DATA_END"


def run_command(command: str, label: str, timeout: int = 600, poll_s: int = 3, max_wait_s: int = 1500) -> str:
    c = _client()
    cid = submit(c, "mt5_box", "run_analysis", {"command": command, "timeout": timeout}, f"tick araştırması: {label}")
    t0 = time.time()
    while time.time() - t0 < max_wait_s:
        r = c.table("evolution_commands").select("status,output,return_code").eq("id", cid).limit(1).execute().data
        if r and r[0]["status"] in ("done", "failed", "timeout"):
            out = r[0].get("output") or ""
            if r[0]["status"] != "done":
                raise RuntimeError(f"{label}: {r[0]['status']} rc={r[0].get('return_code')}\n{out[-1500:]}")
            return out
        time.sleep(poll_s)
    raise TimeoutError(label)


def run_code(code: str, label: str, timeout: int = 600) -> str:
    enc = base64.b64encode(code.encode()).decode()
    return run_command('python -c "import base64;exec(base64.b64decode(\'' + enc + '\'))"', label, timeout)


def decode(out: str):
    if BEGIN not in out:
        raise RuntimeError(out[-1500:])
    blob = out.split(BEGIN, 1)[1].split(END, 1)[0].strip().replace("\n", "").replace("\r", "")
    return json.loads(zlib.decompress(base64.b64decode(blob)))
