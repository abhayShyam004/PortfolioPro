"""
Management command to load initial data from backup file.
Used when migrating from SQLite to PostgreSQL on Render.
"""

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Load data from backup JSON file if database is empty'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Only load data if no users exist (fresh database)
        if User.objects.count() == 0:
            backup_file = 'data_backup.json'
            
            if os.path.exists(backup_file):
                self.stdout.write(self.style.WARNING(f'Loading data from {backup_file}...'))
                try:
                    call_command('loaddata', backup_file, verbosity=1)
                    self.stdout.write(self.style.SUCCESS('Data loaded successfully!'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to load data: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'Backup file {backup_file} not found. Skipping data load.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Database already has {User.objects.count()} users. Skipping data load.'))
