# Stage 1 - builder
FROM python:3.10-slim-bullseye AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2 - final
FROM python:3.10-slim-bullseye

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

CMD ["python3", "consumer.py"]
