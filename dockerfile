FROM python:3.12-slim
WORKDIR /app
COPY bot/ ./bot
RUN pip install discord.py requests
CMD ["python", "bot/main.py"]
