"""
Custom management command to create a superadmin user from environment variables.
Used for automatic deployment on platforms like Render.
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superadmin user from environment variables if it does not exist'

    def handle(self, *args, **options):
        # Get credentials from environment variables
        username = os.getenv('SUPERADMIN_USERNAME', 'admin')
        email = os.getenv('SUPERADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('SUPERADMIN_PASSWORD', 'admin123456')
        subdomain = os.getenv('SUPERADMIN_SUBDOMAIN', 'admin')

        # Check if superadmin already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superadmin "{username}" already exists. Skipping creation.')
            )
            return

        if User.objects.filter(subdomain=subdomain).exists():
            self.stdout.write(
                self.style.WARNING(f'Subdomain "{subdomain}" already taken. Skipping creation.')
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Email "{email}" already taken. Skipping creation.')
            )
            return

        try:
            # Create the superadmin
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                subdomain=subdomain,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superadmin: {username}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  - Email: {email}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  - Subdomain: {subdomain}')
            )
            self.stdout.write(
                self.style.WARNING(f'  - Password: (set via SUPERADMIN_PASSWORD env var)')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create superadmin: {str(e)}')
            )
