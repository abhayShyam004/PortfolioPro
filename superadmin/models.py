from django.db import models
from django.utils import timezone

class ReleaseNote(models.Model):
    """
    System-wide release notes managed by superadmins.
    When published, these are shown to all users on their admin panel.
    """
    version = models.CharField(max_length=20, help_text="e.g. 2.1.0")
    content = models.TextField(help_text="HTML content for the release notes modal")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"v{self.version} ({'Published' if self.is_published else 'Draft'})"
