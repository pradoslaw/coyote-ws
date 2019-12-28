FROM python:2.7-alpine

RUN apk add tzdata gcc g++ make libffi-dev openssl-dev
RUN cp /usr/share/zoneinfo/Europe/Warsaw /etc/localtime
RUN echo "Europe/Warsaw" >  /etc/timezone

WORKDIR /var/www

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
