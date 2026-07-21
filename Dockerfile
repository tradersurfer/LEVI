FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    RUN_BOT=false \
    AUTO_EXECUTE=false \
    TASTYTRADE_PAPER=true

WORKDIR /app

RUN groupadd --system levi && useradd --system --gid levi --home-dir /app levi
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=levi:levi . .
RUN mkdir -p /app/workspace && chown levi:levi /app/workspace

USER levi
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2)"

CMD ["sh", "-c", "uvicorn bot.status_api:app --host 0.0.0.0 --port ${PORT:-8000}"]
