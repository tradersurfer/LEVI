FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TASTYTRADE_PAPER=true
ENV AUTO_EXECUTE=false
ENV CONSENSUS_REQUIRED=true
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "bot.status_api:app", "--host", "0.0.0.0", "--port", "8000"]
