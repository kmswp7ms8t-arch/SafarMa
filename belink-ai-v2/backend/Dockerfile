FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8421

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && uv sync --no-dev
COPY . .
RUN mkdir -p /app/data
EXPOSE 8421
CMD ["sh", "-c", "uv run python main.py"]
