FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AMP_STATE_DIR=/app/state
WORKDIR /app
COPY requirements-framework.txt ./
RUN pip install --no-cache-dir -r requirements-framework.txt \
    && useradd --uid 10001 --create-home framework \
    && mkdir -p /app/state && chown framework:framework /app/state
COPY src/framework/ ./src/framework/
COPY src/serving/static/framework/ ./src/serving/static/framework/
COPY src/serving/static/landing.html ./src/serving/static/landing.html
USER framework
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "src.framework.app:app", "--host", "0.0.0.0", "--port", "8000"]
