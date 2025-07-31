import csv
import json
import random
from pathlib import Path
from faker import Faker
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
try:
    from tqdm import tqdm
except ImportError:
    # Fallback progress bar for when tqdm is not available
    class tqdm:
        def __init__(self, total=None, desc=None):
            self.total = total
            self.desc = desc
            self.n = 0
        
        def update(self, n=1):
            self.n += n
            if self.total:
                print(f"\r{self.desc}: {self.n}/{self.total} ({self.n/self.total*100:.1f}%)", end="", flush=True)
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            print()  # New line after progress

from myapp.models import UserProfile, Book, BookClub, Membership, ReadingProgress, Review


class Command(BaseCommand):
    help = 'Seed the database with realistic user profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', 
            type=int, 
            default=50, 
            help='Number of users to create (default: 50)'
        )
        parser.add_argument(
            '--clear', 
            action='store_true', 
            help='Clear existing user data before seeding'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of users to process in each database transaction (default: 10)'
        )
        parser.add_argument(
            '--goodreads-csv',
            type=str,
            help='Optional path to Goodreads CSV file for advanced realism'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating records'
        )

    def handle(self, *args, **options):
        count = options['count']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        goodreads_csv = options.get('goodreads_csv')

        if options['clear'] and not dry_run:
            self.stdout.write('Clearing existing user data...')
            self.clear_data()
        elif options['clear'] and dry_run:
            self.stdout.write('Would clear existing user data...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Load Goodreads data if provided
        goodreads_data = None
        if goodreads_csv:
            goodreads_data = self.load_goodreads_csv(goodreads_csv)
            if goodreads_data:
                self.stdout.write(f"Loaded {len(goodreads_data)} books from Goodreads CSV")
        
        self.stdout.write(f'Seeding {count} realistic users...')
        
        created_count = 0
        error_count = 0
        
        with tqdm(total=count, desc="Creating users") as pbar:
            # Process in batches for better database performance
            for i in range(0, count, batch_size):
                batch_count = min(batch_size, count - i)
                
                if not dry_run:
                    with transaction.atomic():
                        batch_results = self.seed_users_batch(batch_count, goodreads_data, pbar, dry_run=False)
                else:
                    batch_results = self.seed_users_batch(batch_count, goodreads_data, pbar, dry_run=True)
                
                created_count += batch_results['created']
                error_count += batch_results['errors']
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f"\nSeeding completed!"))
        self.stdout.write(f"Users created: {created_count}")
        
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"Errors encountered: {error_count}"))

    def clear_data(self):
        """Clear existing user-related data"""
        UserProfile.objects.all().delete()
        ReadingProgress.objects.all().delete()
        Review.objects.all().delete()
        Membership.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def load_goodreads_csv(self, csv_path):
        """Load books data from Goodreads CSV export for realistic reading history"""
        try:
            file_path = Path(csv_path)
            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f"Goodreads CSV file not found: {csv_path}"))
                return None
            
            books_data = []
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('Title') and row.get('Author'):
                        books_data.append({
                            'title': row['Title'].strip(),
                            'author': row['Author'].strip(),
                            'rating': self.safe_int(row.get('My Rating', 0)),
                            'date_read': row.get('Date Read', ''),
                            'shelves': row.get('Bookshelves', '').split(',')
                        })
            
            return books_data
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error loading Goodreads CSV: {e}"))
            return None

    def safe_int(self, value, default=0):
        """Safely convert value to int"""
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default

    def seed_users_batch(self, batch_count, goodreads_data, pbar, dry_run=False):
        """Create a batch of users with realistic profiles"""
        fake = Faker()
        results = {'created': 0, 'errors': 0}
        
        # Diverse locales for international users
        locales = [
            'en_US', 'en_GB', 'en_CA', 'en_AU',  # English
            'es_ES', 'es_MX', 'es_AR',           # Spanish
            'fr_FR', 'fr_CA',                    # French
            'de_DE', 'de_AT',                    # German
            'it_IT',                             # Italian
            'pt_BR', 'pt_PT',                    # Portuguese
            'ja_JP',                             # Japanese
            'ko_KR',                             # Korean
            'zh_CN',                             # Chinese
            'hi_IN',                             # Hindi
            'ar_EG',                             # Arabic
            'ru_RU',                             # Russian
            'nl_NL',                             # Dutch
            'sv_SE',                             # Swedish
            'no_NO',                             # Norwegian
        ]
        
        for _ in range(batch_count):
            try:
                # Use diverse locales for international feel
                locale = random.choice(locales)
                fake_localized = Faker(locale)
                
                # Generate unique username and email
                attempts = 0
                while attempts < 10:
                    username = fake.unique.user_name()
                    email = fake.unique.email()
                    
                    if not User.objects.filter(username=username).exists() and not User.objects.filter(email=email).exists():
                        break
                    attempts += 1
                else:
                    # Fallback to guaranteed unique values
                    username = f"{fake.user_name()}_{fake.random_int(1000, 9999)}"
                    email = f"{username}@{fake.domain_name()}"
                
                if dry_run:
                    self.stdout.write(f"Would create user: {username} ({email})")
                    results['created'] += 1
                    pbar.update(1)
                    continue
                
                # Create user with diverse profile
                user = User.objects.create_user(
                    username=username,
                    first_name=fake_localized.first_name(),
                    last_name=fake_localized.last_name(),
                    email=email,
                    password='password123',
                    date_joined=fake.date_time_between(start_date='-2y', end_date='now', tzinfo=timezone.get_current_timezone())
                )
                
                # Create diverse and interesting bio
                bio = self.generate_diverse_bio(fake_localized)
                
                # Choose avatar service randomly for variety
                avatar_services = [
                    f'https://i.pravatar.cc/150?u={email}',
                    f'https://api.dicebear.com/7.x/avataaars/svg?seed={username}',
                    f'https://api.dicebear.com/7.x/bottts/svg?seed={username}',
                    f'https://api.dicebear.com/7.x/identicon/svg?seed={username}'
                ]
                
                # Create user profile
                profile = UserProfile.objects.create(
                    user=user,
                    bio=bio,
                    location=fake_localized.country(),
                    website=fake.url() if random.choice([True, False]) else None,
                    image_url=random.choice(avatar_services),
                    image_updated_at=timezone.now()
                )
                
                # Assign reading history
                self.assign_reading_history(user, goodreads_data, fake)
                
                # Make half the users book club owners/admins
                self.assign_book_club_role(user, fake)
                
                results['created'] += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating user: {e}"))
                results['errors'] += 1
            
            pbar.update(1)
        
        return results

    def generate_diverse_bio(self, fake):
        """Generate diverse and interesting user bios"""
        bio_templates = [
            f"📚 Avid reader who loves {random.choice(['mystery novels', 'sci-fi adventures', 'romance stories', 'literary fiction', 'fantasy epics', 'historical novels'])}. {fake.sentence()}",
            f"✨ Book lover from {fake.city()}. Currently reading my way through {random.choice(['the classics', 'contemporary fiction', 'award winners', 'book club favorites'])}.",
            f"🌟 {fake.job()} by day, bookworm by night. Favorite genres: {random.choice(['thriller & mystery', 'romance & drama', 'fantasy & adventure', 'non-fiction & memoirs'])}.",
            f"📖 {fake.sentence()} Love discussing books and discovering new authors. Always looking for my next great read!",
            f"🎭 Theater enthusiast and bibliophile. Enjoy {random.choice(['classic literature', 'modern poetry', 'graphic novels', 'biographies'])} and long walks in the library.",
            f"🌍 World traveler who collects books from every country visited. {fake.sentence()} Currently exploring {random.choice(['Latin American literature', 'Asian authors', 'African stories', 'European classics'])}.",
            f"☕ Coffee and books are my love language. {fake.sentence()} Member of {random.randint(2, 5)} book clubs and counting!",
            f"🔥 Passionate about {random.choice(['environmental issues', 'social justice', 'mental health awareness', 'education reform'])} and the books that explore these themes."
        ]
        
        return random.choice(bio_templates)

    def assign_reading_history(self, user, goodreads_data, fake):
        """Assign realistic reading history to user"""
        books = list(Book.objects.all())
        
        if not books:
            return  # No books to assign
        
        # Use Goodreads data if available, otherwise generate random
        if goodreads_data and random.choice([True, False]):
            # Use some books from Goodreads data
            sample_books = random.sample(goodreads_data, min(random.randint(3, 8), len(goodreads_data)))
            
            for book_data in sample_books:
                # Try to find matching book in database
                matching_book = Book.objects.filter(
                    title__icontains=book_data['title'][:20]
                ).first()
                
                if matching_book:
                    # Create reading progress
                    is_finished = random.choice([True, True, False])  # 2/3 chance finished
                    current_page = matching_book.page_count if is_finished and matching_book.page_count else random.randint(1, matching_book.page_count or 300)
                    
                    progress, created = ReadingProgress.objects.get_or_create(
                        user=user,
                        book=matching_book,
                        defaults={
                            'current_page': current_page,
                            'is_finished': is_finished,
                            'started_at': fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone()),
                            'finished_at': fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()) if is_finished else None,
                            'notes': fake.sentence() if random.choice([True, False]) else None
                        }
                    )
                    
                    # Add review for finished books
                    if is_finished and not Review.objects.filter(user=user, book=matching_book).exists():
                        Review.objects.create(
                            user=user,
                            book=matching_book,
                            rating=book_data.get('rating', random.randint(3, 5)),
                            title=fake.sentence(nb_words=4),
                            content=fake.text(max_nb_chars=300),
                            created_at=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone())
                        )
        
        # Also add some random books from database
        random_books = random.sample(books, min(random.randint(2, 6), len(books)))
        
        for book in random_books:
            if not ReadingProgress.objects.filter(user=user, book=book).exists():
                is_finished = random.choice([True, True, False])  # 2/3 chance finished
                current_page = book.page_count if is_finished and book.page_count else random.randint(1, book.page_count or 300)
                
                ReadingProgress.objects.create(
                    user=user,
                    book=book,
                    current_page=current_page,
                    is_finished=is_finished,
                    started_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone()),
                    finished_at=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()) if is_finished else None,
                    notes=fake.sentence() if random.choice([True, False]) else None
                )
                
                # Add review for finished books
                if is_finished and not Review.objects.filter(user=user, book=book).exists() and random.choice([True, False]):
                    Review.objects.create(
                        user=user,
                        book=book,
                        rating=random.randint(3, 5),
                        title=fake.sentence(nb_words=4),
                        content=fake.text(max_nb_chars=300),
                        created_at=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone())
                    )

    def assign_book_club_role(self, user, fake):
        """Make half the users book club owners/admins"""
        clubs = list(BookClub.objects.all())
        
        if not clubs:
            return  # No clubs to assign
        
        # 50% chance to be a club owner/admin
        is_owner_admin = random.choice([True, False])
        
        if is_owner_admin:
            # Either create a new club or become admin of existing one
            if random.choice([True, False]) and len(clubs) < 20:  # Create new club
                new_club = BookClub.objects.create(
                    name=f"{fake.catch_phrase()} Book Club",
                    description=fake.text(max_nb_chars=400),
                    creator=user,
                    category=random.choice(['Fiction', 'Mystery', 'Romance', 'Science Fiction', 'Fantasy', 'Biography', 'History']),
                    location=fake.city(),
                    meeting_frequency=random.choice(['Weekly', 'Bi-weekly', 'Monthly']),
                    max_members=random.randint(15, 50),
                    is_private=random.choice([True, False])
                )
                
                # Creator automatically becomes admin
                Membership.objects.create(
                    user=user,
                    book_club=new_club,
                    role='admin',
                    joined_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone())
                )
            else:
                # Become admin of existing club
                club = random.choice(clubs)
                if not Membership.objects.filter(user=user, book_club=club).exists():
                    Membership.objects.create(
                        user=user,
                        book_club=club,
                        role=random.choice(['admin', 'moderator']),
                        joined_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone())
                    )
        else:
            # Regular member of 1-3 clubs
            member_clubs = random.sample(clubs, min(random.randint(1, 3), len(clubs)))
            
            for club in member_clubs:
                if not Membership.objects.filter(user=user, book_club=club).exists():
                    Membership.objects.create(
                        user=user,
                        book_club=club,
                        role='member',
                        joined_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone())
                    )
