# Stage 1: сборка зависимостей
FROM python:3.11-slim AS builder

WORKDIR /app

# Копируем только файлы с зависимостями для кэширования слоёв
COPY requirements.txt .

# Устанавливаем зависимости в отдельную директорию (--target)
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: финальный образ
FROM python:3.11-slim

WORKDIR /app

# Копируем установленные зависимости из builder
COPY --from=builder /root/.local /root/.local

# Копируем исходный код приложения
COPY ./app ./app
COPY ./config ./config
COPY ./migrations ./migrations
COPY main.py .

# Обновляем PATH для пользовательских пакетов
ENV PATH=/root/.local/bin:$PATH

# Открываем порт, который будет использоваться (Render передаёт PORT env)
EXPOSE 8000

# Запуск через uvicorn (порт можно переопределить через переменную окружения PORT)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]