from .forms import UserSearchForm, UserUpdateForm, UserProfileForm, UserPasswordChangeForm, UserRegistrationForm, RoleAssignmentForm, TeamForm, UserCreationForm
from .models import UserProfile, UserRole, Team, UserActivity
from .decorators import admin_required, manager_required    
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash

# Helper functions for role checks
def is_manager_or_admin(user):
    return (
        user.is_superuser or 
        (hasattr(user, "profile") and user.profile.role and user.profile.role.name in ["ADMIN", "MANAGER"])
    )

#------------------------
# User Profile Views
#------------------------
@login_required
def profile_view(request):
    return render(request, 'users/profile.html')

@login_required
def profile_edit_view(request):
    # logic to edit profile
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")    
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }          
    return render(request, "users/profile_edit.html", context)


@login_required
def change_password_view(request):
    # logic to change password
    user = request.user

    if request.method == 'POST':
        form = UserPasswordChangeForm(user, request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password has been changed successfully.")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserPasswordChangeForm(user=user) 

    return render(request, "users/change_password.html", {'form': form})

#------------------------
# User Management Views (Admin Only)
#------------------------
@login_required
@admin_required
def user_list_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('users:profile')
    
    search_form = UserSearchForm(request.GET or None)
    users = User.objects.all().select_related('profile')

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        role = search_form.cleaned_data.get('role')
        status = search_form.cleaned_data.get('status')

        if search:
            users = users.filter(
                username__icontains=search
            )
        if role:
            users = users.filter(profile__role=role)
        if status:
            users = users.filter(profile__is_active=(status == 'active'))

    context = {
        'search_form': search_form,
        'users': users,
    }
    return render(request, 'users/user_list.html', context)

@login_required
@admin_required
def user_create_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Assign default role
            role = form.cleaned_data.get('role')

            profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': role})
            if not created:
                profile.role = role
                profile.save()

            messages.success(request, "User created successfully.")
            return redirect('users:user_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/user_create.html', {'form': form})

@login_required
@admin_required
def user_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "User updated successfully.")
            return redirect('users:user_detail', user_id=user.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    context = {'user_form': user_form, 'profile_form': profile_form, 'user_obj': user}
    return render(request, 'users/user_detail.html', context)

# ----------------------------
# Activity Log (Manager+)
# ----------------------------
@login_required
@admin_required
def activity_log_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "Access denied.")
        return redirect('users:profile')

    activities = UserActivity.objects.select_related('user').all()
    context = {'activities': activities}
    return render(request, 'users/activity_log.html', context)

# ----------------------------
# Teams (Manager+)
# ----------------------------
@login_required
@admin_required
def team_list_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "Access denied.")
        return redirect('users:profile')

    teams = Team.objects.prefetch_related('members').all()
    return render(request, 'users/team_list.html', {'teams': teams})

@login_required
@admin_required
def team_create_view(request):
    if not request.user.profile.is_admin:
        messages.error(request, "Access denied.")
        return redirect('users:profile')

    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Team created successfully.")
            return redirect('users:team_list')
    else:
        form = TeamForm()

    return render(request, 'users/team_create.html', {'form': form})