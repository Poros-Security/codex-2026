FROM python:3.12.6-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
COPY readflag.c /tmp/readflag.c
RUN gcc -O2 -s -o /tmp/readflag /tmp/readflag.c

FROM python:3.12.6-slim
ARG BASE_FLAG=CODEX26{FLAG_INJECTED_AT_RUNTIME}
ENV BASE_FLAG=${BASE_FLAG}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 jail

COPY --from=build /tmp/readflag /usr/local/bin/readflag
RUN chown root:root /usr/local/bin/readflag && chmod 4755 /usr/local/bin/readflag

RUN echo "${BASE_FLAG}" > /flag \
    && chown root:root /flag && chmod 400 /flag

WORKDIR /app
COPY server.py /app/server.py
COPY entrypoint.sh /entrypoint.sh
COPY apply_dynamic_flag.sh /apply_dynamic_flag.sh
RUN sed -i 's/\r$//' /entrypoint.sh /apply_dynamic_flag.sh \
    && chmod +x /entrypoint.sh /apply_dynamic_flag.sh

EXPOSE 11031
CMD ["/entrypoint.sh"]
