FROM python:3.11-slim

WORKDIR /app

# System deps for nmap, snmp
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    snmp \
    snmp-mibs-downloader \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs config

CMD ["python3", "bot/main.py"]
