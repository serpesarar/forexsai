#!/usr/bin/env bash
set -euo pipefail

cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

cd ../frontend
npm install
