#!/bin/zsh
# EK-P9 v2'yi kalan sembol/TF'lerde sırayla koşturur: script koşusu → enjeksiyon → gerçek madenci.
PY=/Users/melihcanodacioglu/Desktop/panel/.venv/bin/python
cd "$(dirname "$0")"
for spec in ${=SPECS:-DAX:1h XAU:1h USOIL:1h NDX:15m}; do
  sym=${spec%%:*}; tf=${spec##*:}; w=full_${tf}_${sym}; lo=${sym:l}
  echo "=== $w başla $(date)"
  $PY -W ignore run_full.py $sym $tf 7 >> data/full_${tf}_${lo}.log 2>&1 || { echo "$w run_full HATA"; continue; }
  $PY -W ignore kombo_enjeksiyon_v2.py $w $sym 1,4,12 > data/enj_v2_${w}.log 2>&1; echo "$w ENJ EXIT $?"
  $PY -W ignore kombo_madenci_v2.py $w > data/kombo_v2_${w}.log 2>&1; echo "$w V2 EXIT $?"
  tail -20 data/kombo_v2_${w}.log
done
echo "=== zincir bitti $(date)"
