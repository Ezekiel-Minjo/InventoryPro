from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if hasattr(request.user, 'profile') and request.user.profile.role.name == "ADMIN":
            return view_func(request, *args, **kwargs)

        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')
    return wrapper


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if hasattr(request.user, 'profile'):
            role = request.user.profile.role.name
            if role == "ADMIN" or role == "MANAGER":
                return view_func(request, *args, **kwargs)

        messages.error(request, "Only managers or admins can access this.")
        return redirect('dashboard')
    return wrapper
