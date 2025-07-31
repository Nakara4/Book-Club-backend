#!/usr/bin/env python
"""
Example usage of the new external ID features and manager methods.

This script demonstrates how to use the get_or_create_by_external_id methods
for idempotent seeding and external image support.

Run this script after running migrations:
python manage.py migrate
python example_usage.py
"""

import os
import django
from datetime import datetime
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.models import Book, BookClub, UserProfile, User, Author


def example_book_creation():
    """Demonstrate idempotent book creation with external IDs"""
    print("=== Book Creation Examples ===")
    
    # Create some authors first
    author, created = Author.objects.get_or_create(
        first_name="George",
        last_name="Orwell",
        defaults={
            "bio": "English novelist and journalist",
            "birth_date": "1903-06-25"
        }
    )
    print(f"Author: {author} ({'created' if created else 'already exists'})")
    
    # Example 1: Create book with Open Library ID
    book_data = {
        'title': '1984',
        'description': 'A dystopian social science fiction novel.',
        'publication_date': '1949-06-08',
        'publisher': 'Secker & Warburg',
        'page_count': 328,
        'image_url': 'https://covers.openlibrary.org/b/id/12345-L.jpg',
        'image_updated_at': timezone.now()
    }
    
    book1, created1 = Book.objects.get_or_create_by_external_id(
        external_id='OL1017825M',
        source='openlibrary',
        defaults=book_data
    )
    book1.authors.add(author)
    print(f"Book 1: {book1.title} ({'created' if created1 else 'already exists'})")
    print(f"  External ID: {book1.external_id}")
    print(f"  Source: {book1.source}")
    print(f"  Image URL: {book1.image_url}")
    
    # Example 2: Try to create the same book again (should return existing)
    book2, created2 = Book.objects.get_or_create_by_external_id(
        external_id='OL1017825M',
        source='openlibrary',
        defaults={'title': 'Different Title'}  # This won't be used
    )
    print(f"Book 2: {book2.title} ({'created' if created2 else 'already exists'})")
    print(f"  Same book? {book1.id == book2.id}")
    
    # Example 3: Create book with Google Books ID
    animal_farm_data = {
        'title': 'Animal Farm',
        'description': 'A satirical allegorical novella.',
        'publication_date': '1945-08-17',
        'publisher': 'Secker & Warburg',
        'page_count': 112,
        'image_url': 'https://books.google.com/books/content?id=xyz&printsec=frontcover&img=1&zoom=1',
        'image_updated_at': timezone.now()
    }
    
    book3, created3 = Book.objects.get_or_create_by_external_id(
        external_id='abc123xyz',
        source='googlebooks',
        defaults=animal_farm_data
    )
    book3.authors.add(author)
    print(f"Book 3: {book3.title} ({'created' if created3 else 'already exists'})")
    print(f"  External ID: {book3.external_id}")
    print(f"  Source: {book3.source}")
    

def example_bookclub_creation():
    """Demonstrate idempotent book club creation with external IDs"""
    print("\n=== BookClub Creation Examples ===")
    
    # Create a user for the club
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User'
        }
    )
    print(f"User: {user.username} ({'created' if created else 'already exists'})")
    
    # Example 1: Create book club with external ID
    club_data = {
        'name': 'Orwell Reading Group',
        'description': 'A club dedicated to reading George Orwell\'s works',
        'creator': user,
        'category': 'Classic Literature',
        'is_private': False,
        'max_members': 25,
        'location': 'New York, NY',
        'meeting_frequency': 'Monthly',
        'image_url': 'https://example.com/club-images/orwell-group.jpg',
        'image_updated_at': timezone.now()
    }
    
    club1, created1 = BookClub.objects.get_or_create_by_external_id(
        external_id='goodreads_group_12345',
        source='goodreads',
        defaults=club_data
    )
    print(f"Club 1: {club1.name} ({'created' if created1 else 'already exists'})")
    print(f"  External ID: {club1.external_id}")
    print(f"  Source: {club1.source}")
    print(f"  Image URL: {club1.image_url}")
    
    # Example 2: Try to create the same club again
    club2, created2 = BookClub.objects.get_or_create_by_external_id(
        external_id='goodreads_group_12345',
        source='goodreads',
        defaults={'name': 'Different Name'}  # This won't be used
    )
    print(f"Club 2: {club2.name} ({'created' if created2 else 'already exists'})")
    print(f"  Same club? {club1.id == club2.id}")


def example_user_profile():
    """Demonstrate user profile with image URL"""
    print("\n=== UserProfile Examples ===")
    
    # Get or create a user
    user, created = User.objects.get_or_create(
        username='reader1',
        defaults={
            'email': 'reader1@example.com',
            'first_name': 'John',
            'last_name': 'Reader'
        }
    )
    print(f"User: {user.username} ({'created' if created else 'already exists'})")
    
    # Create or update profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'bio': 'Avid reader of science fiction and fantasy novels.',
            'location': 'San Francisco, CA',
            'website': 'https://johnreader.blog',
            'image_url': 'https://example.com/profiles/john-reader.jpg',
            'image_updated_at': timezone.now()
        }
    )
    print(f"Profile: {profile} ({'created' if created else 'already exists'})")
    print(f"  Bio: {profile.bio}")
    print(f"  Image URL: {profile.image_url}")


def demonstrate_queries():
    """Demonstrate some useful queries with the new fields"""
    print("\n=== Query Examples ===")
    
    # Find all books from Open Library
    openlibrary_books = Book.objects.filter(source='openlibrary')
    print(f"Books from Open Library: {openlibrary_books.count()}")
    
    # Find all books with external images
    books_with_images = Book.objects.filter(image_url__isnull=False)
    print(f"Books with external images: {books_with_images.count()}")
    
    # Find book clubs from Goodreads
    goodreads_clubs = BookClub.objects.filter(source='goodreads')
    print(f"Book clubs from Goodreads: {goodreads_clubs.count()}")
    
    # Find users with profile images
    users_with_images = User.objects.filter(profile__image_url__isnull=False)
    print(f"Users with profile images: {users_with_images.count()}")


if __name__ == '__main__':
    print("Running external ID and image URL examples...")
    print("=" * 50)
    
    try:
        example_book_creation()
        example_bookclub_creation()
        example_user_profile()
        demonstrate_queries()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nKey features demonstrated:")
        print("✓ UserProfile model with image_url and image_updated_at")
        print("✓ Book model with external_id, source, image_url, and image_updated_at")
        print("✓ BookClub model with external_id, source, image_url, and image_updated_at")
        print("✓ UniqueConstraint on (external_id, source) for both Book and BookClub")
        print("✓ get_or_create_by_external_id manager methods for idempotent seeding")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure to run 'python manage.py migrate' first!")
