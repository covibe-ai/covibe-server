CELERY_RESULT_BACKEND = 'django-db'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/10'
CELERY_BROKER_URL = 'redis://localhost:6379/10'

CELERY_CACHE_BACKEND = 'default'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_TRACK_STARTED = True

CELERY_ROUTES = {
    # 可以在这里配置不同任务的路由
    # 'app.tasks.*': {'queue': 'app_queue'},
    '*': {'queue': 'default'},
}

CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
DJANGO_CELERY_BEAT_TZ_AWARE = True

