FROM python:3.12-slim
WORKDIR /app
COPY ./bot
RUN pip install discord.py requests

CMD ["python", "bot.py"]

