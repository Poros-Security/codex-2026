FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir cryptography==43.0.3

COPY warden.py params.json vault.key ./

ENV VAULT_KEY=""
EXPOSE 18431

CMD ["python", "-u", "warden.py"]
