# Run API from repo root only (parent of /backend). Do not run from inside /backend.
Set-Location $PSScriptRoot
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
