#!/bin/zsh
# NASDAQ 2/3/90/210 dk mum üretimi + bağımsız doğrulama. Kökten: zsh research/ndx_tf_yapilandirma_20261117/calistir.sh
set -e
cd "$(dirname "$0")"
PY=../../.venv/bin/python
$PY src/s01_envanter.py > results/s01_stdout.txt
$PY src/s02_fitil_denetim.py > results/s02_stdout.txt
$PY src/s02_fitil_denetim.py --m30 >> results/s02_stdout.txt
$PY src/s05_ek_kaynak.py > results/s05_stdout.txt
$PY src/s07_tik_2025.py > results/s07_stdout.txt
$PY src/s08_ek_besleme.py > results/s08_stdout.txt
$PY src/s03_uret.py > results/s03_stdout.txt
$PY src/s04_dogrulama.py | tee results/s04_stdout.txt | tail -1
$PY src/s09_red_cozum.py > results/s09_stdout.txt
$PY src/s10_dis_envanter.py > results/s10_stdout.txt
$PY src/s06_dosya_hukumleri.py > results/s06_stdout.txt
