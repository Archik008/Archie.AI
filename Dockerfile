FROM python:3.13.3-slim

WORKDIR /app

# Установка системных библиотек
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    libssl-dev \
    clang \
    llvm-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]