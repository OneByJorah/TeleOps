version: "3.9"

services:

  # ── Telegram Bot + Agent Server ───────────────────────────────────────────
  bot:
    build: .
    container_name: netbot
    restart: unless-stopped
    ports:
      - "8080:8080"   # Agent registration + download server
      - "5000:5000"   # Web dashboard
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ./agents:/app/agents:ro
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - netbot-net
    depends_on:
      - redis

  # ── Redis (state / job queue) ─────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: netbot-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - netbot-net

networks:
  netbot-net:
    driver: bridge

volumes:
  redis-data:
