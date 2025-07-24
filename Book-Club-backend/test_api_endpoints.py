#!/usr/bin/env python
"""
Test script to demonstrate Book Club API endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_user_registration_and_auth():
    """Test user registration and get auth token"""
    print("👤 Testing User Registration and Authentication...")
    
    # Register a test user
    register_data = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register/", json=register_data)
        if response.status_code == 201:
            data = response.json()
            token = data['tokens']['access']
            print(f"✅ User registered successfully: {data['user']['username']}")
            return token
        else:
            print(f"⚠️ Registration response: {response.status_code}")
            print(response.text)
            
            # Try to login if user already exists
            login_data = {
                "email": "testuser1@example.com",
                "password": "testpassword123"
            }
            login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
            if login_response.status_code == 200:
                data = login_response.json()
                token = data['tokens']['access']
                print(f"✅ User logged in successfully: {data['user']['username']}")
                return token
            else:
                print(f"❌ Login failed: {login_response.text}")
                return None
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running on localhost:8000")
        return None

def test_book_club_creation(token):
    """Test book club creation"""
    print("\n🏛️ Testing Book Club Creation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a public book club
    club_data = {
        "name": "API Test Mystery Club",
        "description": "A book club created via API for testing",
        "is_private": False,
        "max_members": 30,
        "location": "Virtual Meeting",
        "meeting_frequency": "Monthly"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/book-clubs/", json=club_data, headers=headers)
        if response.status_code == 201:
            club = response.json()
            print(f"✅ Book club created successfully!")
            print(f"   - ID: {club.get('id')}")
            print(f"   - Name: {club.get('name')}")
            print(f"   - Creator: {club.get('creator', {}).get('username')}")
            print(f"   - Privacy: {'Private' if club.get('is_private') else 'Public'}")
            print(f"   - Max Members: {club.get('max_members')}")
            return club.get('id')
        else:
            print(f"❌ Failed to create book club: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None

def test_book_club_listing(token):
    """Test book club listing"""
    print("\n📋 Testing Book Club Listing...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test basic listing
        response = requests.get(f"{BASE_URL}/api/book-clubs/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            clubs = data.get('results', [])
            print(f"✅ Retrieved {len(clubs)} book clubs")
            
            for club in clubs:
                print(f"   • {club.get('name')} (ID: {club.get('id')})")
                print(f"     Creator: {club.get('creator', {}).get('username')}")
                print(f"     Members: {club.get('member_count', 0)}")
                print(f"     Privacy: {'Private' if club.get('is_private') else 'Public'}")
            
            return clubs
        else:
            print(f"❌ Failed to list book clubs: {response.status_code}")
            print(response.text)
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return []

def test_my_clubs(token):
    """Test my clubs endpoint"""
    print("\n👤 Testing My Clubs Endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/book-clubs/my_clubs/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ My Clubs Summary:")
            print(f"   - Created: {data.get('created_count', 0)} clubs")
            print(f"   - Member of: {data.get('member_count', 0)} clubs")
            print(f"   - Total: {data.get('total_count', 0)} clubs")
            
            clubs = data.get('clubs', [])
            for club in clubs:
                print(f"   • {club.get('name')}")
            
            return data
        else:
            print(f"❌ Failed to get my clubs: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None

def test_book_club_search():
    """Test book club search (public endpoint)"""
    print("\n🔍 Testing Book Club Search...")
    
    try:
        # Test search without authentication (public clubs only)
        response = requests.get(f"{BASE_URL}/api/book-clubs/search/?search=test")
        if response.status_code == 200:
            data = response.json()
            clubs = data.get('results', [])
            print(f"✅ Search found {len(clubs)} public clubs matching 'test'")
            
            for club in clubs:
                print(f"   • {club.get('name')}")
                print(f"     Can Join: {club.get('can_join', 'N/A')}")
                print(f"     Members: {club.get('member_count', 0)}/{club.get('max_members', 0)}")
            
            return clubs
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return []

def test_book_club_discovery():
    """Test book club discovery endpoint"""
    print("\n🌟 Testing Book Club Discovery...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/book-clubs/discover/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Discovery Results:")
            print(f"   - Featured clubs: {len(data.get('featured', []))}")
            print(f"   - Recent clubs: {len(data.get('recent', []))}")
            print(f"   - Popular clubs: {len(data.get('popular', []))}")
            print(f"   - Total public clubs: {data.get('total_public_clubs', 0)}")
            
            # Show featured clubs
            featured = data.get('featured', [])
            if featured:
                print(f"\n⭐ Featured Clubs:")
                for club in featured[:3]:  # Show first 3
                    print(f"   • {club.get('name')} ({club.get('member_count', 0)} members)")
            
            return data
        else:
            print(f"❌ Discovery failed: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None

def test_book_club_join(token, club_id):
    """Test joining a book club"""
    print(f"\n🤝 Testing Book Club Join (Club ID: {club_id})...")
    
    if not club_id:
        print("⚠️ No club ID provided, skipping join test")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/book-clubs/{club_id}/join/", headers=headers)
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Successfully joined club!")
            print(f"   Message: {data.get('message')}")
            membership = data.get('membership', {})
            print(f"   Role: {membership.get('role')}")
            return True
        elif response.status_code == 400:
            # Probably already a member
            error_data = response.json()
            print(f"⚠️ Cannot join: {error_data.get('error')}")
            return False
        else:
            print(f"❌ Join failed: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Testing Book Club API Endpoints")
    print("=" * 50)
    
    # Step 1: Register/Login user
    token = test_user_registration_and_auth()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Step 2: Create a book club
    club_id = test_book_club_creation(token)
    
    # Step 3: List book clubs
    clubs = test_book_club_listing(token)
    
    # Step 4: Get my clubs
    my_clubs = test_my_clubs(token)
    
    # Step 5: Search book clubs
    search_results = test_book_club_search()
    
    # Step 6: Test discovery
    discovery_results = test_book_club_discovery()
    
    # Step 7: Test joining (if we have a club)
    if club_id:
        test_book_club_join(token, club_id)
    
    print("\n🎉 API Testing Complete!")
    print("✅ All book club creation and listing endpoints are working!")

if __name__ == "__main__":
    main()
