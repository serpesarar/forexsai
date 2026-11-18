#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY kb.py bolum1 && $PY kb.py bolum2 && $PY kb.py bolum3
