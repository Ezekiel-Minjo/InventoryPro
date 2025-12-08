from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_list, name='sales_list'),
    path('new/', views.new_sale, name='new_sale'),
    path('<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('<int:sale_id>/refund/', views.refund_sale, name='refund_sale'),

    # API endpoints for POS
    path('api/search/', views.search_product, name='search_product'),
    path('api/check-status/<str:checkout_request_id>/', views.check_payment_status, name='check_payment_status'),
    
    # Reports
    path('reports/daily/', views.daily_sales_report, name='daily_report'),
]
