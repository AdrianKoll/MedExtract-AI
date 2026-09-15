FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        tesseract-ocr \
        tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY extractor ./extractor
COPY medextract ./medextract
RUN pip install --no-cache-dir .

COPY . .
COPY docker/entrypoint.sh /usr/local/bin/medextract-entrypoint
RUN chmod +x /usr/local/bin/medextract-entrypoint \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
ENTRYPOINT ["medextract-entrypoint"]
CMD ["gunicorn", "medextract.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
