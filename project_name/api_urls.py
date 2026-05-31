from rest_framework_nested import routers
from django.urls import path, include

# 创建主路由器
router = routers.DefaultRouter()

# 在这里注册你的 ViewSet
# router.register(r'example', ExampleViewSet, basename='example')

# API URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

