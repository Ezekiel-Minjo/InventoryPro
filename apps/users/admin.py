from django.contrib import admin
from .models import UserProfile, UserRole, Team, UserActivity,  UserSession, Announcement

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(UserRole)
admin.site.register(Team)
admin.site.register(UserActivity)
admin.site.register(UserSession)
admin.site.register(Announcement)