#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
../../../.venv/bin/python cc.py kesif && ../../../.venv/bin/python cc.py dogrula
