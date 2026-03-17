#!/bin/bash
set -e

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -e ".[dev]" -q

if [ ! -f ".env" ]; then
    cp ../.env.example .env
    echo ".env created from .env.example — edit it if needed"
fi

uvicorn app.main:app --reload --port 8000
