# Run TaskPulse Backend & Frontend

## Prerequisites
- **MongoDB** running (e.g. `docker run -d -p 27017:27017 mongo:7` or local install)
- Optional: copy `.env.example` to `.env` and set `GEMINI_API_KEY`

## Backend (Terminal 1 — **repository root**)

Your prompt must be the folder that **contains** the `backend` directory (e.g. `...\taskpulse-backend-main`).  
If you `cd backend` and start the server, you will get **`No module named 'backend'`**.

1. `python -m venv venv` (first time only)
2. `venv\Scripts\activate` (Windows PowerShell)
3. `pip install -r requirements.txt`
4. `python scripts\train_fraud_model.py` (first time — creates `backend\models\xgboost_model.pkl`)
5. Start the API:

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

(equivalent: `python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000`)

Or run: `.\run_backend.ps1`

**Docs:** http://localhost:8000/docs · **Health:** http://localhost:8000/health

## Frontend (Terminal 2)

1. `cd frontend`
2. `npm install`
3. `npm run dev`

**App:** http://localhost:5173

## Stop servers
Ctrl+C in each terminal.

## Troubleshooting
- **`ModuleNotFoundError: No module named 'backend'`** — You started uvicorn from inside the `backend` folder. `cd ..` to the **repository root** (parent of `backend`), then run step 5 again.
- **`Could not import module "main"`** — Pull latest; root `main.py` re-exports the app. Or use `backend.app:app` from the repository root.
- **`uvicorn` is not recognized** — Use `python -m uvicorn ...` (with venv activated).
- **Port 8000 in use** — Add `--port 8001` and set `VITE_API_URL=http://localhost:8001` in `frontend/.env` if needed.
- **Mongo connection errors** — Start MongoDB; set `MONGODB_URI` in `.env` if not default `mongodb://localhost:27017`.
