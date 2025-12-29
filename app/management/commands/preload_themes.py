"""
Management command to preload professional theme presets.
"""

from django.core.management.base import BaseCommand
from app.models import SavedTheme
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Preload professional theme presets for all users'

    THEME_PRESETS = [
        {
            'name': 'Dark Pro',
            'primary_color': '#eabe7c',
            'secondary_color': '#23967f',
            'background_color': '#0a0a0a',
            'text_color': '#ffffff',
            'heading_font': 'DM Serif Display',
            'body_font': 'Public Sans',
            'background_style': 'circles',
            'circle_color': '#eabe7c',
            'button_style': 'rounded',
        },
        {
            'name': 'Minimal Light',
            'primary_color': '#1a1a1a',
            'secondary_color': '#666666',
            'background_color': '#ffffff',
            'text_color': '#1a1a1a',
            'heading_font': 'Inter',
            'body_font': 'Inter',
            'background_style': 'none',
            'circle_color': '#e0e0e0',
            'button_style': 'square',
        },
        {
            'name': 'Ocean Blue',
            'primary_color': '#00bcd4',
            'secondary_color': '#0097a7',
            'background_color': '#0d1b2a',
            'text_color': '#e0f7fa',
            'heading_font': 'Poppins',
            'body_font': 'Roboto',
            'background_style': 'waves',
            'circle_color': '#00bcd4',
            'button_style': 'pill',
        },
        {
            'name': 'Neon Cyber',
            'primary_color': '#ff00ff',
            'secondary_color': '#00ffff',
            'background_color': '#0a0014',
            'text_color': '#ffffff',
            'heading_font': 'Montserrat',
            'body_font': 'Roboto',
            'background_style': 'grid',
            'circle_color': '#ff00ff',
            'button_style': 'rounded',
        },
        {
            'name': 'Forest Green',
            'primary_color': '#4caf50',
            'secondary_color': '#81c784',
            'background_color': '#1b2f1b',
            'text_color': '#e8f5e9',
            'heading_font': 'DM Serif Display',
            'body_font': 'Open Sans',
            'background_style': 'particles',
            'circle_color': '#4caf50',
            'button_style': 'rounded',
        },
        {
            'name': 'Sunset Orange',
            'primary_color': '#ff6f00',
            'secondary_color': '#ff8f00',
            'background_color': '#1a0a00',
            'text_color': '#fff3e0',
            'heading_font': 'Poppins',
            'body_font': 'Lato',
            'background_style': 'gradient',
            'circle_color': '#ff6f00',
            'button_style': 'pill',
        },
        {
            'name': 'Royal Purple',
            'primary_color': '#9c27b0',
            'secondary_color': '#ce93d8',
            'background_color': '#1a0a1f',
            'text_color': '#f3e5f5',
            'heading_font': 'DM Serif Display',
            'body_font': 'DM Sans',
            'background_style': 'aurora',
            'circle_color': '#9c27b0',
            'button_style': 'rounded',
        },
        {
            'name': 'Terminal Hacker',
            'primary_color': '#00ff00',
            'secondary_color': '#00cc00',
            'background_color': '#000000',
            'text_color': '#00ff00',
            'heading_font': 'Roboto',
            'body_font': 'Roboto',
            'background_style': 'matrix',
            'circle_color': '#00ff00',
            'button_style': 'square',
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to add presets for (default: all users)',
        )
        parser.add_argument(
            '--global',
            action='store_true',
            dest='global_presets',
            help='Create presets without user association (global)',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        global_presets = options.get('global_presets', False)

        if global_presets:
            self._create_presets_for_user(None)
            self.stdout.write(self.style.SUCCESS('Created global theme presets'))
        elif username:
            try:
                user = User.objects.get(username=username)
                self._create_presets_for_user(user)
                self.stdout.write(self.style.SUCCESS(f'Created presets for {username}'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {username} not found'))
        else:
            # Create for all users
            users = User.objects.all()
            for user in users:
                self._create_presets_for_user(user)
            self.stdout.write(self.style.SUCCESS(f'Created presets for {users.count()} users'))

    def _create_presets_for_user(self, user):
        for preset in self.THEME_PRESETS:
            # Check if preset already exists for this user
            exists = SavedTheme.objects.filter(
                user=user,
                name=preset['name']
            ).exists()
            
            if not exists:
                SavedTheme.objects.create(user=user, **preset)
                self.stdout.write(f"  Created: {preset['name']}")
            else:
                self.stdout.write(f"  Skipped (exists): {preset['name']}")
