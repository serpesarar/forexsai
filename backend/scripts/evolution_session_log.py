#!/usr/bin/env python3
"""1. Kural yardımcısı — Claude Code oturum kaydını Evrim Paneli'ne yazar.

Backend ÇALIŞMIYORKEN de çalışır (doğrudan dosyaya yazar). Kullanım:

    # Oturum özeti kaydet
    python3 backend/scripts/evolution_session_log.py \
        "signal_gates'e USOIL seans bloğu eklendi" \
        --files backend/services/signal_gates.py,backend/config.py

    # Aynı anda backlog'a unutulmasın-işi ekle
    python3 backend/scripts/evolution_session_log.py \
        "XAU EMEL deneyi yarım kaldı" \
        --backlog "XAU EMEL deneyini bitir|1m replay ile ölçülecek|experiment|high"

Özet Türkçe ve tek cümle-iki cümle olmalı; panel Değişiklik Akışı'nda görünür.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from services import evolution_service as evo  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Evrim Paneli oturum kaydı (1. Kural)")
    parser.add_argument("summary", help="Oturumda ne değişti (kısa Türkçe özet)")
    parser.add_argument("--files", default="", help="Virgülle ayrılmış dosya listesi")
    parser.add_argument(
        "--backlog", action="append", default=[],
        help="Backlog kaydı: 'başlık|detay|kategori|öncelik' (tekrarlanabilir)")
    args = parser.parse_args()

    backlog_ids = []
    for raw in args.backlog:
        parts = (raw.split("|") + ["", "idea", "medium"])[:4]
        item = evo.add_backlog_item(
            title=parts[0], detail=parts[1],
            category=parts[2] or "idea", priority=parts[3] or "medium",
            source="session",
        )
        backlog_ids.append(item["id"])
        print(f"backlog += {item['id']}: {item['title']}")

    files = [f.strip() for f in args.files.split(",") if f.strip()]
    note = evo.add_session_note(args.summary, files=files, backlog_added=backlog_ids)
    print(f"session note kaydedildi: {note['id']} ({note['ts']})")


if __name__ == "__main__":
    main()
