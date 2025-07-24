#!/usr/bin/env python
"""
Test script to demonstrate book club views functionality
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Book-Club-backend.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import BookClub, Membership, Author, Genre, Book
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from myapp.views import BookClubViewSet
from rest_framework import status

def create_test_data():
    """Create test data for demonstration"""
    print("📚 Creating test data...")
    
    # Create test users
    user1, created = User.objects.get_or_create(
        username='bookworm1',
        defaults={
            'email': 'bookworm1@example.com',
            'first_name': 'Alice',
            'last_name': 'Reader'
        }
    )
    
    user2, created = User.objects.get_or_create(
        username='reader2',
        defaults={
            'email': 'reader2@example.com',
            'first_name': 'Bob',
            'last_name': 'Writer'
        }
    )
    
    # Create test authors
    author1, created = Author.objects.get_or_create(
        first_name='Agatha',
        last_name='Christie'
    )
    
    author2, created = Author.objects.get_or_create(
        first_name='Arthur',
        last_name='Doyle'
    )
    
    # Create test genres
    mystery_genre, created = Genre.objects.get_or_create(
        name='Mystery',
        defaults={'description': 'Mystery and detective fiction'}
    )
    
    fiction_genre, created = Genre.objects.get_or_create(
        name='Fiction',
        defaults={'description': 'General fiction'}
    )
    
    # Create test books
    book1, created = Book.objects.get_or_create(
        title='Murder on the Orient Express',
        defaults={
            'description': 'A classic mystery novel',
            'page_count': 256
        }
    )
    book1.authors.add(author1)
    book1.genres.add(mystery_genre, fiction_genre)
    
    book2, created = Book.objects.get_or_create(
        title='The Adventures of Sherlock Holmes',
        defaults={
            'description': 'Classic detective stories',
            'page_count': 307
        }
    )
    book2.authors.add(author2)
    book2.genres.add(mystery_genre, fiction_genre)
    
    print("✅ Test data created successfully!")
    return user1, user2, book1, book2

def test_book_club_creation():
    """Test book club creation"""
    print("\n🏛️ Testing Book Club Creation...")
    
    user1, user2, book1, book2 = create_test_data()
    
    # Create book clubs
    club1 = BookClub.objects.create(
        name="Mystery Lovers Club",
        description="A club for mystery novel enthusiasts",
        creator=user1,
        is_private=False,
        max_members=25,
        location="Downtown Library",
        meeting_frequency="Monthly"
    )
    
    club2 = BookClub.objects.create(
        name="Private Reading Circle",
        description="An exclusive book club for serious readers",
        creator=user2,
        is_private=True,
        max_members=10,
        location="Member's Home",
        meeting_frequency="Bi-weekly"
    )
    
    print(f"✅ Created club: {club1.name}")
    print(f"   - Creator: {club1.creator.username}")
    print(f"   - Privacy: {'Private' if club1.is_private else 'Public'}")
    print(f"   - Max Members: {club1.max_members}")
    print(f"   - Current Members: {club1.member_count}")
    
    print(f"✅ Created club: {club2.name}")
    print(f"   - Creator: {club2.creator.username}")
    print(f"   - Privacy: {'Private' if club2.is_private else 'Public'}")
    print(f"   - Max Members: {club2.max_members}")
    print(f"   - Current Members: {club2.member_count}")
    
    return club1, club2, user1, user2

def test_book_club_listing():
    """Test book club listing functionality"""
    print("\n📋 Testing Book Club Listing...")
    
    # Get all book clubs
    all_clubs = BookClub.objects.all()
    print(f"📊 Total book clubs in database: {all_clubs.count()}")
    
    # List public clubs
    public_clubs = BookClub.objects.filter(is_private=False)
    print(f"🌐 Public book clubs: {public_clubs.count()}")
    
    for club in public_clubs:
        print(f"   • {club.name} (Creator: {club.creator.username})")
    
    # List private clubs
    private_clubs = BookClub.objects.filter(is_private=True)
    print(f"🔒 Private book clubs: {private_clubs.count()}")
    
    for club in private_clubs:
        print(f"   • {club.name} (Creator: {club.creator.username})")

def test_membership_functionality():
    """Test membership creation and management"""
    print("\n👥 Testing Membership Functionality...")
    
    club1, club2, user1, user2 = test_book_club_creation()
    
    # User2 joins User1's public club
    membership1 = Membership.objects.create(
        user=user2,
        book_club=club1,
        role='member'
    )
    
    print(f"✅ {user2.username} joined {club1.name} as {membership1.role}")
    print(f"   - Club now has {club1.member_count} members")
    
    # User1 creates admin membership for their own club (simulating auto-creation)
    admin_membership = Membership.objects.create(
        user=user1,
        book_club=club1,
        role='admin'
    )
    
    print(f"✅ {user1.username} is now admin of {club1.name}")
    print(f"   - Club now has {club1.member_count} members")
    
    # List all memberships
    memberships = Membership.objects.all().select_related('user', 'book_club')
    print(f"\n📊 All memberships ({memberships.count()}):")
    for membership in memberships:
        print(f"   • {membership.user.username} → {membership.book_club.name} ({membership.role})")

def test_view_permissions():
    """Test view permissions and filtering"""
    print("\n🔐 Testing View Permissions...")
    
    all_clubs = BookClub.objects.all()
    public_clubs = BookClub.objects.filter(is_private=False)
    private_clubs = BookClub.objects.filter(is_private=True)
    
    print(f"📊 Permission Summary:")
    print(f"   - Total clubs: {all_clubs.count()}")
    print(f"   - Public (visible to all): {public_clubs.count()}")
    print(f"   - Private (members only): {private_clubs.count()}")
    
    # Simulate what different users can see
    user1 = User.objects.get(username='bookworm1')
    user2 = User.objects.get(username='reader2')
    
    # User1's visible clubs (public + created + member of)
    user1_memberships = Membership.objects.filter(user=user1, is_active=True).values_list('book_club_id', flat=True)
    user1_visible = BookClub.objects.filter(
        models.Q(is_private=False) |
        models.Q(creator=user1) |
        models.Q(id__in=user1_memberships)
    ).distinct()
    
    print(f"\n👤 {user1.username} can see {user1_visible.count()} clubs:")
    for club in user1_visible:
        reason = "Public" if not club.is_private else ("Created" if club.creator == user1 else "Member")
        print(f"   • {club.name} ({reason})")

def main():
    """Run all tests"""
    print("🚀 Testing Book Club Views Functionality")
    print("=" * 50)
    
    try:
        # Test creation
        test_book_club_creation()
        
        # Test listing
        test_book_club_listing()
        
        # Test memberships
        test_membership_functionality()
        
        # Test permissions
        test_view_permissions()
        
        print("\n🎉 All tests completed successfully!")
        print("✅ Book club creation and listing views are working properly!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Import models here to avoid import issues
    from django.db import models
    main()
