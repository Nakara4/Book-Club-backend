"""
Tests for custom exception handler and pagination
"""
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.views import APIView
from myapp.exceptions import custom_exception_handler
from myapp.models import BookClub
import json


class CustomExceptionHandlerTest(TestCase):
    """Test custom exception handler formatting"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
    def test_validation_error_formatting(self):
        """Test that validation errors are formatted correctly"""
        exc = ValidationError({'username': ['This field is required.']})
        request = self.factory.get('/')
        
        response = custom_exception_handler(exc, {'request': request})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)
        
    def test_not_found_error_formatting(self):
        """Test that NotFound errors are formatted correctly"""
        exc = NotFound('Object not found')
        request = self.factory.get('/')
        
        response = custom_exception_handler(exc, {'request': request})
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['detail'], 'Object not found')
        
    def test_permission_denied_formatting(self):
        """Test that PermissionDenied errors are formatted correctly"""
        exc = PermissionDenied('You do not have permission')
        request = self.factory.get('/')
        
        response = custom_exception_handler(exc, {'request': request})
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'You do not have permission')


class PaginationAPITest(APITestCase):
    """Test pagination in API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test book clubs
        for i in range(15):
            BookClub.objects.create(
                name=f'Test Club {i}',
                description=f'Description for club {i}',
                creator=self.user,
                is_private=False,
                max_members=20
            )
    
    def test_pagination_format(self):
        """Test that pagination returns the expected format"""
        response = self.client.get('/api/bookclubs/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check pagination structure
        self.assertIn('results', data)
        self.assertIn('pagination', data)
        
        pagination = data['pagination']
        self.assertIn('count', pagination)
        self.assertIn('page', pagination)
        self.assertIn('pages', pagination)
        self.assertIn('page_size', pagination)
        self.assertIn('has_next', pagination)
        self.assertIn('has_previous', pagination)
        
    def test_pagination_page_size(self):
        """Test that pagination uses the correct page size"""
        response = self.client.get('/api/bookclubs/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 12 results per page (our custom page size)
        self.assertEqual(len(data['results']), 12)
        self.assertEqual(data['pagination']['page_size'], 12)
        self.assertTrue(data['pagination']['has_next'])
        
    def test_custom_page_size_parameter(self):
        """Test that custom page_size parameter works"""
        response = self.client.get('/api/bookclubs/?page_size=5')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 5 results per page
        self.assertEqual(len(data['results']), 5)
        self.assertEqual(data['pagination']['page_size'], 5)


class AuthenticationErrorTest(APITestCase):
    """Test that authentication errors use proper format"""
    
    def test_login_with_invalid_credentials(self):
        """Test login error format"""
        response = self.client.post('/auth/login/', {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('detail', data)
        self.assertEqual(data['detail'], 'User with this email does not exist')
    
    def test_registration_validation_error(self):
        """Test registration validation error format"""
        response = self.client.post('/auth/register/', {
            'username': '',  # Empty username should cause validation error
            'email': 'invalid-email',
            'password': '123'
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        # Should have either 'detail' for single error or 'detail' + 'errors' for multiple
        self.assertTrue('detail' in data or 'errors' in data)
