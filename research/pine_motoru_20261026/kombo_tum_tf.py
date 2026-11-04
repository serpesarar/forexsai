"""EK-P8 tekrarını tüm pencerelere yay: doğrulama-geçen kombinasyonların scriptlerini past/old/tf_1m/5m/4h/1d'de koştur,
sonra kombo_tekrar'ı (recent, tf_15m kaynakları) bu pencerelerle yeniden ölç."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replicate_pine as RP  # noqa: E402
import kombo_tekrar as KT  # noqa: E402

WINDOWS = ("past", "tf_1m", "tf_5m", "tf_4h", "tf_1d", "old")

if __name__ == "__main__":
    sids = set((HERE / "data/kombo_sids.txt").read_text().split())
    for w in WINDOWS:
        RP.run_window(w, sids)
    KT.main("recent", ["tf_15m", *WINDOWS])
    KT.main("tf_15m", ["recent", *WINDOWS])
