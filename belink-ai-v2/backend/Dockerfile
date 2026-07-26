FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8421 \
    HOME=/app \
    PATH="/app/.venv/bin:$PATH" \
    UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

RUN addgroup --system belink && adduser --system --uid 10001 --ingroup belink belink

COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && uv sync --no-dev

COPY . .
RUN mkdir -p /app/data /tmp/uv-cache \
    && chown -R belink:belink /app /tmp/uv-cache

USER belink
EXPOSE 8421

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD /app/.venv/bin/python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.getenv('PORT','8421'), timeout=3).read()" || exit 1

# Run the prebuilt virtual environment directly. Do not invoke uv at runtime:
# the non-root Render service user must never need a cache under /nonexistent.
CMD ["/app/.venv/bin/python", "main.py"]
