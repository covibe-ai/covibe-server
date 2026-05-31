import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_env(env_name, default):
    """
    从环境变量获取配置值
    支持从文件读取（如果设置了 ENV_NAME_FILE 环境变量）
    """
    file_env_name = env_name + '_FILE'
    if file_env_name in os.environ and os.path.isfile(os.environ[file_env_name]):
        with open(os.environ[file_env_name], 'r') as file:
            return file.read().strip()
    if env_name in os.environ:
        return os.environ[env_name]
    return default


BASE_URL = get_env('BASE_URL', 'http://localhost:8000')

CELERY_BROKER_URL = get_env('CELERY_BROKER_URL', 'redis://localhost:6379/20')
CELERY_RESULT_BACKEND = 'django-db'  # 使用数据库存储任务结果

DATABASES = {}
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': get_env('CACHE_REDIS_URL', 'redis://localhost:6379/21'),
    }
}

DEBUG = True

if get_env('ALLOWED_HOSTS', '') != '':
    ALLOWED_HOSTS = get_env('ALLOWED_HOSTS', '').split(',')
if get_env('CORS_ALLOWED_ORIGINS', '') != '':
    CORS_ALLOWED_ORIGINS = get_env('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_ALL_ORIGINS = get_env('CORS_ALLOW_ALL_ORIGINS', 'true').lower() == 'true'
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CSRF_TRUSTED_ORIGINS = get_env('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:5173,http://localhost:5173').split(',')

# OSS 配置（可选）
OSS_ENABLED = False
OSS_BUCKET_NAME = get_env('OSS_BUCKET_NAME', None)
OSS_ENDPOINT = get_env('OSS_ENDPOINT', '')
OSS_ACCESS_KEY_ID = get_env('OSS_ACCESS_KEY_ID', '')
OSS_ACCESS_KEY_SECRET = get_env('OSS_ACCESS_KEY_SECRET', '')
OSS_CDN_DOMAIN = get_env('OSS_CDN_DOMAIN', '')

if OSS_BUCKET_NAME:
    OSS_ENABLED = True
    STORAGES = {
        "default": {
            "BACKEND": "covibe_server.storages.MyOssMediaStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = '/media/'
    MEDIA_ROOT = 'media'

FILE_UPLOAD_ROOT = get_env('FILE_UPLOAD_ROOT', '/uploads/')

SSO_TOKEN_LIFETIME = timedelta(days=int(get_env('SSO_TOKEN_LIFETIME_DAYS', '1')))

