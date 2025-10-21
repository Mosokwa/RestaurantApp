from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/orders/(?P<order_id>[^/]+)/tracking/$', consumers.OrderTrackingConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/restaurant/(?P<restaurant_id>\d+)/dashboard/$', consumers.RestaurantDashboardConsumer.as_asgi()),

    # POS consumers
    re_path(r'ws/pos/realtime/$', consumers.POSRealtimeConsumer.as_asgi()),
    re_path(r'ws/pos/restaurant/(?P<restaurant_id>\w+)/$', consumers.POSRealtimeConsumer.as_asgi()),
    re_path(r'ws/pos/order/(?P<order_uuid>[^/]+)/$', consumers.POSRealtimeConsumer.as_asgi()),
    re_path(r'ws/pos/kitchen/(?P<restaurant_id>\w+)/$', consumers.POSRealtimeConsumer.as_asgi()),

    # ========== NEW ROUTES - REAL-TIME MANAGEMENT ==========
    re_path(r'ws/kitchen/(?P<restaurant_id>\d+)/management/$', consumers.KitchenManagementConsumer.as_asgi()),
    re_path(r'ws/pos/(?P<restaurant_id>\d+)/sync/$', consumers.POSSynchronizationConsumer.as_asgi()),
    re_path(r'ws/tables/(?P<restaurant_id>\d+)/management/$', consumers.TableManagementConsumer.as_asgi()),
]