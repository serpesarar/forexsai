#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY korku.py kesif
$PY korku.py dogrula
$PY korku.py ayna
$PY kart.py
