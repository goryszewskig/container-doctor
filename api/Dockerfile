FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask psycopg2-binary gunicorn

COPY app.py .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
