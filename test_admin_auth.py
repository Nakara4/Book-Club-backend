
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def regular_user():
    return User.objects.create_user(username='user', password='password', email='user@example.com')

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(username='admin', password='password', email='admin@example.com')

@pytest.mark.django_db
def test_jwt_is_staff_claim(regular_user, admin_user):
    # Test regular user
    refresh = RefreshToken.for_user(regular_user)
    access_token = refresh.access_token
    decoded_token = access_token
    assert not decoded_token.get('is_staff', False)

    # Test admin user
    refresh = RefreshToken.for_user(admin_user)
    access_token = refresh.access_token
    decoded_token = access_token
    assert decoded_token.get('is_staff', False)

@pytest.mark.django_db
def test_admin_endpoint_access_for_regular_user(api_client, regular_user):
    api_client.force_authenticate(user=regular_user)
    response = api_client.get('/api/admin/stats/')
    assert response.status_code == 403

@pytest.mark.django_db
def test_admin_endpoint_access_for_admin_user(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get('/api/admin/stats/')
    assert response.status_code == 200

