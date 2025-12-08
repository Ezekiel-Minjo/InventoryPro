from django.urls import path
from . import views

app_name = 'users'
urlpatterns = [
    # User Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/change-password/', views.change_password_view, name='change_password'),

    # User Management URLs (Admin Only)
    path('list/', views.user_list_view, name='user_list'),
    path('create/', views.user_create_view, name='user_create'),
    path('<int:user_id>/', views.user_detail_view, name='user_detail'),

    # Activity Log (Managers+)
    path('activity/', views.activity_log_view, name='activity_log'),

    # Team (Managers+)
    path('teams/', views.team_list_view, name='team_list'),
    path('teams/create/', views.team_create_view, name='team_create'),
]