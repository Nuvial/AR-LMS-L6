FROM python:3.12-slim
RUN useradd app
WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt && chown -R app:app /app

EXPOSE 5000

USER app

CMD ["gunicorn", "--no-control-socket" ,"--bind", "0.0.0.0:5000", "app:app"]