#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY kesisim.py
$PY ksg_dogrulama.py
$PY ksg_ek2.py
