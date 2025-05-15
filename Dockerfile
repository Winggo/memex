FROM python:3.12.8 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN python -m venv .venv
# Pin pip to exact version to avoid errors like "Invalid version: '6.12.8-fly'"
RUN .venv/bin/pip install pip==24.0
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt


FROM python:3.12.8-slim
WORKDIR /app

COPY --from=builder /app/.venv .venv/
COPY . .
CMD ["/app/.venv/bin/uvicorn", "src.app:server", "--host", "0.0.0.0", "--port", "8000"]
