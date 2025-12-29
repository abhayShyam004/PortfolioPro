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
        
        # Create a test user "abhay" for demonstration (SQLite testing)
        test_username = os.getenv('TEST_USER_USERNAME', 'abhay')
        test_password = os.getenv('TEST_USER_PASSWORD', 'testpassword123')
        test_subdomain = os.getenv('TEST_USER_SUBDOMAIN', 'abhay')
        
        if not User.objects.filter(subdomain=test_subdomain).exists():
            try:
                from app.models import Profile, ContactInfo, SiteSettings, CustomSection, SavedTheme, SocialLink
                
                test_user = User.objects.create_user(
                    username=test_username,
                    email='',
                    password=test_password,
                    subdomain=test_subdomain,
                    role='USER'
                )
                
                # Create initial profile and settings
                Profile.objects.create(
                    user=test_user, 
                    name='Abhay',
                    greeting='Hi, I am Abhay',
                    hero_bio='A passionate developer'
                )
                ContactInfo.objects.create(user=test_user, email='test@example.com')
                SiteSettings.objects.create(user=test_user)
                
                # Create default system sections
                default_sections = [
                    {'title': 'Profile', 'slug': 'profile', 'order': 1, 'icon': 'fas fa-user'},
                    {'title': 'About', 'slug': 'about', 'order': 2, 'icon': 'fas fa-info-circle'},
                    {'title': 'Education', 'slug': 'education', 'order': 3, 'icon': 'fas fa-graduation-cap'},
                    {'title': 'Appearance', 'slug': 'appearance', 'order': 4, 'icon': 'fas fa-palette'},
                    {'title': 'Expertise', 'slug': 'expertise', 'order': 5, 'icon': 'fas fa-star'},
                    {'title': 'Experience', 'slug': 'experience', 'order': 6, 'icon': 'fas fa-briefcase'},
                    {'title': 'Skills', 'slug': 'skills', 'order': 7, 'icon': 'fas fa-code'},
                    {'title': 'Projects', 'slug': 'projects', 'order': 8, 'icon': 'fas fa-folder-open'},
                    {'title': 'Contact & Social', 'slug': 'social', 'order': 9, 'icon': 'fas fa-envelope'},
                ]
                for section_data in default_sections:
                    CustomSection.objects.create(
                        user=test_user,
                        title=section_data['title'],
                        slug=section_data['slug'],
                        order=section_data['order'],
                        icon=section_data['icon'],
                        is_system=True,
                        is_visible=True
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created test user: {test_username} (subdomain: {test_subdomain})')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create test user: {str(e)}')
                )
