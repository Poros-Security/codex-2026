FROM php:8.3-apache

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        redis-server supervisor nginx curl python3 python3-pip python3-venv gosu \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m ctf || true

WORKDIR /opt/gopher

# Flask relay
COPY app/requirements.txt /opt/gopher/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /opt/gopher/requirements.txt
COPY app/app.py /opt/gopher/app.py

# Apache/php webroot (shared with redis RDB drop)
COPY web/index.html /var/www/html/index.html
RUN chown -R www-data:www-data /var/www/html && chmod 777 /var/www/html

# Nginx front (single Whale port)
COPY allinone/nginx.conf /etc/nginx/sites-available/default
COPY allinone/supervisord.conf /etc/supervisor/conf.d/gopher.conf
COPY allinone/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && rm -f /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
