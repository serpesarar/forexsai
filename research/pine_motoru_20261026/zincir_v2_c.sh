#!/bin/zsh
PY=/Users/melihcanodacioglu/Desktop/panel/.venv/bin/python
cd "$(dirname "$0")"
echo "=== full_15m_XAU madenci $(date)"
$PY -W ignore kombo_madenci_v2.py full_15m_XAU > data/kombo_v2_full_15m_XAU.log 2>&1; echo "XAU15 V2 EXIT $?"
SPECS="USOIL:15m DAX:5m NDX:5m XAU:5m USOIL:5m" ./zincir_v2.sh
