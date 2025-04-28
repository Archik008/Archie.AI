# Используем официальный Python образ
FROM python:3.13.3-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем
RUN pip install fastapi[all] pytest pytest-asyncio sqlalchemy openai aiogram sentence-transformers asyncpg

# Копируем исходники
COPY . .

# Указываем команду по умолчанию (переопределим в docker-compose)
CMD ["python", "main.py"]