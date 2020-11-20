FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-alpine3.10

RUN apk add tzdata gcc g++ make libffi-dev postgresql-dev
RUN cp /usr/share/zoneinfo/Europe/Warsaw /etc/localtime
RUN echo "Europe/Warsaw" >  /etc/timezone
RUN pip install pipenv

WORKDIR /app

ENV PYTHONPATH "/app"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV MODULE_NAME "main"
ENV PORT 8888

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
