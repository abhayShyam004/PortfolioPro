from django.db import migrations


def assign_data_to_superadmin(apps, schema_editor):
    """
    Assign all existing portfolio data to the first superadmin user.
    This ensures data continuity after adding user FK to all models.
    """
    User = apps.get_model('accounts', 'User')
    
    # Get the first superadmin user (should be 'Abhay')
    try:
        superadmin = User.objects.filter(role='SUPERADMIN').first()
        if not superadmin:
            superadmin = User.objects.first()
        
        if not superadmin:
            print("No users found. Skipping data assignment.")
            return
    except Exception as e:
        print(f"Error getting user: {e}")
        return
    
    # Get all models that need user assignment
    Profile = apps.get_model('app', 'Profile')
    SocialLink = apps.get_model('app', 'SocialLink')
    Expertise = apps.get_model('app', 'Expertise')
    Experience = apps.get_model('app', 'Experience')
    Education = apps.get_model('app', 'Education')
    Skill = apps.get_model('app', 'Skill')
    Project = apps.get_model('app', 'Project')
    ContactInfo = apps.get_model('app', 'ContactInfo')
    SiteSettings = apps.get_model('app', 'SiteSettings')
    SavedTheme = apps.get_model('app', 'SavedTheme')
    CustomSection = apps.get_model('app', 'CustomSection')
    
    # Assign all existing data to superadmin
    models_to_update = [
        (Profile, 'Profile'),
        (SocialLink, 'SocialLink'),
        (Expertise, 'Expertise'),
        (Experience, 'Experience'),
        (Education, 'Education'),
        (Skill, 'Skill'),
        (Project, 'Project'),
        (ContactInfo, 'ContactInfo'),
        (SiteSettings, 'SiteSettings'),
        (SavedTheme, 'SavedTheme'),
        (CustomSection, 'CustomSection'),
    ]
    
    for model, name in models_to_update:
        count = model.objects.filter(user__isnull=True).update(user=superadmin)
        if count > 0:
            print(f"  Assigned {count} {name} record(s) to user '{superadmin.username}'")


def reverse_assignment(apps, schema_editor):
    """
    Reverse the data assignment (set user to null).
    """
    Profile = apps.get_model('app', 'Profile')
    SocialLink = apps.get_model('app', 'SocialLink')
    Expertise = apps.get_model('app', 'Expertise')
    Experience = apps.get_model('app', 'Experience')
    Education = apps.get_model('app', 'Education')
    Skill = apps.get_model('app', 'Skill')
    Project = apps.get_model('app', 'Project')
    ContactInfo = apps.get_model('app', 'ContactInfo')
    SiteSettings = apps.get_model('app', 'SiteSettings')
    SavedTheme = apps.get_model('app', 'SavedTheme')
    CustomSection = apps.get_model('app', 'CustomSection')
    
    for model in [Profile, SocialLink, Expertise, Experience, Education, 
                  Skill, Project, ContactInfo, SiteSettings, SavedTheme, CustomSection]:
        model.objects.all().update(user=None)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_add_user_to_all_models'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(assign_data_to_superadmin, reverse_assignment),
    ]
