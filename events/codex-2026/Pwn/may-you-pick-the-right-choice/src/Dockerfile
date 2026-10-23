FROM debian:bookworm-slim
ARG BASE_FLAG=CODEX26{4t_th3_3nD_0f_th3_D4Y_no_0ne_shall_3sc4p3_th3_pr3determ1n3d_f4te}
ENV BASE_FLAG=${BASE_FLAG}

RUN apt-get update && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 ctf
WORKDIR /app
COPY ./chall /app/chall
COPY ./entrypoint.sh /entrypoint.sh
COPY ./run_chall.sh /app/run_chall.sh
COPY ./apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN chmod 755 /app/chall /entrypoint.sh /app/run_chall.sh /apply_dynamic_flag.sh \
    && sed -i 's/\r$//' /entrypoint.sh /app/run_chall.sh /apply_dynamic_flag.sh \
    && echo "${BASE_FLAG}" > /flag && chmod 444 /flag && chown root:root /flag
EXPOSE 1337
# Root starts entrypoint (writes /flag), socat executes binary as ctf
CMD ["/entrypoint.sh"]
