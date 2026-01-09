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
    position = models.CharField(max_length=200, blank=True, default='')
    timeframe = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
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
    icon_url = models.URLField(blank=True, default="", help_text="External icon URL (e.g., from DevIcon)")
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
    url = models.URLField(blank=True, default='')
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
        ('modern', 'Modern Minimalist'),
        ('classic', 'Classic'),
        ('creative', 'Creative Dark'),
        ('developer', 'Developer Folio'),
        ('terminal', 'Terminal/Hacker'),
        ('terminal_x', 'Terminal X (Advanced)'),
        ('interactive_3d', 'Interactive 3D'),
        ('vcard', 'Digital Business Card'),
        ('cv_simple', 'CV / Resume Simple'),
        ('irish_spring', 'Irish Spring'),
        ('victoreke', 'Pro V2'),
        ('binil', 'TheGr8Binil'),
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
    
    # Coding Activity Section (GitHub/LeetCode stats)
    show_coding_activity = models.BooleanField(default=False, help_text="Show GitHub/LeetCode contribution graphs")
    github_username = models.CharField(max_length=100, blank=True, default="", help_text="Your GitHub username")
    leetcode_username = models.CharField(max_length=100, blank=True, default="", help_text="Your LeetCode username")
    coding_activity_order = models.IntegerField(default=50, help_text="Order position for coding activity section")
    
    # Favicon Customization (Dynamic Generation - No Storage)
    FAVICON_DESIGN_CHOICES = [
        ('circle', 'Circle'),
        ('rounded', 'Rounded Square'),
        ('square', 'Square'),
        ('gradient', 'Gradient'),
        ('outline', 'Outline'),
    ]
    favicon_initials = models.CharField(max_length=3, default="", blank=True, help_text="1-3 characters for favicon (e.g., AB)")
    favicon_design = models.CharField(max_length=20, choices=FAVICON_DESIGN_CHOICES, default='circle')
    favicon_bg_color = models.CharField(max_length=7, default="#6366f1", help_text="Favicon background color")
    favicon_text_color = models.CharField(max_length=7, default="#ffffff", help_text="Favicon text color")
    
    # Intro Animation Settings
    show_intro_animation = models.BooleanField(default=True, help_text="Show language greetings animation on page load")
    intro_greetings = models.TextField(
        default="Hello,Bonjour,Hola,Привет,مرحبا,നമസ്കാരം,こんにちは,नमस्ते",
        blank=True,
        help_text="Comma-separated list of greetings to display"
    )
    INTRO_SPEED_CHOICES = [
        ('slow', 'Slow'),
        ('medium', 'Medium'),
        ('fast', 'Fast'),
    ]
    intro_speed = models.CharField(max_length=10, choices=INTRO_SPEED_CHOICES, default='medium')
    
    # Release Notes Tracking
    last_seen_version = models.CharField(max_length=20, default="0.0.0", help_text="Last version of the app the user has seen release notes for")
    
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


class PageView(models.Model):
    """Track portfolio page views for analytics"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='page_views',
        help_text="The portfolio owner being viewed"
    )
    # Visitor identification (hashed IP for privacy)
    visitor_id = models.CharField(max_length=64, db_index=True, help_text="Hashed visitor identifier")
    
    # Page info
    path = models.CharField(max_length=500, default="/")
    section = models.CharField(max_length=100, blank=True, default="", help_text="Which section was viewed")
    
    # Visitor info
    country = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    device_type = models.CharField(max_length=20, blank=True, default="", help_text="desktop, mobile, tablet")
    browser = models.CharField(max_length=100, blank=True, default="")
    os = models.CharField(max_length=100, blank=True, default="")
    
    # Referrer
    referer = models.URLField(blank=True, default="", help_text="Where the visitor came from")
    referer_domain = models.CharField(max_length=200, blank=True, default="")
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['user', 'visitor_id']),
        ]
    
    def __str__(self):
        return f"View on {self.user.subdomain} at {self.timestamp}"
    
    @classmethod
    def create_from_request(cls, request, portfolio_user):
        """Create a PageView from a request object"""
        import hashlib
        from urllib.parse import urlparse
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        # Hash IP for privacy (with a salt based on user)
        salt = str(portfolio_user.id)
        visitor_id = hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()[:32]
        
        # Parse user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_type = 'desktop'
        browser = ''
        os_name = ''
        
        ua_lower = user_agent.lower()
        if 'mobile' in ua_lower or 'android' in ua_lower and 'mobile' in ua_lower:
            device_type = 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            device_type = 'tablet'
        
        # Simple browser detection
        if 'chrome' in ua_lower and 'edg' not in ua_lower:
            browser = 'Chrome'
        elif 'firefox' in ua_lower:
            browser = 'Firefox'
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            browser = 'Safari'
        elif 'edg' in ua_lower:
            browser = 'Edge'
        else:
            browser = 'Other'
        
        # Simple OS detection
        if 'windows' in ua_lower:
            os_name = 'Windows'
        elif 'mac' in ua_lower:
            os_name = 'macOS'
        elif 'linux' in ua_lower:
            os_name = 'Linux'
        elif 'android' in ua_lower:
            os_name = 'Android'
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            os_name = 'iOS'
        
        # Parse referer
        referer = request.META.get('HTTP_REFERER', '')
        referer_domain = ''
        if referer:
            try:
                parsed = urlparse(referer)
                referer_domain = parsed.netloc
            except:
                pass
        
        return cls.objects.create(
            user=portfolio_user,
            visitor_id=visitor_id,
            path=request.path,
            device_type=device_type,
            browser=browser,
            os=os_name,
            referer=referer[:200] if referer else '',
            referer_domain=referer_domain,
        )
