#!/bin/bash

function get_env() {
    env_name=$1
    default=$2
    file_env_name="${env_name}_FILE"

    if [ -n "${!file_env_name}" ] && [ -f "${!file_env_name}" ]; then
        cat "${!file_env_name}"
    elif [ -n "${!env_name}" ]; then
        echo "${!env_name}"
    else
        echo "$default"
    fi
}

set -o pipefail

run_celery_logfile_and_console() {
    local logfile=$1
    shift
    mkdir -p "$(dirname "$logfile")"
    touch "$logfile"
    tail -n0 -F "$logfile" &
    local tail_pid=$!
    _celery_tail_stop() {
        kill "$tail_pid" 2>/dev/null || true
        wait "$tail_pid" 2>/dev/null || true
    }
    trap _celery_tail_stop EXIT INT TERM

    PYTHONUNBUFFERED=1 "$@" --logfile="$logfile"
    local code=$?

    trap - EXIT INT TERM
    _celery_tail_stop
    exit "$code"
}

run_with_tee() {
    local logfile=$1
    shift
    mkdir -p "$(dirname "$logfile")"
    if command -v stdbuf >/dev/null 2>&1; then
        stdbuf -oL -eL "$@" 2>&1 | tee -a "$logfile"
    else
        "$@" 2>&1 | tee -a "$logfile"
    fi
    exit "${PIPESTATUS[0]}"
}

cd /app

if [ "$1" = "celery" ]; then
    CONCURRENCY=$(get_env CELERY_CONCURRENCY 2)

    if [ "$2" = "beat" ]; then
        run_celery_logfile_and_console /app/logs/celery/beat.log \
            celery -A project_name beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
    elif [ "$2" = "flower" ]; then
        run_with_tee /app/logs/celery/flower.log \
            celery -A project_name flower -l INFO --port=8081
    elif [ "$2" = "worker" ]; then
        run_celery_logfile_and_console /app/logs/celery/worker.log \
            celery -A project_name worker --loglevel=INFO --pool=gevent -Q default \
            --concurrency=$CONCURRENCY --max-tasks-per-child=100 --max-memory-per-child=512000 \
            -n worker@%h
    else
        echo "Invalid celery command: $2. Use 'beat', 'flower', or 'worker'"
        exit 1
    fi
else
    python3 manage.py migrate

    if [ "$(get_env DJANGO_SUPERUSER_CREATE 'true')" = "true" ]; then
        DEFAULT_USERNAME="admin"
        DEFAULT_EMAIL="admin@example.com"
        DEFAULT_NICKNAME="Admin"
        DEFAULT_PASSWORD="password"
        USERNAME=$(get_env SUPERUSER_USERNAME $DEFAULT_USERNAME)
        EMAIL=$(get_env SUPERUSER_EMAIL $DEFAULT_EMAIL)
        NICKNAME=$(get_env SUPERUSER_NICKNAME $DEFAULT_NICKNAME)
        PASSWORD=$(get_env SUPERUSER_PASSWORD $DEFAULT_PASSWORD)

        python3 manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.count() == 0:
    user = User.objects.create_superuser('$USERNAME', '$EMAIL', '$PASSWORD')
    if hasattr(user, 'nickname'):
        user.nickname = '$NICKNAME'
        user.save()
    print(f"Created superuser: {user.username}")
else:
    print("Superuser already exists, skipping creation")
EOF
    fi

    mkdir -p /app/logs/django
    if command -v stdbuf >/dev/null 2>&1; then
        ( stdbuf -oL -eL daphne -b 127.0.0.1 -p 8080 project_name.asgi:application 2>&1 | tee -a /app/logs/django/daphne.log ) &
    else
        ( daphne -b 127.0.0.1 -p 8080 project_name.asgi:application 2>&1 | tee -a /app/logs/django/daphne.log ) &
    fi
    nginx -g "daemon off;"
fi
