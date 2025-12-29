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
        # Get credentials from environment variables with defaults
        username = os.getenv('SUPERADMIN_USERNAME', 'Superadmin@portfoliopro')
        password = os.getenv('SUPERADMIN_PASSWORD', 'ab2112045@gmail.com')
        subdomain = os.getenv('SUPERADMIN_SUBDOMAIN', 'superadmin')
        email = os.getenv('SUPERADMIN_EMAIL', '')  # Email is optional

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

        try:
            # Create the superadmin
            user = User.objects.create_superuser(
                username=username,
                email=email if email else None,
                password=password,
                subdomain=subdomain,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superadmin: {username}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'  - Subdomain: {subdomain}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create superadmin: {str(e)}')
            )
