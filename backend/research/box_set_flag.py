"""box_set_flag.py — kutudaki `yeni deneme/config.py`'ye faz bayrağı yazar.

config.py gitignore'da olduğu için bayraklar push'la değiştirilemez. Bu script
dosyanın SONUNDAKİ yönetilen blok içine yazar; blok dışına dokunmaz, şifre/anahtar
satırlarını görmez bile (yalnız blok metnini üretir).

Güvenlik: sadece `phase_rules.DEFAULTS` içinde TANIMLI bayrak adları kabul edilir;
değer `ast.literal_eval` ile doğrulanır. Bilinmeyen ad / bozuk değer → hata.

Kullanım (kutuda):
    python backend/research/box_set_flag.py --set TP_MODE=fixed
    python backend/research/box_set_flag.py --set NDX_FRIDAY_BLOCK=True --set NDX_SESSION_BLOCK_ENABLED=True
    python backend/research/box_set_flag.py --unset TP_MODE          # varsayılana dön
    python backend/research/box_set_flag.py --show
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "yeni deneme" / "config.py"
BEGIN = "# ─── FAZ BAYRAKLARI (scripts/bot_flags.py yönetir — elle düzenleme) ───"
END = "# ─── FAZ BAYRAKLARI SONU ───"

sys.path.insert(0, str(ROOT / "yeni deneme"))
import phase_rules as pr  # noqa: E402


def read_block(text: str) -> dict:
    m = re.search(re.escape(BEGIN) + r"(.*?)" + re.escape(END), text, re.S)
    if not m:
        return {}
    out: dict[str, object] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, val = line.partition("=")
        name, val = name.strip(), val.split("#")[0].strip()
        if not name or not val:
            continue
        try:
            out[name] = ast.literal_eval(val)
        except Exception:
            pass
    return out


def render(flags: dict) -> str:
    lines = [BEGIN,
             f"# son güncelleme: {datetime.now(timezone.utc).isoformat(timespec='seconds')}"]
    for k in sorted(flags):
        lines.append(f"{k} = {flags[k]!r}")
    lines.append(END)
    return "\n".join(lines)


def write_block(text: str, flags: dict) -> str:
    block = render(flags)
    if BEGIN in text and END in text:
        return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block,
                      text, flags=re.S)
    return text.rstrip() + "\n\n" + block + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", default=[], metavar="AD=DEĞER")
    ap.add_argument("--unset", action="append", default=[], metavar="AD")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    if not CONFIG.exists():
        sys.exit(f"config bulunamadı: {CONFIG}")
    text = CONFIG.read_text(encoding="utf-8")
    flags = read_block(text)

    if a.show and not (a.set or a.unset):
        print("yönetilen bayraklar:", flags or "(yok)")
        print("\netkin değerler:")
        import importlib
        sys.path.insert(0, str(ROOT / "yeni deneme"))
        cfg = importlib.import_module("config")
        for k in sorted(pr.DEFAULTS):
            src = "config" if hasattr(cfg, k) else "varsayılan"
            print(f"  {k:<32} = {pr.flag(cfg, k)!r:<28} ({src})")
        return

    for item in a.set:
        name, _, raw = item.partition("=")
        name, raw = name.strip(), raw.strip()
        if name not in pr.DEFAULTS:
            sys.exit(f"bilinmeyen bayrak: {name} (izinli: phase_rules.DEFAULTS)")
        try:
            flags[name] = ast.literal_eval(raw)
        except Exception:
            flags[name] = raw                       # düz string ("atr", "fixed")
    for name in a.unset:
        flags.pop(name.strip(), None)

    new = write_block(text, flags)
    # Sağlama: yazmadan önce sözdizimi kontrolü (bozuk config = bot ölür)
    try:
        compile(new, str(CONFIG), "exec")
    except SyntaxError as e:
        sys.exit(f"YAZILMADI — sözdizimi hatası: {e}")
    CONFIG.write_text(new, encoding="utf-8")
    print("yazıldı:", {k: flags[k] for k in sorted(flags)})
    print("→ etkili olması için: python3 scripts/remote.py restart bot")


if __name__ == "__main__":
    main()
