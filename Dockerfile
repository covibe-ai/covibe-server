# syntax=docker/dockerfile:1
# 需要 DOCKER_BUILDKIT=1（Docker Desktop / 新版 CLI 默认开启）以使用 --mount=type=cache
FROM python:3.12-slim-bookworm

SHELL ["/bin/bash", "-c"]

WORKDIR /app
ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    TZ=Asia/Shanghai \
    LIBRARY_PATH=/lib:/usr/lib \
    PATH="${PATH}:/root/.local/bin" \
    DJANGO_SUPERUSER_CREATE=true \
    SUPERUSER_USERNAME= \
    SUPERUSER_EMAIL= \
    SUPERUSER_PASSWORD=

COPY deploy/sources.list /etc/apt/sources.list
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nginx \
    git \
    unzip \
    curl \
    python3-dev \
    libpq-dev \
    build-essential \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libxml2-dev \
    libxmlsec1-dev && \
    apt-get -o Dpkg::Options::="--force-confmiss" install --reinstall netbase && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    rm -rf ~/.cache/pip

RUN pip install --no-cache-dir uv

COPY deploy/nginx/nginx.conf /etc/nginx/nginx.conf

COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --frozen --no-emit-project -o /tmp/locked-requirements.txt && \
    uv pip install --system -r /tmp/locked-requirements.txt

COPY . /app/
RUN mv /app/project_name/settings/CONFIG.prod.py /app/project_name/settings/CONFIG.py && \
    chmod +x /app/deploy/entrypoint.sh

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e . --no-deps

RUN python3 manage.py collectstatic --no-input

RUN mkdir -p /app/logs/{celery,django,nginx} /app/media && \
    chown -R www-data:www-data /app/logs/nginx /app/media && \
    chown -R root:root /app/logs/{django,celery} && \
    chmod -R 755 /app/logs /app/media && \
    chmod g+s /app/logs/{nginx,django,celery}

EXPOSE 80

ENTRYPOINT ["/app/deploy/entrypoint.sh"]
