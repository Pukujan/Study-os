# Study OS web app image (D018): built frontend + FastAPI API in one same-origin service.
# Build context: repository root.  docker build -f deploy/Dockerfile .

FROM node:24-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npx vite build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    STATIC_DIR=/app/static COOKIE_SECURE=1
WORKDIR /app
COPY deploy/requirements-web.lock /tmp/requirements-web.lock
RUN pip install --no-deps -r /tmp/requirements-web.lock
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps . && rm -rf /app/src /app/build
COPY --from=web /web/dist /app/static
RUN useradd --system --uid 10001 --no-create-home study && chown -R study /app
USER study
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"
CMD ["uvicorn", "study_os.web.api:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-server-header"]
