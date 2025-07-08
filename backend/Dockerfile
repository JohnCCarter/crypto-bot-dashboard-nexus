# Backend Dockerfile för FastAPI
FROM python:3.11-slim

WORKDIR /app

# Installera beroenden
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera all kod
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
