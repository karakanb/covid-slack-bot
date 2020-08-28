FROM python:3.8.5-alpine3.12
WORKDIR /code

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./ .