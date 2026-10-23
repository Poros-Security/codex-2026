FROM ubuntu:24.04 AS build
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY challenge.c .
RUN gcc challenge.c -o vault.debug -O0 -fno-stack-protector -fPIE -pie -Wl,-z,relro,-z,now -Wl,-z,noexecstack \
    && cp vault.debug vault \
    && strip --strip-all vault

FROM ubuntu:24.04
ARG BASE_FLAG=CODEX26{blind_vault_1s_n0t_s0_s3cur3}
ENV BASE_FLAG=${BASE_FLAG}
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends socat coreutils \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --shell /usr/sbin/nologin ctf
COPY --from=build /build/vault /home/ctf/vault
COPY flag.txt /flag
COPY entrypoint.sh /entrypoint.sh
COPY apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN sed -i 's/\r$//' /entrypoint.sh /apply_dynamic_flag.sh \
    && chmod +x /entrypoint.sh /apply_dynamic_flag.sh \
    && chown root:ctf /home/ctf/vault && chmod 0555 /home/ctf/vault \
    && chown root:ctf /flag && chmod 0440 /flag
EXPOSE 5000
CMD ["/entrypoint.sh"]
