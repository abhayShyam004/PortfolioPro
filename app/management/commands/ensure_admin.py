from django.core.management.base import BaseCommand
from app.models import AdminUser
import os

class Command(BaseCommand):
    help = 'Ensures an admin user exists based on environment variables'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME')
        password = os.getenv('ADMIN_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_USERNAME or ADMIN_PASSWORD not found in environment variables. Skipping admin creation.'
            ))
            return

        user, created = AdminUser.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
        else:
            # Update password just in case env var changed
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated admin user: {username}'))

        # Security: Remove any other admin users to ensure Env Vars are the single source of truth
        deleted_count, _ = AdminUser.objects.exclude(username=username).delete()
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f'Removed {deleted_count} old admin user(s) that did not match environment variables.'))
