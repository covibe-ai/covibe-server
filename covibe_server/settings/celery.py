CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_URL = 'redis://localhost:6379/10'

CELERY_CACHE_BACKEND = 'default'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_TRACK_STARTED = True

CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_TASK_ROUTES = {}

CELERY_BEAT_SCHEDULE = {
    'order-auto-close-expired-orders': {
        'task': 'order.tasks.auto_close_expired_orders',
        'schedule': 60.0,
        'options': {'queue': CELERY_TASK_DEFAULT_QUEUE},
    },
}

CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
DJANGO_CELERY_BEAT_TZ_AWARE = True
