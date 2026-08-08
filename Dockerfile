# ── Stage 1: Build ──────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build
COPY requirements.txt .
# Remove problematic packages for build
RUN sed -i '/^python-nmap/d; /^nmap==/d; /^pywinrm/d; /^scapy/d' requirements.txt && \
    pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ───────────────────────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for nmap, snmp, network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    snmpd \
    iputils-ping \
    net-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python deps from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# App code
COPY bot/ bot/
COPY dashboard/ dashboard/
COPY config/ config/
COPY discovery/ discovery/
COPY agents/ agents/
COPY tests/ tests/
COPY docs/ docs/
COPY handlers.py .
COPY snmp_scanner.py .
COPY index.html .
COPY requirements.txt .

# Create data directories
RUN mkdir -p /app/logs /app/config

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:5000/ || exit 1

EXPOSE 5000 8080

# First-run setup entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python3", "bot/main.py"]
