FROM python:3.11-slim AS base

COPY requirements.txt /
RUN apt-get update && apt-get --no-install-recommends install -y git
RUN pip install --no-cache-dir -r /requirements.txt
RUN apt-get clean

RUN mkdir /app
WORKDIR /app
ADD . /app

RUN python -c "from vale import download_vale_if_missing; download_vale_if_missing()"
RUN python -m nltk.downloader punkt

CMD python main.py