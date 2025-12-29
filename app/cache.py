"""
Cache utilities for the portfolio platform.

Provides decorators and functions for caching public portfolio pages
with automatic cache invalidation when data changes.
"""

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from functools import wraps
import hashlib
import logging

logger = logging.getLogger(__name__)


# Cache keys and timeouts
PORTFOLIO_CACHE_TIMEOUT = 60 * 5  # 5 minutes
PORTFOLIO_CACHE_PREFIX = 'portfolio_'


def get_portfolio_cache_key(subdomain):
    """Generate a cache key for a user's portfolio."""
    return f"{PORTFOLIO_CACHE_PREFIX}{subdomain}"


def cache_portfolio(timeout=PORTFOLIO_CACHE_TIMEOUT):
    """
    Decorator to cache the result of a portfolio view.
    
    Usage:
        @cache_portfolio(timeout=300)
        def portfolio_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Only cache GET requests for tenant portfolios
            if request.method != 'GET':
                return view_func(request, *args, **kwargs)
            
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                return view_func(request, *args, **kwargs)
            
            # Generate cache key
            cache_key = get_portfolio_cache_key(tenant.subdomain)
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache HIT for portfolio: {tenant.subdomain}")
                return cached_response
            
            # Generate response
            logger.debug(f"Cache MISS for portfolio: {tenant.subdomain}")
            response = view_func(request, *args, **kwargs)
            
            # Cache the response (only successful ones)
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)
            
            return response
        return wrapper
    return decorator


def invalidate_portfolio_cache(user):
    """
    Invalidate cached portfolio for a specific user.
    Call this when user's portfolio data changes.
    """
    if user and hasattr(user, 'subdomain'):
        cache_key = get_portfolio_cache_key(user.subdomain)
        cache.delete(cache_key)
        logger.info(f"Cache invalidated for portfolio: {user.subdomain}")


def invalidate_all_portfolio_caches():
    """
    Invalidate all portfolio caches.
    Use sparingly - only for major changes.
    """
    # This requires a cache backend that supports pattern deletion
    # For Redis, we can use cache.delete_many() with pattern matching
    try:
        cache.clear()
        logger.info("All portfolio caches invalidated")
    except Exception as e:
        logger.error(f"Error clearing all caches: {e}")


# ============== Signal Receivers for Auto Cache Invalidation ==============

def get_user_from_instance(instance):
    """Get the user associated with a model instance."""
    if hasattr(instance, 'user'):
        return instance.user
    if hasattr(instance, 'section') and hasattr(instance.section, 'user'):
        return instance.section.user
    return None


@receiver(post_save)
def invalidate_cache_on_save(sender, instance, **kwargs):
    """Automatically invalidate cache when portfolio data is saved."""
    from .models import (
        Profile, SocialLink, Expertise, Experience, 
        Education, Skill, Project, ContactInfo, SiteSettings,
        CustomSection, CustomItem
    )
    
    cached_models = (
        Profile, SocialLink, Expertise, Experience, 
        Education, Skill, Project, ContactInfo, SiteSettings,
        CustomSection, CustomItem
    )
    
    if isinstance(instance, cached_models):
        user = get_user_from_instance(instance)
        if user:
            invalidate_portfolio_cache(user)


@receiver(post_delete)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """Automatically invalidate cache when portfolio data is deleted."""
    from .models import (
        Profile, SocialLink, Expertise, Experience, 
        Education, Skill, Project, ContactInfo, SiteSettings,
        CustomSection, CustomItem
    )
    
    cached_models = (
        Profile, SocialLink, Expertise, Experience, 
        Education, Skill, Project, ContactInfo, SiteSettings,
        CustomSection, CustomItem
    )
    
    if isinstance(instance, cached_models):
        user = get_user_from_instance(instance)
        if user:
            invalidate_portfolio_cache(user)


# ============== Query Optimization Helpers ==============

def get_portfolio_data_optimized(user):
    """
    Get all portfolio data for a user with optimized queries.
    Uses select_related and prefetch_related to minimize database hits.
    """
    from .models import (
        Profile, SocialLink, Expertise, Experience, 
        Education, Skill, Project, ContactInfo, SiteSettings,
        CustomSection
    )
    
    return {
        'profile': Profile.objects.filter(user=user).first(),
        'social_links': list(SocialLink.objects.filter(user=user).order_by('order')),
        'expertise_list': list(Expertise.objects.filter(user=user).order_by('order')),
        'experiences': list(Experience.objects.filter(user=user).order_by('order')),
        'education_list': list(Education.objects.filter(user=user).order_by('order')),
        'skills': list(Skill.objects.filter(user=user).order_by('order')),
        'projects': list(Project.objects.filter(user=user).order_by('order')),
        'contact': ContactInfo.objects.filter(user=user).first(),
        'settings': SiteSettings.objects.filter(user=user).first(),
        'custom_sections': list(
            CustomSection.objects.filter(user=user, is_system=False, is_visible=True)
            .order_by('order')
            .prefetch_related('items')
        ),
    }
