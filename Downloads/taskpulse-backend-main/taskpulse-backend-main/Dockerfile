FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY datasets ./datasets
COPY scripts ./scripts

# Train step is optional at build; copy a pre-built model or run scripts/train_fraud_model.py in CI
RUN if [ -f backend/models/xgboost_model.pkl ]; then echo "model present"; else python scripts/train_fraud_model.py; fi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl --fail http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
