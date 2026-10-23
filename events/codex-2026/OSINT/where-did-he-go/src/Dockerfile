FROM python:3.12-slim

ARG BASE_FLAG=CODEX26{ISHOWSPEED}
ENV BASE_FLAG=${BASE_FLAG}

WORKDIR /app
COPY server.py .
COPY entrypoint.sh /entrypoint.sh
COPY apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN sed -i 's/\r$//' /entrypoint.sh /apply_dynamic_flag.sh \
    && chmod +x /entrypoint.sh /apply_dynamic_flag.sh

EXPOSE 11034
CMD ["/entrypoint.sh"]
