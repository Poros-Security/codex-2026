FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN useradd -u 1000 -r -s /usr/sbin/nologin ctf
USER ctf
EXPOSE 9000
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "1", "--access-logfile", "-", "app:app"]