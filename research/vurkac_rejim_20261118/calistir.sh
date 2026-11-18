#!/bin/zsh
set -e
cd "$(dirname "$0")/src"
../../../.venv/bin/python vr.py kesif
