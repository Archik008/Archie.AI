# Используем официальный Python образ на базе Alpine
FROM python:3.13.3-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем необходимые пакеты для сборки и системные библиотеки
RUN apk update && apk add \
    libssl3 \
    libssl-dev \
    clang \
    llvm-dev \
    musl-dev \
    gcc \
    g++ \
    make
# Копируем файл зависимостей и устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта
COPY . .

# Указываем команду по умолчанию
CMD ["python", "main.py"]