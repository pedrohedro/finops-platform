FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir \
    setuptools==83.0.0 \
    wheel==0.47.0 \
    && python -m pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
