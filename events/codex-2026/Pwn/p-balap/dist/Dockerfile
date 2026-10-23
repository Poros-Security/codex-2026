FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        qemu-system-x86 \
        socat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /challenge

COPY bzImage .
COPY rootfs.cpio.gz .
COPY run.sh .
COPY qemu.sh .

RUN chmod +x run.sh qemu.sh

EXPOSE 31337

CMD ["./run.sh"]
