#!/bin/zsh
# NASDAQ 210m alt fitil → 4 işlem kuralı: test + örnek + ana koşu + grafikler (~20 sn)
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY oz_test.py
$PY ornek_17kasim.py
$PY kosu.py
$PY grafik.py
$PY bugun_17kasim.py
$PY canli_mum.py
