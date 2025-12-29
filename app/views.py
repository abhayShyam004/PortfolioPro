"""
User-scoped views for multi-tenant portfolio platform.

All views are now scoped to:
1. request.user (for authenticated admin operations)
2. request.tenant (for public portfolio viewing via subdomain)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from functools import wraps
import json

from .models import (
    Profile, SocialLink, Expertise, Experience, 
    Education, Skill, Project, ContactInfo, SiteSettings, SavedTheme,
    AdminUser, CustomSection, CustomItem
)

User = get_user_model()


# ============== Helper Functions ==============

def get_or_create_profile(user):
    """Get the profile for a user or create a default one"""
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={
            'name': user.first_name or user.username,
            'greeting': f"Hi, I am {user.first_name or user.username}",
        }
    )
    return profile


def get_or_create_contact(user):
    """Get contact info for a user or create a default one"""
    contact, created = ContactInfo.objects.get_or_create(
        user=user,
        defaults={'email': user.email}
    )
    return contact


def get_or_create_settings(user):
    """Get site settings for a user or create default ones"""
    site_settings, created = SiteSettings.objects.get_or_create(user=user)
    return site_settings


# ============== Authentication Decorator ==============

def admin_required(view_func):
    """
    Decorator to require authentication via Django auth system.
    Works with both session auth and JWT (via DRF).
    Falls back to legacy cookie-based JWT for backward compatibility.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated via Django auth
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # Fallback: Check legacy JWT cookie (for backward compatibility during transition)
        import jwt
        token = request.COOKIES.get('admin_token')
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                # Try to get the user from the token
                username = payload.get('username')
                if username:
                    try:
                        user = User.objects.get(username=username)
                        request.user = user
                        return view_func(request, *args, **kwargs)
                    except User.DoesNotExist:
                        pass
            except jwt.PyJWTError:
                pass
        
        return redirect('admin_login')
    return wrapper


def get_admin_user(request):
    """
    Get the authenticated user for admin operations.
    Returns the Django User object.
    """
    if request.user.is_authenticated:
        return request.user
    return None


# ============== Public Portfolio View ==============

def portfolio_view(request):
    """
    Main portfolio page with dynamic content.
    
    In multi-tenant mode:
    - If request.tenant exists (from subdomain middleware), show that user's portfolio
    - Otherwise, show landing page (main site homepage)
    
    In development mode:
    - Use ?subdomain=xxx query parameter to simulate subdomain
    
    Note: Superadmin panel is accessed via /superadmin/ URL, not via subdomain.
    Everyone (including superadmins) can have a portfolio.
    """
    # Determine which user's portfolio to show
    tenant = getattr(request, 'tenant', None)
    
    if not tenant:
        # No tenant resolved - show landing page (main homepage)
        return render(request, 'app/landing.html', {
            'message': 'Create your stunning portfolio in minutes!'
        })
    
    # Check if tenant's portfolio is accessible
    if tenant.is_banned:
        raise Http404("This portfolio is not available.")
    
    # Get user-scoped data
    profile = get_or_create_profile(tenant)
    contact = get_or_create_contact(tenant)
    site_settings = get_or_create_settings(tenant)
    
    # Get orderable sections (excluding admin-only sections)
    orderable_slugs = ['about', 'skills', 'projects', 'experience', 'education', 'expertise']
    orderable_sections = CustomSection.objects.filter(
        user=tenant,
        is_visible=True
    ).filter(
        models.Q(slug__in=orderable_slugs) | models.Q(is_system=False)
    ).order_by('order')
    
    # Detect if education and experience are adjacent (for side-by-side layout)
    edu_exp_adjacent = False
    edu_first = False  # True if education comes before experience
    section_slugs = list(orderable_sections.values_list('slug', flat=True))
    for i, slug in enumerate(section_slugs):
        if slug == 'education' and i + 1 < len(section_slugs) and section_slugs[i + 1] == 'experience':
            edu_exp_adjacent = True
            edu_first = True
            break
        elif slug == 'experience' and i + 1 < len(section_slugs) and section_slugs[i + 1] == 'education':
            edu_exp_adjacent = True
            edu_first = False
            break
    
    # TERMINAL X: Data Serialization (True Hacker OS Rebuild)
    if site_settings.active_theme == 'terminal_x':
        terminal_fs = {
            "user": profile.name.lower().replace(" ", "") if profile.name else "guest",
            "hostname": "portfolio",
            "boot_config": site_settings.theme_config or {
                "show_boot_sequence": True,
                "matrix_effect": False,
                "enable_scanlines": True,
                "enabled_commands": ["help", "ls", "cd", "cat", "whoami", "skills", "projects", "experience", "contact", "links"]
            },
            "file_system": {
                "home": {
                    "user": {
                        "about.txt": profile.about_text or "No description available.",
                        "contact.txt": f"Email: {contact.email}\nPhone: {contact.phone or 'N/A'}\nHeading: {contact.contact_heading or ''}",
                        "links.txt": "\n".join([f"{l.platform}: {l.url}" for l in SocialLink.objects.filter(user=tenant)]),
                        "skills": {
                            s.name: f"Level: {s.category}\n---\n{s.description or 'No details.'}" for s in Skill.objects.filter(user=tenant)
                        },
                        "projects": {
                            p.title.lower().replace(" ", "_").replace("'", "") + ".txt": f"Title: {p.title}\nCategory: {p.category}\nURL: {p.url or 'N/A'}\n---\n{p.description}" for p in Project.objects.filter(user=tenant)
                        },
                        "experience": {
                           f"{e.company.lower().replace(' ', '_')}.log": f"[{e.timeframe}]\nRole: {e.position}\nCompany: {e.company}\n---\n{e.description}" for e in Experience.objects.filter(user=tenant)
                        },
                        "education": {
                           f"{e.institution.lower().replace(' ', '_')}.txt": f"[{e.timeframe}]\nDegree: {e.degree}\nInstitution: {e.institution}\n---\n{e.description}" for e in Education.objects.filter(user=tenant)
                        },
                         # Map custom sections as text files or directories (simplified as files for now)
                        "custom": {
                             s.title.lower().replace(" ", "_") + ".md": f"# {s.title}\n\n" + "\n\n".join([f"## {i.title}\n{i.subtitle}\n{i.description}\nLink: {i.link}" for i in s.items.all()])
                             for s in CustomSection.objects.filter(user=tenant, is_system=False, is_visible=True).prefetch_related('items')
                        }
                    }
                }
            },
            # Raw Data for Rich Formatters (Cards, Bars)
            "raw_data": {
                "skills": [{"name": s.name, "category": s.category, "description": s.description} for s in Skill.objects.filter(user=tenant)],
                "projects": [{"title": p.title, "category": p.category, "description": p.description, "url": p.url, "Tech": "N/A"} for p in Project.objects.filter(user=tenant)],
                 "experience": [{"company": e.company, "position": e.position, "timeframe": e.timeframe, "description": e.description} for e in Experience.objects.filter(user=tenant)],
            }
        }
        
        return render(request, 'app/themes/terminal_x/base.html', {
            'terminal_data_json': json.dumps(terminal_fs),
            'settings': site_settings,
        })

    context = {
        'profile': profile,
        'social_links': SocialLink.objects.filter(user=tenant),
        'expertise_list': Expertise.objects.filter(user=tenant),
        'experiences': Experience.objects.filter(user=tenant),
        'education_list': Education.objects.filter(user=tenant),
        'skills': Skill.objects.filter(user=tenant),
        'projects': Project.objects.filter(user=tenant),
        'contact': contact,
        'settings': site_settings,
        'orderable_sections': orderable_sections,
        'edu_exp_adjacent': edu_exp_adjacent,
        'edu_first': edu_first,
        'custom_sections': CustomSection.objects.filter(
            user=tenant, 
            is_system=False, 
            is_visible=True
        ).order_by('order').prefetch_related('items'),
        'tenant': tenant,
    }

    # Theme Routing
    if site_settings.active_theme == 'interactive_3d':
        return render(request, 'app/themes/interactive_3d/main.html', context)
    
    if site_settings.active_theme == 'developer_folio':
        return render(request, 'app/themes/developer_folio/main.html', context)
    
    if site_settings.active_theme == 'irish_spring':
        return render(request, 'app/themes/zachjordan_clone/main.html', context)

    return render(request, 'app/index.html', context)


def contact_view(request):
    return render(request, 'app/contact.html')


# ============== User Registration ==============

def register(request):
    """
    User registration page.
    Creates a new user account with portfolio.
    """
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('admin_panel')
    
    error = None
    success = None
    form_data = {}
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        subdomain = request.POST.get('subdomain', '').strip().lower()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        form_data = {'username': username, 'email': email, 'subdomain': subdomain}
        
        # Validation
        if not all([username, email, subdomain, password, password2]):
            error = "All fields are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != password2:
            error = "Passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = "Username is already taken."
        elif User.objects.filter(email=email).exists():
            error = "Email is already registered."
        elif User.objects.filter(subdomain=subdomain).exists():
            error = "Subdomain is already taken."
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    subdomain=subdomain,
                    role='USER'
                )
                
                # Create initial profile and settings
                from app.models import Profile, ContactInfo, SiteSettings, CustomSection
                Profile.objects.create(
                    user=user, 
                    name=username,
                    greeting=f"Hi, I am {username}"
                )
                ContactInfo.objects.create(user=user, email=email)
                SiteSettings.objects.create(user=user)
                
                # Create default system sections (matching admin panel layout)
                default_sections = [
                    {'title': 'Profile', 'slug': 'profile', 'order': 1, 'icon': 'fas fa-user'},
                    {'title': 'About', 'slug': 'about', 'order': 2, 'icon': 'fas fa-info-circle'},
                    {'title': 'Education', 'slug': 'education', 'order': 3, 'icon': 'fas fa-graduation-cap'},
                    {'title': 'Appearance', 'slug': 'appearance', 'order': 4, 'icon': 'fas fa-palette'},
                    {'title': 'Expertise', 'slug': 'expertise', 'order': 5, 'icon': 'fas fa-star'},
                    {'title': 'Experience', 'slug': 'experience', 'order': 6, 'icon': 'fas fa-briefcase'},
                    {'title': 'Skills', 'slug': 'skills', 'order': 7, 'icon': 'fas fa-code'},
                    {'title': 'Projects', 'slug': 'projects', 'order': 8, 'icon': 'fas fa-folder-open'},
                    {'title': 'Contact & Social', 'slug': 'social', 'order': 9, 'icon': 'fas fa-envelope'},
                ]
                for section_data in default_sections:
                    CustomSection.objects.create(
                        user=user,
                        title=section_data['title'],
                        slug=section_data['slug'],
                        order=section_data['order'],
                        icon=section_data['icon'],
                        is_system=True,
                        is_visible=True
                    )
                
                # Create default themes
                from app.models import SavedTheme
                default_themes = [
                    {'name': 'Default', 'primary_color': '#eabe7c', 'secondary_color': '#23967f', 'background_color': '#141516', 'text_color': '#a1a1a2', 'heading_font': 'DM Serif Display', 'body_font': 'Public Sans', 'background_style': 'circles', 'circle_color': '#eabe7c', 'button_style': 'square'},
                    {'name': 'Royal Gold', 'primary_color': '#ffd700', 'secondary_color': '#daa520', 'background_color': '#0c0800', 'text_color': '#fffbec', 'heading_font': 'DM Sans', 'body_font': 'DM Sans', 'background_style': 'grid', 'circle_color': '#ffd700', 'button_style': 'square'},
                    {'name': 'Solar Flare', 'primary_color': '#ff4500', 'secondary_color': '#ff8c00', 'background_color': '#1a0500', 'text_color': '#ffe6e6', 'heading_font': 'DM Sans', 'body_font': 'DM Sans', 'background_style': 'gradient', 'circle_color': '#ff4500', 'button_style': 'pill'},
                    {'name': 'Forest Whisper', 'primary_color': '#228b22', 'secondary_color': '#32cd32', 'background_color': '#051a05', 'text_color': '#e6ffe6', 'heading_font': 'DM Sans', 'body_font': 'DM Sans', 'background_style': 'circles', 'circle_color': '#32cd32', 'button_style': 'rounded'},
                    {'name': 'Midnight Void', 'primary_color': '#6600cc', 'secondary_color': '#9933ff', 'background_color': '#050010', 'text_color': '#f2e6ff', 'heading_font': 'DM Sans', 'body_font': 'DM Sans', 'background_style': 'gradient', 'circle_color': '#9933ff', 'button_style': 'rounded'},
                    {'name': 'Tech Blue', 'primary_color': '#0066ff', 'secondary_color': '#3399ff', 'background_color': '#000a1a', 'text_color': '#e6f2ff', 'heading_font': 'DM Sans', 'body_font': 'DM Sans', 'background_style': 'particles', 'circle_color': '#0066ff', 'button_style': 'rounded'},
                    {'name': 'Strawberry Blast', 'primary_color': '#ff0055', 'secondary_color': '#ff6699', 'background_color': '#2e0011', 'text_color': '#ffddee', 'heading_font': 'DM Sans', 'body_font': 'DM Sans', 'background_style': 'circles', 'circle_color': '#ff0055', 'button_style': 'pill'},
                    {'name': 'Cyberpunk Neon', 'primary_color': '#00ff00', 'secondary_color': '#00ffff', 'background_color': '#000000', 'text_color': '#ffffff', 'heading_font': 'DM Sans', 'body_font': 'DM Sans', 'background_style': 'grid', 'circle_color': '#ff00ff', 'button_style': 'square'},
                ]
                for theme_data in default_themes:
                    SavedTheme.objects.create(user=user, **theme_data)
                
                # Create default social links with empty URLs
                from app.models import SocialLink
                default_social_links = [
                    {'platform': 'linkedin', 'display_name': 'LinkedIn', 'url': '', 'order': 1},
                    {'platform': 'leetcode', 'display_name': 'LeetCode', 'url': '', 'order': 2},
                    {'platform': 'github', 'display_name': 'GitHub', 'url': '', 'order': 3},
                    {'platform': 'instagram', 'display_name': 'Instagram', 'url': '', 'order': 4},
                ]
                for link_data in default_social_links:
                    SocialLink.objects.create(user=user, **link_data)
                
                import jwt
                import datetime
                payload = {
                    'user_id': user.id,
                    'username': user.username,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                    'iat': datetime.datetime.utcnow()
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                
                response = redirect('admin_panel')
                response.set_cookie(
                    'admin_token', 
                    token, 
                    max_age=60*60*24,
                    httponly=True, 
                    samesite='Lax'
                )
                return response
                
            except Exception as e:
                error = f"Registration failed: {str(e)}"
    
    return render(request, 'app/register.html', {
        'error': error,
        'success': success,
        'form_data': form_data
    })


# ============== Admin Login/Logout ==============

def admin_login(request):
    """
    Admin login page - now uses Django's auth system with JWT tokens.
    Supports both new User model and legacy AdminUser for transition.
    
    Superadmins are redirected to /superadmin/ panel.
    Regular users are redirected to /admin-panel/ for portfolio management.
    """
    # Check if already logged in
    if request.user.is_authenticated:
        # Redirect superadmins to superadmin panel, others to admin panel
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin:
            return redirect('superadmin:dashboard')
        return redirect('admin_panel')
    
    # Check legacy JWT cookie
    import jwt
    import datetime
    token = request.COOKIES.get('admin_token')
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            # Check if this is a superadmin
            user_id = payload.get('user_id')
            if user_id:
                user = User.objects.filter(id=user_id).first()
                if user and user.is_superadmin:
                    return redirect('superadmin:dashboard')
            return redirect('admin_panel')
        except jwt.PyJWTError:
            pass
    
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        # Try new User model first
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                if user.is_banned:
                    error = "Your account has been suspended."
                elif not user.is_active:
                    error = "Your account is not active."
                else:
                    # Generate JWT for cookie-based auth (legacy support)
                    payload = {
                        'user_id': user.id,
                        'username': user.username,
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                        'iat': datetime.datetime.utcnow()
                    }
                    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                    
                    # Redirect based on role
                    if user.is_superadmin:
                        response = redirect('superadmin:dashboard')
                    else:
                        response = redirect('admin_panel')
                    
                    response.set_cookie(
                        'admin_token', 
                        token, 
                        max_age=60*60*24,
                        httponly=True, 
                        samesite='Lax'
                    )
                    return response
            else:
                error = "Invalid username or password"
        except User.DoesNotExist:
            # Fallback to legacy AdminUser for transition
            try:
                admin_user = AdminUser.objects.get(username=username)
                if admin_user.check_password(password):
                    payload = {
                        'username': admin_user.username,
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                        'iat': datetime.datetime.utcnow()
                    }
                    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                    
                    response = redirect('admin_panel')
                    response.set_cookie(
                        'admin_token', 
                        token, 
                        max_age=60*60*24,
                        httponly=True, 
                        samesite='Lax'
                    )
                    return response
                else:
                    error = "Invalid username or password"
            except AdminUser.DoesNotExist:
                error = "Invalid username or password"
    
    return render(request, 'app/admin_login.html', {'error': error})


def admin_logout(request):
    """Admin logout"""
    from django.contrib.auth import logout
    logout(request)
    response = redirect('home')
    response.delete_cookie('admin_token')
    return response


# ============== Admin Panel ==============

@admin_required
def admin_panel(request):
    """Main admin panel dashboard - user-scoped. For regular users only."""
    user = get_admin_user(request)
    if not user:
        return redirect('admin_login')
    
    # Superadmins don't have portfolio admin panels - redirect to superadmin panel
    if hasattr(user, 'is_superadmin') and user.is_superadmin:
        return redirect('superadmin:dashboard')
    
    profile = get_or_create_profile(user)
    contact = get_or_create_contact(user)
    site_settings = get_or_create_settings(user)
    
    context = {
        'profile': profile,
        'social_links': SocialLink.objects.filter(user=user),
        'expertise_list': Expertise.objects.filter(user=user),
        'experiences': Experience.objects.filter(user=user),
        'education_list': Education.objects.filter(user=user),
        'skills': Skill.objects.filter(user=user),
        'projects': Project.objects.filter(user=user),
        'contact': contact,
        'platform_choices': SocialLink.PLATFORM_CHOICES,
        'settings': site_settings,
        'saved_themes': SavedTheme.objects.filter(user=user),
        'font_choices': SiteSettings.FONT_CHOICES,
        'button_style_choices': SiteSettings.BUTTON_STYLE_CHOICES,
        'style_choices': SiteSettings.STYLE_CHOICES,
        'theme_choices': SiteSettings.THEME_CHOICES,
        'custom_sections': CustomSection.objects.filter(user=user, is_system=False).prefetch_related('items'),
        'all_sections': CustomSection.objects.filter(user=user).order_by('order'),
        'main_page_sections': CustomSection.objects.filter(user=user).filter(
            models.Q(slug__in=['about', 'skills', 'projects', 'experience', 'education', 'expertise']) | 
            models.Q(is_system=False)
        ).order_by('order'),
        'icon_choices': [
            'fas fa-layer-group', 'fas fa-trophy', 'fas fa-certificate', 'fas fa-star', 
            'fas fa-heart', 'fas fa-globe', 'fas fa-book', 'fas fa-camera', 
            'fas fa-code', 'fas fa-laptop-code', 'fas fa-terminal', 'fas fa-palette', 
            'fas fa-pen-nib', 'fas fa-music', 'fas fa-video', 'fas fa-dumbbell', 
            'fas fa-utensils', 'fas fa-car', 'fas fa-plane', 'fas fa-briefcase', 
            'fas fa-graduation-cap', 'fas fa-rocket', 'fas fa-lightbulb', 'fas fa-puzzle-piece'
        ],
        'next_section_order': CustomSection.objects.filter(user=user).count() + 1,
        'current_user': user,
    }
    return render(request, 'app/admin_panel.html', context)


# ============== Profile API ==============

@admin_required
def update_profile(request):
    """Update profile information - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        profile = get_or_create_profile(user)
        
        profile.name = request.POST.get('name', profile.name)
        profile.greeting = request.POST.get('greeting', profile.greeting)
        profile.hero_bio = request.POST.get('hero_bio', profile.hero_bio)
        profile.about_text = request.POST.get('about_text', profile.about_text)
        profile.cv_link = request.POST.get('cv_link', profile.cv_link)
        profile.ai_assistant_script = request.POST.get('ai_assistant_script', profile.ai_assistant_script)
        
        if 'about_photo' in request.FILES:
            profile.about_photo = request.FILES['about_photo']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
    
    return redirect('admin_panel')


# ============== Contact API ==============

@admin_required
def update_contact(request):
    """Update contact information - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        contact = get_or_create_contact(user)
        
        contact.email = request.POST.get('email', contact.email)
        contact.phone = request.POST.get('phone', contact.phone)
        contact.contact_heading = request.POST.get('contact_heading', contact.contact_heading)
        contact.save()
        messages.success(request, 'Contact info updated successfully!')
    
    return redirect('/admin-panel/?section=social')


# ============== Social Links API ==============

@admin_required
def add_social_link(request):
    """Add social link - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        SocialLink.objects.create(
            user=user,
            platform=request.POST.get('platform'),
            display_name=request.POST.get('display_name', ''),
            url=request.POST.get('url'),
            order=request.POST.get('order', 0)
        )
        messages.success(request, 'Social link added successfully!')
    return redirect('/admin-panel/?section=social')


@admin_required
def update_social_link(request, pk):
    """Update social link - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        link = get_object_or_404(SocialLink, pk=pk, user=user)
        
        link.platform = request.POST.get('platform', link.platform)
        link.display_name = request.POST.get('display_name', link.display_name)
        link.url = request.POST.get('url', link.url)
        link.order = request.POST.get('order', link.order)
        link.save()
        messages.success(request, 'Social link updated successfully!')
    return redirect('/admin-panel/?section=social')


@admin_required
def delete_social_link(request, pk):
    """Delete social link - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        link = get_object_or_404(SocialLink, pk=pk, user=user)
        link.delete()
        messages.success(request, 'Social link deleted successfully!')
    return redirect('/admin-panel/?section=social')


# ============== Expertise API ==============

@admin_required
def add_expertise(request):
    """Add expertise - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        Expertise.objects.create(
            user=user,
            name=request.POST.get('name'),
            order=request.POST.get('order', 0)
        )
        messages.success(request, 'Expertise added successfully!')
    return redirect('/admin-panel/?section=expertise')


@admin_required
def update_expertise(request, pk):
    """Update expertise - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        item = get_object_or_404(Expertise, pk=pk, user=user)
        
        item.name = request.POST.get('name', item.name)
        item.order = request.POST.get('order', item.order)
        item.save()
        messages.success(request, 'Expertise updated successfully!')
    return redirect('/admin-panel/?section=expertise')


@admin_required
def delete_expertise(request, pk):
    """Delete expertise - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        item = get_object_or_404(Expertise, pk=pk, user=user)
        item.delete()
        messages.success(request, 'Expertise deleted successfully!')
    return redirect('/admin-panel/?section=expertise')


# ============== Experience API ==============

@admin_required
def add_experience(request):
    """Add experience - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        Experience.objects.create(
            user=user,
            company=request.POST.get('company'),
            position=request.POST.get('position'),
            timeframe=request.POST.get('timeframe'),
            description=request.POST.get('description'),
            order=request.POST.get('order', 0)
        )
        messages.success(request, 'Experience added successfully!')
    return redirect('/admin-panel/?section=experience')


@admin_required
def update_experience(request, pk):
    """Update experience - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        exp = get_object_or_404(Experience, pk=pk, user=user)
        
        exp.company = request.POST.get('company', exp.company)
        exp.position = request.POST.get('position', exp.position)
        exp.timeframe = request.POST.get('timeframe', exp.timeframe)
        exp.description = request.POST.get('description', exp.description)
        exp.order = request.POST.get('order', exp.order)
        exp.save()
        messages.success(request, 'Experience updated successfully!')
    return redirect('/admin-panel/?section=experience')


@admin_required
def delete_experience(request, pk):
    """Delete experience - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        exp = get_object_or_404(Experience, pk=pk, user=user)
        exp.delete()
        messages.success(request, 'Experience deleted successfully!')
    return redirect('/admin-panel/?section=experience')


# ============== Education API ==============

@admin_required
def add_education(request):
    """Add education - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        Education.objects.create(
            user=user,
            institution=request.POST.get('institution'),
            degree=request.POST.get('degree'),
            timeframe=request.POST.get('timeframe'),
            description=request.POST.get('description'),
            order=request.POST.get('order', 0)
        )
        messages.success(request, 'Education added successfully!')
    return redirect('/admin-panel/?section=education')


@admin_required
def update_education(request, pk):
    """Update education - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        edu = get_object_or_404(Education, pk=pk, user=user)
        
        edu.institution = request.POST.get('institution', edu.institution)
        edu.degree = request.POST.get('degree', edu.degree)
        edu.timeframe = request.POST.get('timeframe', edu.timeframe)
        edu.description = request.POST.get('description', edu.description)
        edu.order = request.POST.get('order', edu.order)
        edu.save()
        messages.success(request, 'Education updated successfully!')
    return redirect('/admin-panel/?section=education')


@admin_required
def delete_education(request, pk):
    """Delete education - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        edu = get_object_or_404(Education, pk=pk, user=user)
        edu.delete()
        messages.success(request, 'Education deleted successfully!')
    return redirect('/admin-panel/?section=education')


# ============== Skills API ==============

@admin_required
def add_skill(request):
    """Add skill - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        skill = Skill.objects.create(
            user=user,
            name=request.POST.get('name'),
            category=request.POST.get('category'),
            description=request.POST.get('description', ''),
            order=request.POST.get('order', 0)
        )
        if 'icon' in request.FILES:
            skill.icon = request.FILES['icon']
            skill.save()
        messages.success(request, 'Skill added successfully!')
    return redirect('/admin-panel/?section=skills')


@admin_required
def update_skill(request, pk):
    """Update skill - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        skill = get_object_or_404(Skill, pk=pk, user=user)
        
        skill.name = request.POST.get('name', skill.name)
        skill.category = request.POST.get('category', skill.category)
        skill.description = request.POST.get('description', skill.description)
        skill.order = request.POST.get('order', skill.order)
        if 'icon' in request.FILES:
            skill.icon = request.FILES['icon']
        skill.save()
        messages.success(request, 'Skill updated successfully!')
    return redirect('/admin-panel/?section=skills')


@admin_required
def delete_skill(request, pk):
    """Delete skill - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        skill = get_object_or_404(Skill, pk=pk, user=user)
        skill.delete()
        messages.success(request, 'Skill deleted successfully!')
    return redirect('/admin-panel/?section=skills')


# ============== Projects API ==============

@admin_required
def add_project(request):
    """Add project - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        project = Project.objects.create(
            user=user,
            title=request.POST.get('title'),
            category=request.POST.get('category'),
            url=request.POST.get('url'),
            description=request.POST.get('description', ''),
            order=request.POST.get('order', 0)
        )
        if 'icon' in request.FILES:
            project.icon = request.FILES['icon']
            project.save()
        messages.success(request, 'Project added successfully!')
    return redirect('/admin-panel/?section=projects')


@admin_required
def update_project(request, pk):
    """Update project - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        project = get_object_or_404(Project, pk=pk, user=user)
        
        project.title = request.POST.get('title', project.title)
        project.category = request.POST.get('category', project.category)
        project.url = request.POST.get('url', project.url)
        project.description = request.POST.get('description', project.description)
        project.order = request.POST.get('order', project.order)
        if 'icon' in request.FILES:
            project.icon = request.FILES['icon']
        project.save()
        messages.success(request, 'Project updated successfully!')
    return redirect('/admin-panel/?section=projects')


@admin_required
def delete_project(request, pk):
    """Delete project - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        project = get_object_or_404(Project, pk=pk, user=user)
        project.delete()
        messages.success(request, 'Project deleted successfully!')
    return redirect('/admin-panel/?section=projects')


# ============== Appearance API ==============

@admin_required
def update_appearance(request):
    """Update site appearance settings - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        site_settings = get_or_create_settings(user)
        
        # Color Scheme
        site_settings.primary_color = request.POST.get('primary_color', site_settings.primary_color)
        site_settings.secondary_color = request.POST.get('secondary_color', site_settings.secondary_color)
        site_settings.background_color = request.POST.get('background_color', site_settings.background_color)
        
        # Handle both old and new field names for text color
        text_color_value = request.POST.get('text_color') or request.POST.get('hero_about_text_color')
        if text_color_value:
            site_settings.hero_about_text_color = text_color_value
        
        general_text_value = request.POST.get('general_text_color')
        if general_text_value:
            site_settings.general_text_color = general_text_value
        
        # Typography
        site_settings.heading_font = request.POST.get('heading_font', site_settings.heading_font)
        site_settings.body_font = request.POST.get('body_font', site_settings.body_font)
        
        # Font Sizes
        try:
            site_settings.name_font_size = float(request.POST.get('name_font_size', site_settings.name_font_size))
            site_settings.greeting_font_size = float(request.POST.get('greeting_font_size', site_settings.greeting_font_size))
            site_settings.name_font_size_mobile = float(request.POST.get('name_font_size_mobile', site_settings.name_font_size_mobile))
            site_settings.greeting_font_size_mobile = float(request.POST.get('greeting_font_size_mobile', site_settings.greeting_font_size_mobile))
        except (ValueError, TypeError):
            pass
        
        # Section Visibility - NOW HANDLED IN MANAGE SECTIONS TAB VIA TOGGLE API
        # old code removed to prevent accidental overwrites

        
        # Background Effects
        site_settings.background_style = request.POST.get('background_style', site_settings.background_style)
        site_settings.circle_color = request.POST.get('circle_color', site_settings.circle_color)
        
        # Button Style
        site_settings.button_style = request.POST.get('button_style', site_settings.button_style)
        
        # Theme Selection
        active_theme = request.POST.get('active_theme')
        if active_theme:
            site_settings.active_theme = active_theme
            
            # Interactive 3D Configuration
            if active_theme == 'interactive_3d':
                config = site_settings.theme_config or {}
                config['effect_type'] = request.POST.get('vanta_effect_type', 'net')
                config['color'] = request.POST.get('vanta_color', '#6366f1')
                config['background_color'] = request.POST.get('vanta_bg_color', '#0a0a0a')
                config['intensity'] = request.POST.get('vanta_intensity', '1.0')
                config['speed'] = request.POST.get('vanta_speed', '1.0')
                config['opacity'] = request.POST.get('vanta_opacity', '1.0')
                config['glass_opacity'] = request.POST.get('glass_opacity', '0.1')
                config['mouse_controls'] = request.POST.get('vanta_mouse_controls') == 'true'
                site_settings.theme_config = config
        
        site_settings.save()
        messages.success(request, 'Appearance settings updated successfully!')
    
    return redirect('/admin-panel/?section=appearance')


@admin_required
def save_theme(request):
    """Save current settings as a named theme - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        site_settings = get_or_create_settings(user)
        theme_name = request.POST.get('theme_name', 'My Theme')
        
        SavedTheme.objects.create(
            user=user,
            name=theme_name,
            primary_color=site_settings.primary_color,
            secondary_color=site_settings.secondary_color,
            background_color=site_settings.background_color,
            text_color=site_settings.text_color,
            heading_font=site_settings.heading_font,
            body_font=site_settings.body_font,
            background_style=site_settings.background_style,
            circle_color=site_settings.circle_color,
            button_style=site_settings.button_style,
        )
        messages.success(request, f'Theme "{theme_name}" saved successfully!')
    
    return redirect('/admin-panel/?section=appearance')


@admin_required
def load_theme(request, pk):
    """Load a saved theme - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        theme = get_object_or_404(SavedTheme, pk=pk, user=user)
        site_settings = get_or_create_settings(user)
        
        site_settings.primary_color = theme.primary_color
        site_settings.secondary_color = theme.secondary_color
        site_settings.background_color = theme.background_color
        site_settings.text_color = theme.text_color
        site_settings.heading_font = theme.heading_font
        site_settings.body_font = theme.body_font
        site_settings.background_style = theme.background_style
        site_settings.circle_color = theme.circle_color
        site_settings.button_style = theme.button_style
        site_settings.save()
        
        messages.success(request, f'Theme "{theme.name}" loaded successfully!')
    
    return redirect('/admin-panel/?section=appearance')


@admin_required
def delete_theme(request, pk):
    """Delete a saved theme - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        theme = get_object_or_404(SavedTheme, pk=pk, user=user)
        theme_name = theme.name
        theme.delete()
        messages.success(request, f'Theme "{theme_name}" deleted successfully!')
    
    return redirect('/admin-panel/?section=appearance')


# ============== Custom Sections API ==============

@admin_required
def add_section(request):
    """Add a new custom section - user-scoped"""
    if request.method == 'POST':
        user = get_admin_user(request)
        CustomSection.objects.create(
            user=user,
            title=request.POST.get('title'),
            icon=request.POST.get('icon', 'fas fa-layer-group'),
            order=request.POST.get('order', 0),
            show_image=request.POST.get('show_image') == 'on',
            show_link_button=request.POST.get('show_link_button') == 'on',
            button_text=request.POST.get('button_text', 'View Details'),
            card_layout=request.POST.get('card_layout', 'grid')
        )
        messages.success(request, 'Section added successfully!')
    return redirect('admin_panel')


@admin_required
def delete_section(request, pk):
    """Delete a custom section - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        section = get_object_or_404(CustomSection, pk=pk, user=user)
        section.delete()
        messages.success(request, 'Section deleted successfully!')
    return redirect('/admin-panel/?section=manage-sections')


@admin_required
def add_custom_item(request, section_id):
    """Add an item to a custom section - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        section = get_object_or_404(CustomSection, pk=section_id, user=user)
        
        item = CustomItem.objects.create(
            section=section,
            title=request.POST.get('title'),
            subtitle=request.POST.get('subtitle', ''),
            description=request.POST.get('description', ''),
            link=request.POST.get('link', ''),
            order=request.POST.get('order', 0)
        )
        if 'icon' in request.FILES:
            item.icon = request.FILES['icon']
            item.save()
        messages.success(request, 'Item added successfully!')
    return redirect(f'/admin-panel/?section={section.slug}')


@admin_required
def update_custom_item(request, pk):
    """Update a custom item - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        item = get_object_or_404(CustomItem, pk=pk, section__user=user)
        
        item.title = request.POST.get('title', item.title)
        item.subtitle = request.POST.get('subtitle', item.subtitle)
        item.description = request.POST.get('description', item.description)
        item.link = request.POST.get('link', item.link)
        item.order = request.POST.get('order', item.order)
        if 'icon' in request.FILES:
            item.icon = request.FILES['icon']
        item.save()
        messages.success(request, 'Item updated successfully!')
    return redirect(f'/admin-panel/?section={item.section.slug}')


@admin_required
def delete_custom_item(request, pk):
    """Delete a custom item - with ownership check"""
    if request.method == 'POST':
        user = get_admin_user(request)
        item = get_object_or_404(CustomItem, pk=pk, section__user=user)
        section_slug = item.section.slug
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect(f'/admin-panel/?section={section_slug}')
    return redirect('admin_panel')


@admin_required
def update_section_order(request):
    """API to update section order via Drag & Drop - user-scoped"""
    if request.method == "POST":
        user = get_admin_user(request)
        try:
            data = json.loads(request.body)
            order_list = data.get('order', [])
            for index, section_id in enumerate(order_list):
                # Only update sections owned by user
                CustomSection.objects.filter(
                    id=section_id, 
                    user=user
                ).update(order=index + 1)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@admin_required
def toggle_section_visibility(request):
    """API to toggle visibility of sections (System or Custom) - user-scoped"""
    if request.method == "POST":
        user = get_admin_user(request)
        try:
            data = json.loads(request.body)
            item_id = data.get('id')
            item_type = data.get('type')  # 'section' or 'setting'
            
            is_visible = False
            
            if item_type == 'section':
                # Toggle CustomSection (includes About, Skills, etc.)
                section = CustomSection.objects.get(id=item_id, user=user)
                section.is_visible = not section.is_visible
                section.save()
                is_visible = section.is_visible
                message = f"Section '{section.title}' is now {'Visible' if is_visible else 'Hidden'}"
                
            elif item_type == 'setting':
                # Toggle SiteSettings field (for Intro/Contact)
                settings = get_or_create_settings(user)
                field_name = item_id # e.g. 'show_intro_section'
                
                # Verify it's a valid boolean field
                if hasattr(settings, field_name) and field_name.startswith('show_'):
                    current_val = getattr(settings, field_name)
                    setattr(settings, field_name, not current_val)
                    settings.save()
                    is_visible = not current_val
                    message = f"Section is now {'Visible' if is_visible else 'Hidden'}"
                else:
                    return JsonResponse({'status': 'error', 'message': 'Invalid setting field'}, status=400)
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid item type'}, status=400)

            return JsonResponse({'status': 'success', 'is_visible': is_visible, 'message': message})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@admin_required
@require_http_methods(["POST"])
def edit_section(request, pk):
    """Update section properties (title, icon, layout, etc.)"""
    section = get_object_or_404(CustomSection, pk=pk, user=request.user)
    
    try:
        data = json.loads(request.body)
        
        # Update fields
        if 'title' in data:
            section.title = data['title']
        if 'icon' in data:
            section.icon = data['icon']
        if 'card_layout' in data:
            section.card_layout = data['card_layout']
        if 'show_image' in data:
            section.show_image = data['show_image']
        if 'show_link_button' in data:
            section.show_link_button = data['show_link_button']
        if 'button_text' in data:
            section.button_text = data['button_text']
            
        section.save()
        
        return JsonResponse({'status': 'success', 'message': 'Section updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

