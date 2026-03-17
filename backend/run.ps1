if (-not (Test-Path "venv")) {
    python -m venv venv
}

.\venv\Scripts\Activate.ps1

pip install -e ".[dev]" -q

if (-not (Test-Path ".env")) {
    Copy-Item ..\.env.example .env
    Write-Host ".env created from .env.example — edit it if needed"
}

uvicorn app.main:app --reload --port 8000
