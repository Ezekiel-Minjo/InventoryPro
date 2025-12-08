from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static  
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/accounts/login/'), name='logout'),

    # Main dashboard
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),  

    # App URLs
    path('inventory/', include('apps.inventory.urls')),
    path('payments/', include('apps.payments.urls')),
    path('products/', include('apps.products.urls')),
    path('sales/', include('apps.sales.urls')),
    path('reports/', include('apps.reports.urls')),
    path('suppliers/', include('apps.suppliers.urls')),
    path('users/', include('apps.users.urls')),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
