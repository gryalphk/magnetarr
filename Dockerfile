FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY bot /app/bot

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot/main.py"]
