FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/api/pyproject.toml /app/pyproject.toml
COPY services/api/app /app/app
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .[dev]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
