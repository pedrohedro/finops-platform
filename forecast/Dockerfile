FROM python:3.11-slim

# Prophet needs C++ compiler for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir \
    setuptools==83.0.0 \
    wheel==0.47.0 \
    && python -m pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "forecast.py"]
