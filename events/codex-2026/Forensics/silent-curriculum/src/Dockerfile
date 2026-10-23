FROM python:3.12-slim

ARG BASE_FLAG=CODEX26{s1l3nt_c0urs3_adm1n_t4k30v3r}
ENV BASE_FLAG=${BASE_FLAG}
ENV PYTHONUNBUFFERED=1
ENV CTF_PORT=11033

WORKDIR /app
COPY server.py qna.json ./
COPY entrypoint.sh /entrypoint.sh
COPY apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN sed -i 's/\r$//' /entrypoint.sh /apply_dynamic_flag.sh \
    && chmod +x /entrypoint.sh /apply_dynamic_flag.sh

EXPOSE 11033
CMD ["/entrypoint.sh"]
