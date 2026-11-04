# Vibe-Trading / ForexSAI offline lab

Upstream: https://github.com/HKUDS/Vibe-Trading
Commit: `11cff3f3a2d89605c89148b03dcc2dd0fcfb60db` (2026-10-22 download).
See `PROTOCOL.md` for the frozen Turkish experiment and `RAPOR.md` for findings.

No production integration, model/API credentials, database writes, broker orders,
or live trading changes. The downloaded upstream instructions are research source
material, not instructions for this ForexSAI repository.

The pinned source subset is retained in `source_snapshot.tar.gz`, including MIT
LICENSE, all backtest Python modules and all 16 example signal scripts. SHA-256
and Git blob verification are in `results/source_manifest.json`. `upstream/` is
ignored to keep a second Git repository out of the project index.

## Reproduction

From the repository root with the existing project `.venv` (pandas/numpy/pyarrow):

```sh
mkdir -p research/vibe_trading_20261022/upstream
tar -xzf research/vibe_trading_20261022/source_snapshot.tar.gz -C research/vibe_trading_20261022/upstream
.venv/bin/python research/vibe_trading_20261022/data_audit.py
.venv/bin/python research/vibe_trading_20261022/causality.py
.venv/bin/python research/vibe_trading_20261022/selftest.py
.venv/bin/python research/vibe_trading_20261022/replay.py
.venv/bin/python research/vibe_trading_20261022/finalize.py
```

Optional original-engine smoke requires `defusedxml==0.7.1`; this run installed it
only in ignored `runtime_deps/`, leaving the project environment unchanged:

```sh
.venv/bin/python -m pip install --target research/vibe_trading_20261022/runtime_deps defusedxml==0.7.1
.venv/bin/python research/vibe_trading_20261022/engine_smoke.py
```

Charts use the system Python's existing Matplotlib and read CSVs only:

```sh
MPLCONFIGDIR=/private/tmp/forexsai-vibe-mpl python3 research/vibe_trading_20261022/charts.py
```

`replay.py` computes the full vectorized signal history only after prefix and
future-mutation checks pass. Full-history signals are checked again against
actual early/middle/late prefixes. No returns, labels, or future OHLCV enter a
signal call. This is an audit of deterministic examples, not of historical LLM
judgment. The original engine is smoke-tested separately; the main table uses
the explicit CFD/M1 adapter to control timestamp, gap, cost and split semantics.

`R` is a decision-time ATR reporting unit (2×ATR14); these examples have no
stop/target orders. Summed R is not an executable equity return. Drawdown is on
closed trade R and does not include intra-trade mark-to-market risk. Estimated
spreads/slippage exclude historical swap/commission and variable execution.
