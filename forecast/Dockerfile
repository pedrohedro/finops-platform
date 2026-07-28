FROM python:3.11-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir \
    setuptools==83.0.0 \
    wheel==0.47.0 \
    && /opt/venv/bin/python -m pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

ENV PATH="/opt/venv/bin:$PATH"
RUN groupadd --gid 10001 finops \
    && useradd --uid 10001 --gid 10001 --create-home finops

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY . .

USER 10001:10001
CMD ["python", "forecast.py"]
