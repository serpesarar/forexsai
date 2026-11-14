#!/bin/bash
# gerçek + 10 martingal piyasa (3 paralel)
cd "$(dirname "$0")/src"
PY=/Users/melihcanodacioglu/Desktop/panel/.venv/bin/python
$PY build_grid.py real > ../logs/build_real.log 2>&1
for s in 1 2 3 4 5 6 7 8 9 10; do
  $PY build_grid.py mart $s > ../logs/build_mart$s.log 2>&1 &
  if (( s % 3 == 0 )); then wait; fi
done
wait
echo ALLDONE
