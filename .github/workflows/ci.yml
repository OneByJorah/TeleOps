name: NetBot CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install flake8 pytest pytest-asyncio
          pip install -r requirements.txt

      - name: Lint
        run: flake8 bot/ discovery/ dashboard/ --max-line-length=120 --ignore=E501,W503

      - name: Test
        run: pytest tests/ -v --tb=short
        if: always()

  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t netbot:test .
