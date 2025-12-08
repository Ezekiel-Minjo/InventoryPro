from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('low-stock/', views.low_stock, name='low_stock'),
    path('adjust/<int:product_id>/', views.adjust_stock, name='adjust_stock'),
    path('movements/', views.stock_movements, name='movements'),
    path('reports/', views.stock_report, name='stock_report'),
]
