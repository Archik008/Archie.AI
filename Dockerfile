FROM python:3.13.3-alpine

WORKDIR /app

COPY requirements.txt .

# Апгрейдим pip перед установкой
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]