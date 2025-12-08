from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list, name='supplier_list'),
    path('<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('create/', views.supplier_create, name='supplier_create'),
    path('<int:supplier_id>/update/', views.supplier_update, name='supplier_update'),

    # Purchase Orders
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:po_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:po_id>/pay/', views.pay_supplier, name='pay_supplier'),
    path('purchase-orders/<int:po_id>/receive/', views.receive_purchase_order, name='receive_po'),
]