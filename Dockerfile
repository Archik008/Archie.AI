# Используем официальный Python образ
FROM python:3.13.3-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем исходники
COPY . .

# Указываем команду по умолчанию (переопределим в docker-compose)
CMD ["python", "main.py"]