#!/usr/bin/env python3
"""
Test script to validate backend-frontend authentication sync
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_cors_preflight():
    """Test CORS preflight request"""
    print("🔍 Testing CORS preflight...")
    
    headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type,Authorization'
    }
    
    response = requests.options(f"{BASE_URL}/auth/login/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"CORS Headers: {dict(response.headers)}")
    print()

def test_login():
    """Test login endpoint"""
    print("🔑 Testing login endpoint...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", 
                           json=login_data, 
                           headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json().get('tokens', {})
    return None

def test_protected_endpoint(tokens):
    """Test protected endpoint with JWT token"""
    if not tokens:
        print("❌ No tokens available for testing protected endpoint")
        return
        
    print("🔒 Testing protected endpoint...")
    
    headers = {
        'Authorization': f"Bearer {tokens['access']}",
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_jwt_token_endpoint():
    """Test JWT token endpoint"""
    print("🎫 Testing JWT token endpoint...")
    
    jwt_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/token/", json=jwt_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("🚀 Testing Backend-Frontend Authentication Sync\n")
    
    # Test CORS
    test_cors_preflight()
    
    # Test login
    tokens = test_login()
    
    # Test protected endpoint
    test_protected_endpoint(tokens)
    
    # Test JWT endpoint
    test_jwt_token_endpoint()
    
    print("✅ Authentication sync test completed!")
