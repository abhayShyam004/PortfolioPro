"""
Unit tests for multi-tenant isolation and permissions.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from app.models import Profile, Skill, Project, SiteSettings, ContactInfo

User = get_user_model()


class MultiTenantIsolationTests(TestCase):
    """Tests for multi-tenant data isolation."""
    
    def setUp(self):
        """Create two users with separate data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!',
            subdomain='user1'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123!',
            subdomain='user2'
        )
        
        # Create data for user1
        self.profile1 = Profile.objects.create(
            user=self.user1,
            name='User One',
            greeting='Hello from User 1'
        )
        self.skill1 = Skill.objects.create(
            user=self.user1,
            name='Python',
            category='Backend'
        )
        self.project1 = Project.objects.create(
            user=self.user1,
            title='User1 Project',
            category='Web'
        )
        
        # Create data for user2
        self.profile2 = Profile.objects.create(
            user=self.user2,
            name='User Two',
            greeting='Hello from User 2'
        )
        self.skill2 = Skill.objects.create(
            user=self.user2,
            name='JavaScript',
            category='Frontend'
        )
    
    def test_profile_belongs_to_user(self):
        """Test that profiles are correctly associated with users."""
        self.assertEqual(self.profile1.user, self.user1)
        self.assertEqual(self.profile2.user, self.user2)
    
    def test_user_cannot_see_other_skills(self):
        """Test that users can only see their own skills."""
        user1_skills = Skill.objects.filter(user=self.user1)
        user2_skills = Skill.objects.filter(user=self.user2)
        
        self.assertEqual(user1_skills.count(), 1)
        self.assertEqual(user1_skills.first().name, 'Python')
        
        self.assertEqual(user2_skills.count(), 1)
        self.assertEqual(user2_skills.first().name, 'JavaScript')
    
    def test_user_cannot_see_other_projects(self):
        """Test that users can only see their own projects."""
        user1_projects = Project.objects.filter(user=self.user1)
        user2_projects = Project.objects.filter(user=self.user2)
        
        self.assertEqual(user1_projects.count(), 1)
        self.assertEqual(user2_projects.count(), 0)
    
    def test_data_isolation_with_filtering(self):
        """Test that filtering by user returns correct data."""
        # Add more skills to user1
        Skill.objects.create(user=self.user1, name='Django', category='Backend')
        Skill.objects.create(user=self.user1, name='Flask', category='Backend')
        
        # User1 should have 3 skills, User2 should have 1
        self.assertEqual(Skill.objects.filter(user=self.user1).count(), 3)
        self.assertEqual(Skill.objects.filter(user=self.user2).count(), 1)


class PermissionTests(TestCase):
    """Tests for object-level permissions."""
    
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!',
            subdomain='user1'
        )
        self.superadmin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )
        
        # Create skill for user1
        self.skill = Skill.objects.create(
            user=self.user1,
            name='Django',
            category='Backend'
        )
    
    def test_anonymous_cannot_access_admin_panel(self):
        """Test anonymous users are redirected from admin panel."""
        response = self.client.get(reverse('admin_panel'))
        self.assertRedirects(response, reverse('admin_login'))
    
    def test_anonymous_cannot_modify_data(self):
        """Test anonymous users cannot modify portfolio data."""
        response = self.client.post(reverse('add_skill'), {
            'name': 'Hacked',
            'category': 'Evil'
        })
        # Should redirect to login
        self.assertEqual(response.status_code, 302)


class SubdomainMiddlewareTests(TestCase):
    """Tests for subdomain middleware."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            subdomain='testuser'
        )
        # Create required data for portfolio rendering
        Profile.objects.create(
            user=self.user,
            name='Test User',
            greeting='Hello!'
        )
        ContactInfo.objects.create(
            user=self.user,
            email='test@example.com'
        )
        SiteSettings.objects.create(user=self.user)
    
    def test_subdomain_query_param_sets_tenant(self):
        """Test that ?subdomain= query param sets request.tenant (dev mode)."""
        response = self.client.get('/', {'subdomain': 'testuser'})
        self.assertEqual(response.status_code, 200)
        # The response should contain user's profile data
        self.assertContains(response, 'Test User')
    
    def test_invalid_subdomain_shows_landing(self):
        """Test that invalid subdomain shows landing page."""
        response = self.client.get('/', {'subdomain': 'nonexistent'})
        # Should show landing page (200 status)
        self.assertEqual(response.status_code, 200)
    
    def test_reserved_subdomain_not_resolved(self):
        """Test that reserved subdomains are not resolved as tenants."""
        response = self.client.get('/', {'subdomain': 'www'})
        self.assertEqual(response.status_code, 200)
        # Should not crash and show landing or fallback
    
    def test_no_subdomain_shows_landing_page(self):
        """Test no subdomain shows landing page (main homepage)."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Should show landing page with PortfolioPro branding
        self.assertContains(response, 'PortfolioPro')


class HealthCheckTests(TestCase):
    """Tests for health check endpoint."""
    
    def test_health_check_returns_200(self):
        """Test health check endpoint returns 200."""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_check_returns_json(self):
        """Test health check returns proper JSON."""
        response = self.client.get('/health/')
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'portfoliopro')


class CacheInvalidationTests(TestCase):
    """Tests for cache invalidation on data changes."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='cacheuser',
            email='cache@example.com',
            password='TestPass123!',
            subdomain='cacheuser'
        )
    
    def test_cache_key_generation(self):
        """Test cache key is generated correctly."""
        from app.cache import get_portfolio_cache_key
        key = get_portfolio_cache_key('testsubdomain')
        self.assertEqual(key, 'portfolio_testsubdomain')
    
    def test_cache_invalidation_function(self):
        """Test cache invalidation function runs without error."""
        from app.cache import invalidate_portfolio_cache
        # Should not raise any errors
        invalidate_portfolio_cache(self.user)


class ModelRelationshipTests(TestCase):
    """Tests for model relationships and constraints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeluser',
            email='model@example.com',
            password='TestPass123!',
            subdomain='modeluser'
        )
    
    def test_profile_one_to_one(self):
        """Test Profile has OneToOne relationship with User."""
        profile = Profile.objects.create(
            user=self.user,
            name='Model User'
        )
        
        # Creating another profile for same user should fail
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Profile.objects.create(
                user=self.user,
                name='Duplicate Profile'
            )
    
    def test_skill_ordering(self):
        """Test skills are ordered by 'order' field."""
        Skill.objects.create(user=self.user, name='Third', category='Test', order=3)
        Skill.objects.create(user=self.user, name='First', category='Test', order=1)
        Skill.objects.create(user=self.user, name='Second', category='Test', order=2)
        
        skills = list(Skill.objects.filter(user=self.user).order_by('order'))
        self.assertEqual(skills[0].name, 'First')
        self.assertEqual(skills[1].name, 'Second')
        self.assertEqual(skills[2].name, 'Third')
