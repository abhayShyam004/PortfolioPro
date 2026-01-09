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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps
import json
import jwt
from django.conf import settings

from app.models import Profile, Project, Skill
from .models import ReleaseNote

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


    return JsonResponse({'users': user_list})


def get_git_commits(limit=15):
    """Helper to fetch recent git commits"""
    import subprocess
    try:
        # Get hash, subject, date relative
        cmd = ['git', 'log', f'-n {limit}', '--pretty=format:%h|%s|%ar']
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        
        commits = []
        for line in result.split('\n'):
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 3:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'time': parts[2]
                    })
        return commits
    except Exception as e:
        print(f"Error fetching git logs: {e}")
        return []


@superadmin_required
def release_note_list(request):
    """
    List and create release notes with structured input support.
    """
    if request.method == 'POST':
        version = request.POST.get('version').strip()
        
        # Structured Input Logic
        headline = request.POST.get('headline', '').strip()
        features = request.POST.get('new_features', '').strip()
        fixes = request.POST.get('fixes', '').strip()
        improvements = request.POST.get('improvements', '').strip()
        
        # Manual Override (if they want to write raw HTML)
        raw_content = request.POST.get('content', '').strip()
        
        final_content = ""
        
        if raw_content:
            final_content = raw_content
        elif headline or features or fixes or improvements:
            # Generate HTML structure
            html_parts = [f'<div style="text-align: left;">']
            
            if headline:
                html_parts.append(f'<h3 style="color: var(--primary); margin-bottom: 15px;">🚀 {headline}</h3>')
            
            html_parts.append('<ul style="list-style-type: disc; padding-left: 20px; line-height: 1.6;">')
            
            def process_lines(text, prefix=""):
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                for line in lines:
                    clean_line = line.lstrip('-').lstrip('*').strip()
                    prefix_html = f"<strong>{prefix}:</strong> " if prefix else ""
                    html_parts.append(f'<li style="margin-bottom: 8px;">{prefix_html}{clean_line}</li>')

            if features:
                process_lines(features, "New")
            if fixes:
                process_lines(fixes, "Fixed")
            if improvements:
                process_lines(improvements, "Improved")
                
            html_parts.append('</ul>')
            html_parts.append('<p style="margin-top: 15px; font-size: 0.9em; opacity: 0.7;">Enjoy the updates! - Abhay</p>')
            html_parts.append('</div>')
            
            final_content = "\n".join(html_parts)
        
        if version and final_content:
            ReleaseNote.objects.create(
                version=version,
                content=final_content,
                is_published=False  # Draft by default
            )
            messages.success(request, f'Draft release note v{version} created.')
        else:
            messages.error(request, 'Version and content are required.')
        return redirect('superadmin:release_note_list')
    
    notes = ReleaseNote.objects.all()
    commits = get_git_commits()
    
    # Calculate next version suggestion
    from django.utils import timezone
    next_version = "1.0.0"
    latest_note = ReleaseNote.objects.order_by('-created_at').first()
    
    base_version = "1.0" # Default base for new day's releases
    if latest_note:
        try:
            parts = latest_note.version.split('.')
            if len(parts) >= 2:
                base_version = f"{parts[0]}.{parts[1]}"
        except ValueError:
            pass

    today = timezone.now().date()
    today_versions = ReleaseNote.objects.filter(
        created_at__date=today,
        version__startswith=base_version
    ).order_by('-version')

    if today_versions.exists():
        last_ver = today_versions.first().version
        try:
            parts = last_ver.split('.')
            patch = int(parts[2])
            next_patch = patch + 1
            next_version = f"{parts[0]}.{parts[1]}.{next_patch}"
        except (IndexError, ValueError):
            next_version = f"{base_version}.1"
    else:
        # If no releases today, start with .0 or .1 for the current base_version
        if latest_note:
             try:
                parts = latest_note.version.split('.')
                major, minor = int(parts[0]), int(parts[1])
                # If the latest note is from a previous day, and its major.minor matches, increment patch
                if latest_note.created_at.date() < today and f"{major}.{minor}" == base_version:
                    next_version = f"{major}.{minor}.0" # Start new patch series for today
                else: # New major.minor or first release ever
                    next_version = f"{major}.{minor}.0"
             except:
                 next_version = "1.0.0"
        else:
            next_version = "1.0.0"
    
    # helper to clean html list items for placeholder
    def extract_items(html, key):
        import re
        # Find the list associated with the key (New:, Fixed:, Improved:)
        # This regex looks for <strong>Key:</strong>...</li> items
        pattern = re.compile(rf'<strong>{key}:</strong>\s*(.*?)</li>')
        items = pattern.findall(html)
        if items:
            return "- " + "\n- ".join(items)
        return ""

    last_features = ""
    last_fixes = ""
    last_improvements = ""

    if latest_note and latest_note.content:
        last_features = extract_items(latest_note.content, "New")
        last_fixes = extract_items(latest_note.content, "Fixed")
        last_improvements = extract_items(latest_note.content, "Improved")

    context = {
        'notes': notes,
        'commits': commits,
        'next_version': next_version,
        'last_features': last_features,
        'last_fixes': last_fixes,
        'last_improvements': last_improvements,
    }
    return render(request, 'superadmin/release_note_list.html', context)


@superadmin_required
def deploy_release_note(request, note_id):
    """
    Publish/Deploy a release note and notify all users.
    """
    if request.method == 'POST':
        note = get_object_or_404(ReleaseNote, id=note_id)
        note.is_published = True
        note.save()
        
        # --- Automatic Email Notification ---
        try:
            from django.contrib.auth import get_user_model
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            user_model = get_user_model()
            # Send to all active users
            recipients = user_model.objects.filter(is_active=True).values_list('email', flat=True)
            recipient_list = [email for email in recipients if email]
            
            if recipient_list:
                email = EmailMessage(
                    subject=f"New Update: v{note.version} Released!",
                    body=f"Hello,\n\nA new update (v{note.version}) has just been released!\n\nCheck out what's new:\n{note.content}\n\nBest,\nPortfolioPro Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.DEFAULT_FROM_EMAIL],
                    bcc=recipient_list,
                )
                email.content_subtype = "html"  # Allow HTML in email if content is HTML-ish
                email.send(fail_silently=False)
                messages.success(request, f'Release note v{note.version} deployed and emailed to {len(recipient_list)} users!')
            else:
                 messages.success(request, f'Release note v{note.version} deployed (no users to email).')
                 
        except Exception as e:
            messages.warning(request, f'Release note deployed, but email failed: {str(e)}')

    return redirect('superadmin:release_note_list')


@superadmin_required
def delete_release_note(request, note_id):
    """
    Delete a release note.
    """
    if request.method == 'POST':
        note = get_object_or_404(ReleaseNote, id=note_id)
        note.delete()
        messages.success(request, f'Release note v{note.version} deleted.')
    return redirect('superadmin:release_note_list')


@superadmin_required
def broadcast_email(request):
    """Send broadcast emails to users."""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        recipient_group = request.POST.get('recipient_group')
        
        if not subject or not message:
            messages.error(request, "Subject and message are required.")
            return redirect('superadmin:broadcast_email')
            
        recipients = []
        try:
            from django.contrib.auth import get_user_model
            user_model = get_user_model()
            
            if recipient_group == 'superadmins':
                recipients = user_model.objects.filter(role='SUPERADMIN').values_list('email', flat=True)
                group_name = "All Superadmins"
            elif recipient_group == 'all_users':
                recipients = user_model.objects.filter(is_active=True).values_list('email', flat=True)
                group_name = "All Active Users"
            else:
                messages.error(request, "Invalid recipient group.")
                return redirect('superadmin:broadcast_email')
                
            # Filter out empty emails
            recipient_list = [email for email in recipients if email]
            
            if not recipient_list:
                messages.warning(request, f"No recipients found in group: {group_name}")
                return redirect('superadmin:broadcast_email')
                
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            # Send email using BCC for privacy
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],  # Send To: sender (common practice)
                bcc=recipient_list,
            )
            email.send(fail_silently=False)
            
            messages.success(request, f"Email broadcast sent to {len(recipient_list)} recipients ({group_name}).")
            
        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")
            
        return redirect('superadmin:broadcast_email')
        
    return render(request, 'superadmin/broadcast_email.html')
