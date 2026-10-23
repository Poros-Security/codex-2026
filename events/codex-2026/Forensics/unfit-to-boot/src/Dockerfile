FROM python:3.12-slim

ARG BASE_FLAG=CODEX26{unf1t_h4sh3d_n0d3s_ub1_00b_m4st3r}
ENV BASE_FLAG=${BASE_FLAG}
ENV PYTHONUNBUFFERED=1
ENV CTF_PORT=11032

WORKDIR /app
COPY server.py qna.json ./
COPY entrypoint.sh /entrypoint.sh
COPY apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN sed -i 's/\r$//' /entrypoint.sh /apply_dynamic_flag.sh \
    && chmod +x /entrypoint.sh /apply_dynamic_flag.sh

EXPOSE 11032
CMD ["/entrypoint.sh"]
