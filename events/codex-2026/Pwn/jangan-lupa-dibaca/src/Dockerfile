FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
COPY notesvc.c /tmp/notesvc.c
RUN gcc -O0 -fno-stack-protector -no-pie -fcf-protection=none -s -o /tmp/notesvc /tmp/notesvc.c

FROM debian:bookworm-slim
ARG BASE_FLAG=CODEX26{th3_t0d0_w4s_th3_b4ckd00r_4ll_al0ng}
ENV BASE_FLAG=${BASE_FLAG}
RUN apt-get update && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -u 1000 -M ctfuser
WORKDIR /home/ctfuser
COPY --from=build /tmp/notesvc ./notesvc
COPY entrypoint.sh /entrypoint.sh
COPY apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN sed -i 's/\r$//' /entrypoint.sh /apply_dynamic_flag.sh \
    && chmod +x notesvc /entrypoint.sh /apply_dynamic_flag.sh
EXPOSE 11030
CMD ["/entrypoint.sh"]
