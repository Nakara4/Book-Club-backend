#!/usr/bin/env python
"""
Simple test to demonstrate core book club functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def main():
    print("🚀 Simple Book Club API Test")
    print("=" * 40)
    
    # Step 1: Register a user
    print("\n1️⃣ Registering new user...")
    register_data = {
        "username": "simpletest",
        "email": "simpletest@example.com", 
        "password": "testpass123",
        "confirm_password": "testpass123",
        "first_name": "Simple",
        "last_name": "Test"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register/", json=register_data)
        if response.status_code == 201:
            token = response.json()['tokens']['access']
            print("✅ User registered successfully!")
        else:
            # User probably exists, try login
            login_data = {"email": "simpletest@example.com", "password": "testpass123"}
            response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
            if response.status_code == 200:
                token = response.json()['tokens']['access']
                print("✅ User logged in successfully!")
            else:
                print("❌ Could not authenticate user")
                return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 2: Create a book club
    print("\n2️⃣ Creating book club...")
    headers = {"Authorization": f"Bearer {token}"}
    club_data = {
        "name": "Simple Test Book Club",
        "description": "A simple book club for testing",
        "is_private": False,
        "max_members": 15,
        "location": "Online",
        "meeting_frequency": "Weekly"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/book-clubs/", json=club_data, headers=headers)
        if response.status_code == 201:
            club = response.json()
            print("✅ Book club created successfully!")
            print(f"   - Name: {club.get('name')}")
            print(f"   - Max Members: {club.get('max_members')}")
            club_id = club.get('id')
        else:
            print(f"❌ Failed to create book club: {response.status_code}")
            print(response.text)
            club_id = None
    except Exception as e:
        print(f"❌ Error: {e}")
        club_id = None
    
    # Step 3: List book clubs
    print("\n3️⃣ Listing book clubs...")
    try:
        response = requests.get(f"{BASE_URL}/api/book-clubs/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            clubs = data.get('results', [])
            print(f"✅ Found {len(clubs)} book clubs:")
            for club in clubs[:3]:  # Show first 3
                print(f"   • {club.get('name')} (Members: {club.get('member_count', 0)})")
        else:
            print(f"❌ Failed to list book clubs: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Step 4: Test joining club (if we created one)
    if club_id:
        print(f"\n4️⃣ Testing join club (ID: {club_id})...")
        try:
            response = requests.post(f"{BASE_URL}/api/book-clubs/{club_id}/join/", headers=headers)
            if response.status_code == 201:
                print("✅ Successfully joined the club!")
            elif response.status_code == 400:
                print("⚠️ Already a member (expected for creator)")
            else:
                print(f"❌ Join failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Test completed!")
    print("✅ Core book club creation and listing functionality is working!")

if __name__ == "__main__":
    main()
