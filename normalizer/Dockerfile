FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir \
    setuptools==83.0.0 \
    wheel==0.47.0 \
    && python -m pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "normalizer.py"]
