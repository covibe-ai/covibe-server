from rest_framework_nested import routers
from django.urls import path, include

from order.views import OrderViewSet

router = routers.DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('payments/wechat/', include('wechat.urls')),
    path('', include(router.urls)),
]
