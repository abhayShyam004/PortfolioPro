"""
Subdomain Middleware for Multi-Tenant Portfolio Platform.

This middleware extracts the subdomain from incoming requests and resolves
it to a User, enabling multi-tenant portfolio routing.

Examples:
    abhay.portfoliopro.site -> request.tenant = User(subdomain='abhay')
    john.portfoliopro.site -> request.tenant = User(subdomain='john')
    www.portfoliopro.site -> Landing page (no tenant)
    portfoliopro.site -> Landing page (no tenant)
    localhost:8000/?subdomain=abhay -> Dev mode tenant resolution
"""

import re
import logging
from django.http import Http404
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class SubdomainMiddleware:
    """
    Middleware to extract subdomain from request and attach tenant user.
    
    Attributes added to request:
        request.subdomain: str or None - The extracted subdomain
        request.tenant: User or None - The resolved user for this subdomain
        request.is_tenant_request: bool - Whether this is a tenant-specific request
    """
    
    # Subdomains that should not be treated as user portfolios
    RESERVED_SUBDOMAINS = frozenset({
        'www', 'api', 'admin', 'static', 'media', 'app', 
        'mail', 'ftp', 'blog', 'help', 'support', 'status',
        'docs', 'developer', 'dev', 'staging', 'test', 'demo',
        'login', 'register', 'signup', 'auth', 'dashboard',
        'superadmin', 'panel', 'console'
    })
    
    # Cache timeout for tenant lookup (5 minutes)
    CACHE_TIMEOUT = 300
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Get main domain from settings, default to localhost for dev
        self.main_domain = getattr(settings, 'MAIN_DOMAIN', 'portfoliopro.site')
    
    def __call__(self, request):
        # Initialize request attributes
        request.subdomain = None
        request.tenant = None
        request.is_tenant_request = False
        
        # Extract and resolve subdomain
        subdomain = self._extract_subdomain(request)
        
        if subdomain and subdomain not in self.RESERVED_SUBDOMAINS:
            request.subdomain = subdomain
            request.tenant = self._get_tenant_by_subdomain(subdomain)
            request.is_tenant_request = request.tenant is not None
            
            if request.tenant:
                logger.debug(f"Tenant resolved: {subdomain} -> {request.tenant.username}")
            else:
                logger.debug(f"No tenant found for subdomain: {subdomain}")
        
        response = self.get_response(request)
        return response
    
    def _extract_subdomain(self, request):
        """
        Extract subdomain from the request host.
        
        Handles:
        - Production: abhay.portfoliopro.site -> 'abhay'
        - Development: localhost:8000/?subdomain=abhay -> 'abhay'
        - Fallback: anyhost.com/?subdomain=abhay -> 'abhay' (for hosts without wildcard DNS)
        """
        host = request.get_host().lower()
        
        # Remove port if present
        host_without_port = host.split(':')[0]
        
        # Development mode: check query parameter first
        if self._is_local_host(host_without_port):
            subdomain = request.GET.get('subdomain', '').lower().strip()
            if subdomain:
                return subdomain
            return None
        
        # Production mode: try to extract from subdomain first
        subdomain = self._extract_subdomain_from_host(host_without_port)
        if subdomain:
            return subdomain
        
        # Fallback: check query parameter for hosts without wildcard DNS support
        # (e.g., Render free tier: portfoliopro-8rxk.onrender.com/?subdomain=abhay)
        subdomain = request.GET.get('subdomain', '').lower().strip()
        if subdomain:
            return subdomain
        
        return None
    
    def _is_local_host(self, host):
        """Check if host is localhost or local IP."""
        local_hosts = {'localhost', '127.0.0.1', '0.0.0.0', 'testserver'}
        return host in local_hosts or host.startswith('192.168.') or host.startswith('10.')
    
    def _extract_subdomain_from_host(self, host):
        """
        Extract subdomain from a production hostname.
        
        Examples:
            abhay.portfoliopro.site -> 'abhay'
            www.portfoliopro.site -> 'www' (filtered later as reserved)
            portfoliopro.site -> None
        """
        # Escape dots in main domain for regex
        escaped_domain = re.escape(self.main_domain)
        
        # Pattern: subdomain.domain.tld
        pattern = rf'^([a-z0-9][a-z0-9-]*[a-z0-9]|[a-z0-9])\.{escaped_domain}$'
        match = re.match(pattern, host)
        
        if match:
            return match.group(1)
        
        return None
    
    def _get_tenant_by_subdomain(self, subdomain):
        """
        Get user by subdomain.
        
        Returns None if:
        - Subdomain not found
        - User is inactive
        - User is banned
        
        Note: Caching disabled temporarily to fix Render deployment issues.
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            user = User.objects.filter(
                subdomain__iexact=subdomain,
                is_active=True,
                is_banned=False
            ).first()
            
            if user:
                logger.info(f"Tenant found for subdomain '{subdomain}': {user.username}")
                return user
            else:
                logger.warning(f"No active/unbanned user found for subdomain '{subdomain}'")
                return None
                
        except Exception as e:
            logger.error(f"Error resolving tenant for subdomain '{subdomain}': {e}")
            return None
    
    @staticmethod
    def invalidate_tenant_cache(subdomain):
        """
        Invalidate cached tenant data. Call this when user data changes.
        
        Usage:
            SubdomainMiddleware.invalidate_tenant_cache('abhay')
        """
        cache_key = f'tenant_{subdomain}'
        cache.delete(cache_key)


class TenantNotFoundMiddleware:
    """
    Optional middleware to return 404 for unknown tenant subdomains.
    Use this if you want strict tenant enforcement.
    
    Add AFTER SubdomainMiddleware in settings.MIDDLEWARE.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # If subdomain was detected but no tenant was found, return 404
        if request.subdomain and not request.tenant:
            # Only enforce on non-API paths
            if not request.path.startswith('/api/'):
                raise Http404(f"Portfolio not found: {request.subdomain}")
        
        return self.get_response(request)
