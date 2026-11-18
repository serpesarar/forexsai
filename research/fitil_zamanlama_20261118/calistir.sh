#!/bin/zsh
# Fitil sonrası giriş zamanlaması: test → AL (KEŞİF+doğrulama) → SAT → oynaklık tetiği
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY fz_oz_test.py
$PY fz_run.py kesif 0 al && $PY fz_run.py dogrula 5 al
$PY fz_run.py kesif 0 sat && $PY fz_run.py dogrula 6 sat
$PY fz_run.py kesif 0 atr && $PY fz_run.py dogrula 11 atr
