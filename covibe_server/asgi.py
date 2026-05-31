"""
ASGI config for covibe_server project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'covibe_server.settings')

# 启用异步支持
django_asgi_app = get_asgi_application()

# 如果需要 WebSocket 支持，可以在这里添加
# from channels.routing import ProtocolTypeRouter
# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": ...,
# })

application = django_asgi_app

