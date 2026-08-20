#!/usr/bin/env python3
"""bot_flags.py — kutudaki botun faz bayraklarını panelden tek komutla değiştir.

`yeni deneme/config.py` gitignore'da olduğu için bayraklar git ile taşınmaz;
bu script köprü üzerinden kutudaki `box_set_flag.py`'yi çalıştırır.

    python3 scripts/bot_flags.py show                 # etkin değerler
    python3 scripts/bot_flags.py phase1 on            # Faz-1 giriş filtreleri
    python3 scripts/bot_flags.py phase0 off           # Faz-0'ı eski davranışa al
    python3 scripts/bot_flags.py phase2 block         # sıkı konum kapısını BLOK yap
    python3 scripts/bot_flags.py set TP_ATR_MULT 3.0
    python3 scripts/bot_flags.py revert-all           # HER ŞEY eski davranışa
    python3 scripts/bot_flags.py ... --restart        # sonrasında botu yenile

Faz haritası (2026-08-14 karşı-olgusal denetimi):
  phase0 : TP=2.5×ATR70 + koşullu BE + zaman stopu     (varsayılan AÇIK)
  phase1 : ASIA/Cuma yasağı + S/R kolu kapalı + oy sıkılığı (varsayılan KAPALI)
  phase2 : sıkı dalga-konumu kapısı                     (varsayılan GÖLGE)
  phase3 : MOD-E probasyon — live | shadow | off        (varsayılan GÖLGE)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTE = ROOT / "scripts" / "remote.py"

PRESETS: dict[str, dict[str, dict[str, str]]] = {
    # phase0 = dış-örneklemde AYAKTA KALAN hâli (yalnız koşullu BE).
    "phase0": {
        "on": {"MGMT_BE_MODE": "'conditional_mfe'", "TP_MODE": "'fixed'",
               "MGMT_TIME_STOP_MIN": "0"},
        "off": {"MGMT_BE_MODE": "'time30'", "TP_MODE": "'fixed'",
                "MGMT_TIME_STOP_MIN": "0"},
    },
    # atrtp = dış-örneklemde ELENEN TP deneyi (WR ↑, para ↓). Yeniden denemek
    # istenirse tek komutla açılır; kanıt birikmeden canlıda tutma.
    "atrtp": {
        "on": {"TP_MODE": "'atr'", "TP_ATR_MULT": "2.5", "TP_ATR_MIN_R": "0.3"},
        "off": {"TP_MODE": "'fixed'"},
    },
    "timestop": {
        "on": {"MGMT_TIME_STOP_MIN": "240"},
        "off": {"MGMT_TIME_STOP_MIN": "0"},
    },
    "phase1": {
        "on": {"NDX_SESSION_BLOCK_ENABLED": "True", "NDX_FRIDAY_BLOCK": "True",
               "NDX_WEEKEND_HOLD_BLOCK": "True", "NDX_SR_ENTRY_ENABLED": "False",
               "PHASE1_CONFIG_RESTORE": "True"},
        "off": {"NDX_SESSION_BLOCK_ENABLED": "False", "NDX_FRIDAY_BLOCK": "False",
                "NDX_WEEKEND_HOLD_BLOCK": "False", "NDX_SR_ENTRY_ENABLED": "True",
                "PHASE1_CONFIG_RESTORE": "False"},
    },
    "phase2": {
        "shadow": {"POS_TIGHT_ENABLED": "True", "POS_TIGHT_BLOCK": "False"},
        "block": {"POS_TIGHT_ENABLED": "True", "POS_TIGHT_BLOCK": "True"},
        "off": {"POS_TIGHT_ENABLED": "False", "POS_TIGHT_BLOCK": "False"},
    },
    # phase3 = MOD-E probasyonu. 'live' → emir 5 bar geciktirilir (probation_exec).
    # re-entry: ana işlem kapanınca aynı yönde bir kez daha gir.
    # dış-örneklemde bağımsızlık ✅ + eşit-risk alfa ✅ ama plasebo ❌ (p=0.187)
    # → gölgeyle başla, 2-4 hafta veri sonrası live.
    "reentry": {
        "shadow": {"REENTRY_MODE": "'shadow'"},
        "live": {"REENTRY_MODE": "'live'"},
        "off": {"REENTRY_MODE": "'off'"},
    },
    "phase3": {
        "live": {"PROBATION_LIVE": "True", "PROBATION_SHADOW_ENABLED": "True"},
        "shadow": {"PROBATION_SHADOW_ENABLED": "True", "PROBATION_LIVE": "False"},
        "off": {"PROBATION_SHADOW_ENABLED": "False", "PROBATION_LIVE": "False"},
    },
}


def run_box(args: list[str], timeout: int = 300) -> int:
    cmd = " ".join(["python", "backend/research/box_set_flag.py"] + args)
    return subprocess.call([sys.executable, str(REMOTE), "sh", cmd,
                            "--timeout", str(timeout)])


def main() -> None:
    argv = [a for a in sys.argv[1:] if a != "--restart"]
    restart = "--restart" in sys.argv
    if not argv:
        print(__doc__)
        sys.exit(1)
    cmd = argv[0]

    if cmd == "show":
        rc = run_box(["--show"])
    elif cmd == "set" and len(argv) == 3:
        rc = run_box([f"--set={argv[1]}={argv[2]}"])
    elif cmd == "unset" and len(argv) == 2:
        rc = run_box([f"--unset={argv[1]}"])
    elif cmd == "revert-all":
        flags: dict[str, str] = {}
        for preset in PRESETS.values():
            flags.update(preset.get("off", {}))
        rc = run_box([f"--set={k}={v}" for k, v in flags.items()])
    elif cmd in PRESETS and len(argv) == 2 and argv[1] in PRESETS[cmd]:
        rc = run_box([f"--set={k}={v}" for k, v in PRESETS[cmd][argv[1]].items()])
    else:
        print(__doc__)
        sys.exit(1)

    if rc == 0 and restart:
        subprocess.call([sys.executable, str(REMOTE), "restart", "bot"])
    sys.exit(rc)


if __name__ == "__main__":
    main()
