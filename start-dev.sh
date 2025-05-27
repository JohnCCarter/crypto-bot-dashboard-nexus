#!/usr/bin/env bash
# 1) starta backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask run --host=0.0.0.0 &

# 2) starta frontend (dev)
cd ..
npm install
npm run dev
