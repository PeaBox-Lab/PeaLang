FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 pealang && useradd --uid 10001 --gid 10001 --create-home pealang
WORKDIR /app
COPY pealang-0.90.0rc1-py3-none-any.whl /tmp/pealang.whl
RUN pip install --no-cache-dir /tmp/pealang.whl && rm /tmp/pealang.whl
USER 10001:10001
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/live', timeout=2)" || exit 1
LABEL org.opencontainers.image.title="PeaLang" org.opencontainers.image.version="0.90.0rc1"
CMD ["pea-serve", "serve", "/app/pipeline.json", "--host", "0.0.0.0", "--port", "8000"]
