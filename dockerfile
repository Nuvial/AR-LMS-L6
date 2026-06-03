FROM python:3.12-slim
RUN useradd app \
    && apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt \ 
    && chown -R app:app /app \
    && chmod +x /app/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--no-control-socket" ,"--bind", "0.0.0.0:5000", "app:app"]