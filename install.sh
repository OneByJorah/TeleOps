#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Installing TeleOps ==="

if ! command -v docker &> /dev/null; then
    echo "Docker is required but not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose is required but not installed."
    exit 1
fi

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env from .env.example. Please review and set real values before production use."
    else
        echo "No .env.example found; creating empty .env"
        touch .env
    fi
fi

echo "Building and starting TeleOps on port 5000..."
if docker compose version &> /dev/null; then
    docker compose up --build -d
else
    docker-compose up --build -d
fi

echo "TeleOps installed. Access: http://localhost:5000"
