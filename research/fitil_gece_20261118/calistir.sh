#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY gece_run.py kesif
$PY gece_run.py dogrula
$PY gece_run.py dax
$PY kart.py
