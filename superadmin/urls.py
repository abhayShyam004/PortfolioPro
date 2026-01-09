from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/ban/', views.ban_user, name='ban_user'),
    path('users/<int:user_id>/unban/', views.unban_user, name='unban_user'),
    path('users/<int:user_id>/reset-password/', views.reset_user_password, name='reset_user_password'),
    path('users/<int:user_id>/impersonate/', views.impersonate_user, name='impersonate_user'),
    path('users/<int:user_id>/change-role/', views.change_user_role, name='change_user_role'),
    
    # Impersonation
    path('end-impersonation/', views.end_impersonation, name='end_impersonation'),
    
    # API endpoints
    path('api/stats/', views.api_user_stats, name='api_stats'),
    path('api/recent-users/', views.api_recent_users, name='api_recent_users'),
    
    # Release Notes
    path('release-notes/', views.release_note_list, name='release_note_list'),
    path('release-notes/<int:note_id>/deploy/', views.deploy_release_note, name='deploy_release_note'),
    path('release-notes/<int:note_id>/delete/', views.delete_release_note, name='delete_release_note'),
    path('broadcast-email/', views.broadcast_email, name='broadcast_email'),
]
