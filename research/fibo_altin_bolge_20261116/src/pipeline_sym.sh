#!/bin/zsh
# EK-3 sembol hattı: birincil → ızgara (TF başına paralel) → ızgara analizi → EK-3. Kullanım: src/pipeline_sym.sh DAX
set -e
S=$1; cd "$(dirname $0)"; PY=../../../.venv/bin/python; L=../logs
export FB_SYM=$S
$PY -c "import fblib; p=fblib.load_main(); print('yol', p.n)" > $L/${S}_load.log 2>&1
$PY run_primary.py > $L/${S}_primary.log 2>&1
for tf in 1m 5m 15m 30m 1h 4h; do $PY run_grid.py $tf > $L/${S}_grid_$tf.log 2>&1 & done; wait
$PY an_grid.py > $L/${S}_an_grid.log 2>&1
[ "$2" = "ek3" ] && $PY run_ek3.py > $L/${S}_ek3.log 2>&1
echo "HAT BİTTİ $S"
