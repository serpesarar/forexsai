#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY gk.py kesif && $PY gk.py dogrula && $PY gk.py tasima
