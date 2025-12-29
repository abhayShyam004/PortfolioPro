from django.core.management.base import BaseCommand
from app.models import CustomSection

class Command(BaseCommand):
    help = 'Populates the standard 8 system sections for drag and drop ordering.'

    def handle(self, *args, **options):
        system_sections = [
            {'title': 'Profile', 'slug': 'profile', 'icon': 'fas fa-user-circle', 'order': 1},
            {'title': 'Appearance', 'slug': 'appearance', 'icon': 'fas fa-palette', 'order': 2},
            {'title': 'Projects', 'slug': 'projects', 'icon': 'fas fa-layer-group', 'order': 3},
            {'title': 'Skills', 'slug': 'skills', 'icon': 'fas fa-shapes', 'order': 4},
            {'title': 'Experience', 'slug': 'experience', 'icon': 'fas fa-briefcase', 'order': 5},
            {'title': 'Education', 'slug': 'education', 'icon': 'fas fa-graduation-cap', 'order': 6},
            {'title': 'Contact & Social', 'slug': 'social', 'icon': 'fas fa-share-nodes', 'order': 7},
            {'title': 'Expertise', 'slug': 'expertise', 'icon': 'fas fa-code', 'order': 8},
        ]

        created_count = 0
        updated_count = 0

        for section_data in system_sections:
            section, created = CustomSection.objects.get_or_create(
                slug=section_data['slug'],
                defaults={
                    'title': section_data['title'],
                    'icon': section_data['icon'],
                    'order': section_data['order'],
                    'is_system': True,
                    'is_visible': True
                }
            )

            if not created:
                # Ensure existing records are marked as system
                if not section.is_system:
                    section.is_system = True
                    section.save()
                    updated_count += 1
            else:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully populated system sections. Created: {created_count}, Updated: {updated_count}.'))
