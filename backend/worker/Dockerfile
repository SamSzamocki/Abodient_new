FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# dummy command until we add Celery
CMD ["python", "-c", "print('worker placeholder, exits')"]
