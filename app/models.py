from django.db import models
from django.conf import settings


class Profile(models.Model):
    """Main profile information - One per user"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio_profile',
        null=True,  # Temporarily nullable for migration
        blank=True
    )
    name = models.CharField(max_length=100, default="Your Name")
    greeting = models.CharField(max_length=200, default="Hi, I am")
    hero_bio = models.TextField(default="A web designer & backend developer based in India.")
    about_text = models.TextField(default="")
    about_photo = models.ImageField(upload_to='profile/', blank=True, null=True)
    cv_link = models.URLField(blank=True, default="")
    ai_assistant_script = models.TextField(blank=True, default="", help_text="Paste the full JS script from your AI provider here")

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"{self.name} ({self.user.subdomain if self.user else 'No User'})"


class SocialLink(models.Model):
    """Social media links - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='social_links',
        null=True,
        blank=True
    )
    PLATFORM_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('leetcode', 'LeetCode'),
        ('github', 'GitHub'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter/X'),
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
        ('dribbble', 'Dribbble'),
        ('behance', 'Behance'),
        ('medium', 'Medium'),
        ('devto', 'Dev.to'),
        ('stackoverflow', 'Stack Overflow'),
        ('other', 'Other'),
    ]
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    display_name = models.CharField(max_length=50, default="")
    url = models.URLField(blank=True, default="")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"{self.get_platform_display()} - {self.url}"


class Expertise(models.Model):
    """Expertise/skills list shown in About section - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expertise_list',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Expertise"
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return self.name


class Experience(models.Model):
    """Work experience entries - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='experiences',
        null=True,
        blank=True
    )
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    timeframe = models.CharField(max_length=100)
    description = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"{self.position} at {self.company}"


class Education(models.Model):
    """Education entries - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='education_list',
        null=True,
        blank=True
    )
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    timeframe = models.CharField(max_length=100)
    description = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Education"
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class Skill(models.Model):
    """Skills shown in Skills section with icons - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skills',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='skills/', blank=True, null=True)
    description = models.TextField(blank=True, default="")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return self.name


class Project(models.Model):
    """Portfolio projects - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    url = models.URLField()
    description = models.TextField(blank=True, default="")
    icon = models.ImageField(upload_to='projects/', blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    """Contact information - One per user"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contact_info',
        null=True,
        blank=True
    )
    email = models.EmailField(default="")
    phone = models.CharField(max_length=20, default="")
    contact_heading = models.TextField(default="I love to hear from you. Whether you have a question or just want to chat about design, tech & art — shoot me a message.")

    class Meta:
        verbose_name = "Contact Info"
        verbose_name_plural = "Contact Info"
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return self.email


class SiteSettings(models.Model):
    """Site appearance settings - One per user"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='site_settings',
        null=True,
        blank=True
    )
    # Color Scheme
    primary_color = models.CharField(max_length=7, default="#eabe7c")
    secondary_color = models.CharField(max_length=7, default="#23967f")
    background_color = models.CharField(max_length=7, default="#0a0a0a")
    hero_about_text_color = models.CharField(max_length=7, default="#ffffff", help_text="Color for hero bio and about description")
    general_text_color = models.CharField(max_length=7, default="#a0a0a0", help_text="Color for headings, greeting, section titles")
    
    # Typography
    name_font_size = models.FloatField(default=11.0)
    greeting_font_size = models.FloatField(default=2.0)
    name_font_size_mobile = models.FloatField(default=4.0)
    greeting_font_size_mobile = models.FloatField(default=1.5)
    FONT_CHOICES = [
        ('DM Serif Display', 'DM Serif Display'),
        ('Public Sans', 'Public Sans'),
        ('DM Sans', 'DM Sans'),
        ('Inter', 'Inter'),
        ('Poppins', 'Poppins'),
        ('Roboto', 'Roboto'),
        ('Montserrat', 'Montserrat'),
        ('Open Sans', 'Open Sans'),
        ('Lato', 'Lato'),
    ]
    heading_font = models.CharField(max_length=50, choices=FONT_CHOICES, default="DM Serif Display")
    body_font = models.CharField(max_length=50, choices=FONT_CHOICES, default="Public Sans")
    
    # Section Headings (About, Skills, etc.)
    section_heading_color = models.CharField(max_length=7, default="#ffffff", help_text="Color for section titles (About, Skills, etc.)")
    section_heading_font_size = models.FloatField(default=1.6, help_text="Font size in rem for section headings")
    section_heading_font_size_mobile = models.FloatField(default=1.4, help_text="Font size in rem for section headings on mobile")
    
    # Section Visibility
    show_intro_section = models.BooleanField(default=True)
    show_about_section = models.BooleanField(default=True)
    show_skills_section = models.BooleanField(default=True)
    show_works_section = models.BooleanField(default=True)
    show_contact_section = models.BooleanField(default=True)
    
    # Background Effects
    STYLE_CHOICES = [
        ('none', 'No Effect'),
        ('circles', 'Moving Circles'),
        ('particles', 'Tech Particles'),
        ('gradient', 'Gradient Mesh'),
        ('grid', 'Retro Grid'),
        ('waves', 'Digital Waves'),
        ('matrix', 'Matrix Rain'),
        ('starfield', 'Starfield Warp'),
        ('aurora', 'Aurora Borealis'),
        ('hexagons', 'Neon Hexagons'),
    ]
    background_style = models.CharField(max_length=20, choices=STYLE_CHOICES, default="circles")
    circle_color = models.CharField(max_length=7, default="#6366f1")
    
    # Theme System
    THEME_CHOICES = [
        ('classic', 'Classic'),
        ('interactive_3d', 'Interactive 3D'),
        ('developer_folio', 'Developer Folio'),
        ('irish_spring', 'Irish Spring'),
        ('neural_odyssey', 'Neural Odyssey'),
        ('chrono_story', 'Chrono Story'),
        ('glass_horizon', 'Glass Horizon'),
        ('cinematic_flow', 'Cinematic Flow'),
    ]
    active_theme = models.CharField(max_length=30, choices=THEME_CHOICES, default='classic')
    theme_config = models.JSONField(default=dict, blank=True, help_text="Theme-specific configuration")
    
    # Button Style
    BUTTON_STYLE_CHOICES = [
        ('rounded', 'Rounded'),
        ('pill', 'Pill'),
        ('square', 'Square'),
    ]
    button_style = models.CharField(max_length=20, choices=BUTTON_STYLE_CHOICES, default="rounded")
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f"Settings for {self.user.subdomain if self.user else 'No User'}"


class SavedTheme(models.Model):
    """Saved custom themes - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_themes',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    
    # Store all theme settings
    primary_color = models.CharField(max_length=7, default="#6366f1")
    secondary_color = models.CharField(max_length=7, default="#a5b4fc")
    background_color = models.CharField(max_length=7, default="#0a0a0a")
    text_color = models.CharField(max_length=7, default="#ffffff")
    heading_font = models.CharField(max_length=50, default="DM Sans")
    body_font = models.CharField(max_length=50, default="DM Sans")
    background_style = models.CharField(max_length=20, default="circles")
    circle_color = models.CharField(max_length=7, default="#6366f1")
    button_style = models.CharField(max_length=20, default="rounded")
    
    # Font sizes
    name_font_size = models.FloatField(default=4.5)
    greeting_font_size = models.FloatField(default=1.3)
    section_heading_font_size = models.FloatField(default=1.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return self.name


class ThemePreset(models.Model):
    """Global theme presets available to all users"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    preview_image = models.CharField(max_length=200, blank=True, help_text="Path to preview image in static/")
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Whether this theme is available for selection")
    
    # Theme-specific defaults
    default_config = models.JSONField(default=dict, blank=True)
    
    # Required CSS/JS files (paths relative to static/)
    css_file = models.CharField(max_length=100, blank=True, help_text="e.g., css/themes/terminal-x.css")
    js_file = models.CharField(max_length=100, blank=True, help_text="e.g., js/themes/terminal-x.js")
    
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name


# NOTE: AdminUser is deprecated - kept for backward compatibility during migration
# Will be removed in a future cleanup
class AdminUser(models.Model):
    """DEPRECATED: Custom Admin User - replaced by accounts.User"""
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)
    
    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw_password)
        
    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = "Admin User (Deprecated)"


class CustomSection(models.Model):
    """Dynamic sections created by the user (e.g. Awards, Certifications) - Scoped to user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_sections',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)  # Removed unique=True, will be unique per user
    icon = models.CharField(max_length=50, default="fas fa-layer-group")
    order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    
    # Customization options for non-system sections
    show_image = models.BooleanField(default=True, help_text="Show image/icon in card")
    show_link_button = models.BooleanField(default=True, help_text="Show clickable link button")
    button_text = models.CharField(max_length=50, default="View Details", help_text="Text for the link button")
    
    CARD_LAYOUT_CHOICES = [
        ('grid', 'Grid (Cards)'),
        ('list', 'List View'),
        ('timeline', 'Timeline'),
    ]
    card_layout = models.CharField(max_length=20, choices=CARD_LAYOUT_CHOICES, default='grid')

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['user'])]
        # Unique together: slug must be unique per user
        unique_together = [['user', 'slug']]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Check uniqueness within user's sections
            while CustomSection.objects.filter(user=self.user, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CustomItem(models.Model):
    """Items within a custom section"""
    section = models.ForeignKey(CustomSection, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, default="")
    link = models.URLField(blank=True, default="")
    icon = models.ImageField(upload_to='custom_items/', blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
