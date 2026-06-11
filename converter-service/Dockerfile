# Stage 1 - builder
FROM python:3.10-slim-bullseye AS builder

WORKDIR /app

RUN apt-get update --fix-missing \
    && apt-get install -y --no-install-recommends --fix-missing \
       gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2 - final
FROM python:3.10-slim-bullseye

WORKDIR /app

RUN apt-get update --fix-missing \
    && apt-get install -y --no-install-recommends --fix-missing \
       ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

CMD ["python3", "consumer.py"]
