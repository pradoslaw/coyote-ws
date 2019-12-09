FROM python:2.7

RUN apt-get clean && apt-get update -yqq && apt-get install -y libpq-dev locales
RUN locale-gen en_US.UTF-8 && update-locale

WORKDIR /var/www

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
