# 1. Берем легкий образ Python
FROM python:3.11-slim

# 2. Отключаем создание кеш-файлов .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Создаем рабочую папку внутри контейнера
WORKDIR /code

# 4. Копируем файл зависимостей и устанавливаем их
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем весь код проекта внутрь контейнера
COPY . /code/

# 6. Говорим, какой порт будет открыт
EXPOSE 8000

# 7. Команда для запуска сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
