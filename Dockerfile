FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -c "from vale import download_vale_if_missing; download_vale_if_missing()" && \
    python -m nltk.downloader punkt
CMD ["python", "main.py"] 