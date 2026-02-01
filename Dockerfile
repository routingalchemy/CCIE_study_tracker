FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apk add --no-cache --virtual gcc libffi-dev openssl-dev

COPY . .

RUN pip install --no-cache-dir -r requirements.txt 

RUN mkdir -p uploads data

EXPOSE 5000

CMD ["gunicorn", "-c", "/app/gunicorn_config.py", "app:app"]
