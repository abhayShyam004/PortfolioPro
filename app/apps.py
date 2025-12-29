from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        This connects the cache invalidation signals.
        """
        # Import to register signal handlers
        from . import cache  # noqa: F401
