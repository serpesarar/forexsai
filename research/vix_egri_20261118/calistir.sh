#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY ve.py kesif && $PY ve.py dogrula && $PY kart.py
