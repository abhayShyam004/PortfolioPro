from django.urls import path
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from . import views


def health_check(request):
    """Health check endpoint for Docker/Kubernetes"""
    return JsonResponse({'status': 'healthy', 'service': 'portfoliopro'})


def debug_subdomain(request):
    """Debug endpoint to check subdomain resolution"""
    User = get_user_model()
    subdomain_param = request.GET.get('subdomain', '')
    
    # Get all subdomains in database
    all_subdomains = list(User.objects.values_list('subdomain', flat=True))
    
    # Check if subdomain exists
    user_exists = User.objects.filter(subdomain__iexact=subdomain_param).exists() if subdomain_param else False
    
    return JsonResponse({
        'requested_subdomain': subdomain_param,
        'subdomain_from_request': getattr(request, 'subdomain', None),
        'tenant_resolved': getattr(request, 'tenant', None) is not None,
        'tenant_username': getattr(request, 'tenant', None).username if getattr(request, 'tenant', None) else None,
        'user_exists_in_db': user_exists,
        'all_subdomains_in_db': all_subdomains,
        'host': request.get_host(),
    })


urlpatterns = [
    # Health Check & Debug
    path('health/', health_check, name='health_check'),
    path('debug-subdomain/', debug_subdomain, name='debug_subdomain'),
    
    # Main portfolio
    path('', views.portfolio_view, name='home'),
    path('contact/', views.contact_view, name='contact'),
    
    # Admin authentication
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('register/', views.register, name='register'),
    
    # Profile API
    path('api/profile/update/', views.update_profile, name='update_profile'),
    
    # Contact API
    path('api/contact/update/', views.update_contact, name='update_contact'),
    
    # Social Links API
    path('api/social/add/', views.add_social_link, name='add_social_link'),
    path('api/social/<int:pk>/update/', views.update_social_link, name='update_social_link'),
    path('api/social/<int:pk>/delete/', views.delete_social_link, name='delete_social_link'),
    
    # Expertise API
    path('api/expertise/add/', views.add_expertise, name='add_expertise'),
    path('api/expertise/<int:pk>/update/', views.update_expertise, name='update_expertise'),
    path('api/expertise/<int:pk>/delete/', views.delete_expertise, name='delete_expertise'),
    
    # Experience API
    path('api/experience/add/', views.add_experience, name='add_experience'),
    path('api/experience/<int:pk>/update/', views.update_experience, name='update_experience'),
    path('api/experience/<int:pk>/delete/', views.delete_experience, name='delete_experience'),
    
    # Education API
    path('api/education/add/', views.add_education, name='add_education'),
    path('api/education/<int:pk>/update/', views.update_education, name='update_education'),
    path('api/education/<int:pk>/delete/', views.delete_education, name='delete_education'),
    
    # Skills API
    path('api/skill/add/', views.add_skill, name='add_skill'),
    path('api/skill/<int:pk>/update/', views.update_skill, name='update_skill'),
    path('api/skill/<int:pk>/delete/', views.delete_skill, name='delete_skill'),
    
    # Projects API
    path('api/project/add/', views.add_project, name='add_project'),
    path('api/project/<int:pk>/update/', views.update_project, name='update_project'),
    path('api/project/<int:pk>/delete/', views.delete_project, name='delete_project'),
    
    # Appearance API
    path('api/appearance/update/', views.update_appearance, name='update_appearance'),
    path('api/theme/save/', views.save_theme, name='save_theme'),
    path('api/theme/<int:pk>/load/', views.load_theme, name='load_theme'),
    path('api/theme/<int:pk>/delete/', views.delete_theme, name='delete_theme'),
    
    # Section Reordering API
    path('api/section/update-order/', views.update_section_order, name='update_section_order'),
    path('api/section/toggle-visibility/', views.toggle_section_visibility, name='toggle_section_visibility'),
    path('api/section/<int:pk>/edit/', views.edit_section, name='edit_section'),
    
    # Custom Sections API
    path('api/section/add/', views.add_section, name='add_section'),
    path('api/section/<int:pk>/delete/', views.delete_section, name='delete_section'),
    path('api/custom-item/<int:section_id>/add/', views.add_custom_item, name='add_custom_item'),
    path('api/custom-item/<int:pk>/update/', views.update_custom_item, name='update_custom_item'),
    path('api/custom-item/<int:pk>/delete/', views.delete_custom_item, name='delete_custom_item'),
]