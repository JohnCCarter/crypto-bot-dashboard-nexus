FROM python:3.10-slim

WORKDIR /app

# Installera beroenden
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera all kod
COPY . .

# Ange Flask-app och startkommando
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0"]
