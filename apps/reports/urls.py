from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('profit/', views.profit_report, name='profit_report'),
    path('movements/', views.movement_report, name='movement_report'),
    
    # Exports
    path('export/sales-csv/', views.export_sales_csv, name='export_sales_csv'),
    path('export/inventory-pdf/', views.export_inventory_pdf, name='export_inventory_pdf'),
]