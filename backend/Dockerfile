FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser
RUN mkdir -p /home/appuser/.cache/fontconfig && chown -R appuser:appgroup /home/appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install-deps chromium
RUN playwright install chromium

COPY src/ ./src/
COPY alembic.ini ./src/

RUN chown -R appuser:appgroup /app

WORKDIR /app/src

USER appuser

CMD ["python", "-m", "core.scraping.main"]