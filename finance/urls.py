from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FeeViewSet,
    PaymentViewSet,
    PaymentMethodViewSet,
    BursarDashboardView,
    MpesaSTKPushView,
    MpesaCallbackView,
)


# urlpatterns = router.urls
router = DefaultRouter()
router.register(r'fees', FeeViewSet, basename='fees')
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-methods')

urlpatterns = [
    
    path(
        'mpesa/stk-push/',
        MpesaSTKPushView.as_view(),
        name='mpesa-stk-push'
    ),

    path(
        'mpesa/callback/',
        MpesaCallbackView.as_view(),
        name='mpesa-callback'
    ),
    path(
       "dashboard/",
        BursarDashboardView.as_view(),
        name="bursar-dashboard",
    ),

    path('',include(router.urls)),
]
