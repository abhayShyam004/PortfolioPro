"""
Superadmin views for platform management.

These views are only accessible by users with role=SUPERADMIN.
Provides functionality for:
- User management (list, activate, deactivate, ban)
- User impersonation
- Platform statistics
- Global theme management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps
import json
import jwt
from django.conf import settings

from app.models import Profile, Project, Skill

User = get_user_model()


def superadmin_required(view_func):
    """
    Decorator to require superadmin privileges.
    Works with both session auth and JWT cookie.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = None
        
        # Check Django auth first
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback to JWT cookie
            token = request.COOKIES.get('admin_token')
            if token:
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                    user_id = payload.get('user_id')
                    username = payload.get('username')
                    if user_id:
                        user = User.objects.filter(id=user_id).first()
                    elif username:
                        user = User.objects.filter(username=username).first()
                except jwt.PyJWTError:
                    pass
        
        if not user:
            return redirect('admin_login')
        
        if not user.is_superadmin:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('admin_panel')
        
        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapper


@superadmin_required
def dashboard(request):
    """
    Superadmin dashboard with platform statistics.
    """
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True, is_banned=False).count()
    banned_users = User.objects.filter(is_banned=True).count()
    superadmins = User.objects.filter(role='SUPERADMIN').count()
    
    # Recent users
    recent_users = User.objects.order_by('-created_at')[:10]
    
    # Content statistics
    total_profiles = Profile.objects.count()
    total_projects = Project.objects.count()
    total_skills = Skill.objects.count()
    
    # Users with most content (exclude superadmins - they don't have portfolios)
    top_users = User.objects.filter(role='USER').annotate(
        project_count=Count('projects', distinct=True),
        skill_count=Count('skills', distinct=True)
    ).order_by('-project_count')[:5]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'banned_users': banned_users,
        'superadmins': superadmins,
        'recent_users': recent_users,
        'total_profiles': total_profiles,
        'total_projects': total_projects,
        'total_skills': total_skills,
        'top_users': top_users,
    }
    return render(request, 'superadmin/dashboard.html', context)


@superadmin_required
def user_list(request):
    """
    List all users with filtering and pagination.
    """
    users = User.objects.all().order_by('-created_at')
    
    # Filters
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True, is_banned=False)
    elif status_filter == 'banned':
        users = users.filter(is_banned=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(subdomain__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    context = {
        'users': users_page,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search': search,
        'role_choices': User.Role.choices,
    }
    return render(request, 'superadmin/user_list.html', context)


@superadmin_required
def user_detail(request, user_id):
    """
    View detailed user information.
    """
    target_user = get_object_or_404(User, id=user_id)
    
    # Get user's content
    profile = Profile.objects.filter(user=target_user).first()
    projects = Project.objects.filter(user=target_user)
    skills = Skill.objects.filter(user=target_user)
    
    context = {
        'target_user': target_user,
        'profile': profile,
        'projects': projects,
        'skills': skills,
    }
    return render(request, 'superadmin/user_detail.html', context)


@superadmin_required
def toggle_user_status(request, user_id):
    """
    Toggle user active status (activate/deactivate).
    """
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        # Don't allow deactivating yourself
        if target_user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect('superadmin:user_list')
        
        target_user.is_active = not target_user.is_active
        target_user.save()
        
        status = "activated" if target_user.is_active else "deactivated"
        messages.success(request, f'User {target_user.username} has been {status}.')
    
    return redirect('superadmin:user_list')


@superadmin_required
def ban_user(request, user_id):
    """
    Ban a user (prevent access to their portfolio and admin).
    """
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        # Don't allow banning yourself or other superadmins
        if target_user == request.user:
            messages.error(request, "You cannot ban your own account.")
            return redirect('superadmin:user_list')
        
        if target_user.is_superadmin:
            messages.error(request, "You cannot ban another superadmin.")
            return redirect('superadmin:user_list')
        
        target_user.is_banned = True
        target_user.save()
        
        # Invalidate tenant cache
        from app.middleware import SubdomainMiddleware
        SubdomainMiddleware.invalidate_tenant_cache(target_user.subdomain)
        
        messages.success(request, f'User {target_user.username} has been banned.')
    
    return redirect('superadmin:user_list')


@superadmin_required
def unban_user(request, user_id):
    """
    Unban a user.
    """
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        target_user.is_banned = False
        target_user.save()
        
        # Invalidate tenant cache
        from app.middleware import SubdomainMiddleware
        SubdomainMiddleware.invalidate_tenant_cache(target_user.subdomain)
        
        messages.success(request, f'User {target_user.username} has been unbanned.')
    
    return redirect('superadmin:user_list')


@superadmin_required
def reset_user_password(request, user_id):
    """
    Reset a user's password to a temporary one.
    """
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        # Generate temporary password
        import secrets
        temp_password = secrets.token_urlsafe(12)
        target_user.set_password(temp_password)
        target_user.save()
        
        messages.success(
            request, 
            f'Password reset for {target_user.username}. Temporary password: {temp_password}'
        )
    
    return redirect('superadmin:user_detail', user_id=user_id)


@superadmin_required
def impersonate_user(request, user_id):
    """
    Impersonate a user (login as them temporarily).
    Stores original superadmin in session for return.
    """
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        # Clear any existing impersonation data first
        if 'impersonator_id' in request.session:
            del request.session['impersonator_id']
        if 'impersonator_username' in request.session:
            del request.session['impersonator_username']
        
        # Store original admin info
        request.session['impersonator_id'] = request.user.id
        request.session['impersonator_username'] = request.user.username
        request.session.modified = True
        
        # Generate JWT for target user with a unique timestamp to prevent caching
        import datetime
        import time
        payload = {
            'user_id': target_user.id,
            'username': target_user.username,
            'impersonated': True,
            'nonce': int(time.time() * 1000),  # Unique nonce to prevent caching
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        response = redirect('admin_panel')
        # Delete old cookie first, then set new one
        response.delete_cookie('admin_token')
        response.set_cookie(
            'admin_token', 
            token, 
            max_age=60*60,  # 1 hour for impersonation
            httponly=True, 
            samesite='Lax'
        )
        
        messages.info(request, f'Now impersonating {target_user.username}. Click "End Impersonation" to return.')
        return response
    
    return redirect('superadmin:user_list')


@superadmin_required
def end_impersonation(request):
    """
    End impersonation and return to superadmin account.
    """
    impersonator_id = request.session.get('impersonator_id')
    
    if impersonator_id:
        original_user = get_object_or_404(User, id=impersonator_id)
        
        # Clear impersonation session data
        del request.session['impersonator_id']
        if 'impersonator_username' in request.session:
            del request.session['impersonator_username']
        
        # Generate JWT for original user
        import datetime
        payload = {
            'user_id': original_user.id,
            'username': original_user.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        response = redirect('superadmin:dashboard')
        response.set_cookie(
            'admin_token', 
            token, 
            max_age=60*60*24,
            httponly=True, 
            samesite='Lax'
        )
        
        messages.success(request, 'Impersonation ended. Welcome back!')
        return response
    
    messages.warning(request, 'No active impersonation to end.')
    return redirect('admin_panel')


@superadmin_required
def change_user_role(request, user_id):
    """
    Change a user's role (USER <-> SUPERADMIN).
    """
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        
        if new_role not in ['USER', 'SUPERADMIN']:
            messages.error(request, 'Invalid role.')
            return redirect('superadmin:user_detail', user_id=user_id)
        
        # Don't allow demoting yourself
        if target_user == request.user and new_role == 'USER':
            messages.error(request, "You cannot demote your own account.")
            return redirect('superadmin:user_detail', user_id=user_id)
        
        target_user.role = new_role
        target_user.is_staff = (new_role == 'SUPERADMIN')
        target_user.is_superuser = (new_role == 'SUPERADMIN')
        target_user.save()
        
        messages.success(request, f'User {target_user.username} role changed to {new_role}.')
    
    return redirect('superadmin:user_detail', user_id=user_id)


# ============== API Endpoints ==============

@superadmin_required
def api_user_stats(request):
    """
    API endpoint for user statistics (for AJAX dashboards).
    """
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True, is_banned=False).count(),
        'banned_users': User.objects.filter(is_banned=True).count(),
        'superadmins': User.objects.filter(role='SUPERADMIN').count(),
        'total_projects': Project.objects.count(),
        'total_skills': Skill.objects.count(),
    }
    return JsonResponse(stats)


@superadmin_required
def api_recent_users(request):
    """
    API endpoint for recent users.
    """
    limit = int(request.GET.get('limit', 10))
    users = User.objects.order_by('-created_at')[:limit]
    
    user_list = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'subdomain': u.subdomain,
        'role': u.role,
        'is_active': u.is_active,
        'is_banned': u.is_banned,
        'created_at': u.created_at.isoformat(),
    } for u in users]
    
    return JsonResponse({'users': user_list})
