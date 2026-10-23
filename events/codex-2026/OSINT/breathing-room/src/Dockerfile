FROM python:3.12-slim

ARG BASE_FLAG=CODEX26{SEOUL_PM25_GRADE5_2019-02-15}
ENV BASE_FLAG=${BASE_FLAG}

WORKDIR /app
COPY server.py .
COPY entrypoint.sh /entrypoint.sh
COPY apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN sed -i 's/\r$//' /entrypoint.sh /apply_dynamic_flag.sh \
    && chmod +x /entrypoint.sh /apply_dynamic_flag.sh

EXPOSE 11033
CMD ["/entrypoint.sh"]
