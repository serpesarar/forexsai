#!/bin/zsh
# NASDAQ V/W dip kâr kapısı araması: test → tur 1 KEŞİF+doğrulama → tur 2 → tur 3 → tur 4 taşıma → kart
set -e
cd "$(dirname "$0")/src"
PY=../../../.venv/bin/python
$PY vw_oz_test.py
$PY kesif.py
$PY dogrulama.py "" 5
$PY kesif2.py
$PY dogrulama.py _tur2 6
$PY kesif3.py
$PY dogrulama.py _tur3 9
$PY tur4.py
$PY kart.py
$PY dax_dogrulama.py
