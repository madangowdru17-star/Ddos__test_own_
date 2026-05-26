FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements_v2.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY attacks_v2.py .
COPY bot_v2.py .

CMD ["python", "bot_v2.py"]