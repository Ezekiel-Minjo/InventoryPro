from django.urls import path
from . import views, daraja

app_name = 'payments'

urlpatterns = [
    path('transactions/', views.transaction_list, name='transaction_list'),
    
    # M-Pesa endpoints
    path('stk-push/', views.initiate_stk_push, name='stk_push'),
    path('b2c/', views.initiate_b2c, name='b2c_payment'),
    
    # Callbacks (no authentication required)
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('result/', views.mpesa_result, name='mpesa_result'),
    path('timeout/', views.mpesa_timeout, name='mpesa_timeout'),
]