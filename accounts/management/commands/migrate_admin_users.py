"""
Management command to migrate existing AdminUser records to the new User model.
Run this AFTER running migrations.

Usage:
    python manage.py migrate_admin_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate existing AdminUser records to the new User model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.NOTICE('Starting AdminUser migration...'))
        
        # Import AdminUser from app.models
        try:
            from app.models import AdminUser
        except ImportError:
            self.stdout.write(self.style.WARNING('AdminUser model not found. Nothing to migrate.'))
            return
        
        admin_users = AdminUser.objects.all()
        
        if not admin_users.exists():
            self.stdout.write(self.style.WARNING('No AdminUser records found.'))
            return
        
        self.stdout.write(f'Found {admin_users.count()} AdminUser record(s) to migrate.')
        
        migrated = 0
        skipped = 0
        
        for admin_user in admin_users:
            username = admin_user.username
            
            # Check if user already exists in new User model
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(
                    f'  SKIP: User "{username}" already exists in new User model.'
                ))
                skipped += 1
                continue
            
            # Create subdomain from username (lowercase, no special chars)
            subdomain = username.lower().replace(' ', '-').replace('_', '-')
            
            # Ensure subdomain is unique
            base_subdomain = subdomain
            counter = 1
            while User.objects.filter(subdomain=subdomain).exists():
                subdomain = f'{base_subdomain}{counter}'
                counter += 1
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f'  [DRY RUN] Would migrate: {username} -> subdomain: {subdomain}, role: SUPERADMIN'
                ))
            else:
                try:
                    with transaction.atomic():
                        # Create new user as SUPERADMIN (since they were admin before)
                        new_user = User(
                            username=username,
                            subdomain=subdomain,
                            email=f'{username.lower()}@placeholder.local',  # Placeholder email
                            role=User.Role.SUPERADMIN,
                            is_staff=True,
                            is_superuser=True,
                            is_active=True,
                        )
                        
                        # Copy the password hash directly
                        new_user.password = admin_user.password_hash
                        new_user.last_login = admin_user.last_login
                        
                        new_user.save()
                        
                        self.stdout.write(self.style.SUCCESS(
                            f'  MIGRATED: {username} -> User(subdomain={subdomain}, role=SUPERADMIN)'
                        ))
                        migrated += 1
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'  ERROR migrating {username}: {str(e)}'
                    ))
        
        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.NOTICE(
                f'DRY RUN complete. Would migrate {migrated + skipped - skipped} users, skip {skipped}.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Migration complete. Migrated: {migrated}, Skipped: {skipped}'
            ))
            
            if migrated > 0:
                self.stdout.write(self.style.NOTICE(
                    '\nIMPORTANT: Migrated users have placeholder emails. '
                    'Please update them in Django admin or via API.'
                ))
