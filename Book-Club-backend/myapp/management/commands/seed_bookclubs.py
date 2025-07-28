from faker import Faker
from myapp.models import BookClub, User, Membership, Book, Genre, Author, ReadingSession, Discussion, Review
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seed the database with realistic book club data'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()
        
        self.stdout.write('Seeding realistic book club data...')
        self.seed_users()
        self.seed_authors_and_genres()
        self.seed_books()
        self.seed_book_clubs()
        self.seed_reading_sessions()
        self.seed_discussions_and_reviews()
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

    def clear_data(self):
        BookClub.objects.all().delete()
        Book.objects.all().delete()
        Author.objects.all().delete()
        Genre.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def seed_users(self):
        fake = Faker()
        self.stdout.write('Creating users...')
        
        users_data = [
            {'username': 'bookworm_sarah', 'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah.j@email.com'},
            {'username': 'literaturelover', 'first_name': 'Michael', 'last_name': 'Chen', 'email': 'michael.chen@email.com'},
            {'username': 'novel_reader', 'first_name': 'Emma', 'last_name': 'Williams', 'email': 'emma.w@email.com'},
            {'username': 'mystery_maven', 'first_name': 'David', 'last_name': 'Brown', 'email': 'david.brown@email.com'},
            {'username': 'fantasy_fan', 'first_name': 'Jessica', 'last_name': 'Davis', 'email': 'jessica.d@email.com'},
        ]
        
        for user_data in users_data:
            User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                    'password': 'pbkdf2_sha256$600000$placeholder$hash'
                }
            )
        
        # Create additional random users
        for _ in range(45):
            username = fake.user_name()
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email(),
                    password='password123'
                )

    def seed_authors_and_genres(self):
        self.stdout.write('Creating authors and genres...')
        
        # Popular authors
        famous_authors = [
            {'first_name': 'Agatha', 'last_name': 'Christie', 'bio': 'Famous mystery writer known for Hercule Poirot and Miss Marple series.'},
            {'first_name': 'Stephen', 'last_name': 'King', 'bio': 'Master of horror and supernatural fiction.'},
            {'first_name': 'J.K.', 'last_name': 'Rowling', 'bio': 'Author of the Harry Potter series.'},
            {'first_name': 'Jane', 'last_name': 'Austen', 'bio': 'Classic English novelist known for Pride and Prejudice.'},
            {'first_name': 'George', 'last_name': 'Orwell', 'bio': 'Author of 1984 and Animal Farm.'},
            {'first_name': 'Toni', 'last_name': 'Morrison', 'bio': 'Nobel Prize-winning author known for Beloved.'},
            {'first_name': 'Harper', 'last_name': 'Lee', 'bio': 'Author of To Kill a Mockingbird.'},
            {'first_name': 'Margaret', 'last_name': 'Atwood', 'bio': 'Canadian author known for The Handmaid\'s Tale.'},
        ]
        
        for author_data in famous_authors:
            Author.objects.get_or_create(
                first_name=author_data['first_name'],
                last_name=author_data['last_name'],
                defaults={'bio': author_data['bio']}
            )
        
        # Book genres
        genres_data = [
            {'name': 'Fiction', 'description': 'Imaginative works of prose, mainly novels and short stories'},
            {'name': 'Mystery', 'description': 'Stories involving puzzles, crimes, or unexplained events'},
            {'name': 'Romance', 'description': 'Stories focused on love relationships and romantic entanglements'},
            {'name': 'Science Fiction', 'description': 'Speculative fiction dealing with futuristic concepts'},
            {'name': 'Fantasy', 'description': 'Fiction involving magical or supernatural elements'},
            {'name': 'Biography', 'description': 'Detailed accounts of real people\'s lives'},
            {'name': 'History', 'description': 'Non-fiction works about past events'},
            {'name': 'Self-Help', 'description': 'Books designed to help readers improve their lives'},
            {'name': 'Young Adult', 'description': 'Literature targeted towards teenage readers'},
            {'name': 'Literary Fiction', 'description': 'Character-driven fiction with artistic merit'},
        ]
        
        for genre_data in genres_data:
            Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults={'description': genre_data['description']}
            )

    def seed_books(self):
        self.stdout.write('Creating books...')
        fake = Faker()
        authors = list(Author.objects.all())
        genres = list(Genre.objects.all())
        
        # Popular books
        popular_books = [
            {'title': 'Pride and Prejudice', 'author': 'Jane Austen', 'genre': 'Fiction', 'pages': 432},
            {'title': 'Murder on the Orient Express', 'author': 'Agatha Christie', 'genre': 'Mystery', 'pages': 256},
            {'title': 'The Shining', 'author': 'Stephen King', 'genre': 'Fiction', 'pages': 688},
            {'title': '1984', 'author': 'George Orwell', 'genre': 'Fiction', 'pages': 328},
            {'title': 'Harry Potter and the Philosopher\'s Stone', 'author': 'J.K. Rowling', 'genre': 'Fantasy', 'pages': 223},
            {'title': 'Beloved', 'author': 'Toni Morrison', 'genre': 'Literary Fiction', 'pages': 321},
            {'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'genre': 'Fiction', 'pages': 376},
            {'title': 'The Handmaid\'s Tale', 'author': 'Margaret Atwood', 'genre': 'Science Fiction', 'pages': 311},
        ]
        
        for book_data in popular_books:
            try:
                author = Author.objects.get(last_name=book_data['author'].split()[-1])
                genre = Genre.objects.get(name=book_data['genre'])
                
                book, created = Book.objects.get_or_create(
                    title=book_data['title'],
                    defaults={
                        'description': fake.text(max_nb_chars=500),
                        'page_count': book_data['pages'],
                        'publication_date': fake.date_this_century(),
                        'publisher': fake.company(),
                    }
                )
                
                if created:
                    book.authors.add(author)
                    book.genres.add(genre)
            except (Author.DoesNotExist, Genre.DoesNotExist):
                continue
        
        # Create additional random books
        for _ in range(50):
            book = Book.objects.create(
                title=fake.catch_phrase() + ': A Novel',
                description=fake.text(max_nb_chars=500),
                page_count=random.randint(200, 600),
                publication_date=fake.date_between(start_date='-50y', end_date='today'),
                publisher=fake.company(),
            )
            book.authors.set(random.sample(authors, k=random.randint(1, 2)))
            book.genres.set(random.sample(genres, k=random.randint(1, 2)))

    def seed_book_clubs(self):
        self.stdout.write('Creating book clubs...')
        fake = Faker()
        users = list(User.objects.all())
        
        # Image mapping for book clubs
        image_mapping = {
            'Mystery': 'bookclub_images/mystery_club.jpg',
            'Romance': 'bookclub_images/romance_club.jpg', 
            'Science Fiction': 'bookclub_images/scifi_club.jpg',
            'Literary Fiction': 'bookclub_images/literary_club.jpg',
            'Fantasy': 'bookclub_images/fantasy_club.jpg',
            'Young Adult': 'bookclub_images/ya_club.jpg',
            'Non-Fiction': 'bookclub_images/mystery_club.jpg',  # fallback
            'Fiction': 'bookclub_images/classic_club.jpg'
        }
        
        # Realistic book club names and descriptions
        book_clubs_data = [
            {
                'name': 'Mystery Lovers United',
                'description': 'Dive into thrilling mysteries, solve puzzles, and discuss plot twists with fellow detective fiction enthusiasts. From Agatha Christie classics to modern Nordic noir.',
                'category': 'Mystery',
                'location': 'Downtown Library',
                'frequency': 'Monthly'
            },
            {
                'name': 'Romantic Reads & Wine',
                'description': 'Share heartwarming romances over a glass of wine. We explore contemporary romance, historical fiction, and everything that makes our hearts flutter.',
                'category': 'Romance', 
                'location': 'Cozy Corner Café',
                'frequency': 'Bi-weekly'
            },
            {
                'name': 'Sci-Fi Explorers',
                'description': 'Journey through galaxies, explore futuristic worlds, and discuss the possibilities of tomorrow. Perfect for fans of hard sci-fi and space opera.',
                'category': 'Science Fiction',
                'location': 'Tech Hub Community Center',
                'frequency': 'Monthly'
            },
            {
                'name': 'Literary Ladies',
                'description': 'A supportive community of women readers exploring literary fiction, memoirs, and thought-provoking narratives that challenge and inspire.',
                'category': 'Literary Fiction',
                'location': 'Riverside Park Pavilion',
                'frequency': 'Monthly'
            },
            {
                'name': 'Fantasy & Magic Circle',
                'description': 'Escape to magical realms, meet dragons and wizards, and discuss epic fantasy adventures. From Tolkien to modern fantasy authors.',
                'category': 'Fantasy',
                'location': 'Game & Book Café',
                'frequency': 'Monthly'
            },
            {
                'name': 'Young Adult Adventures',
                'description': 'Exploring coming-of-age stories, dystopian futures, and young love. Perfect for readers who love YA fiction and nostalgic about teen years.',
                'category': 'Young Adult',
                'location': 'University Student Center',
                'frequency': 'Weekly'
            },
            {
                'name': 'Non-Fiction Knowledge Seekers',
                'description': 'Expand your mind with biographies, history, science, and self-improvement books. Learn something new with every meeting.',
                'category': 'Non-Fiction',
                'location': 'Community Learning Center',
                'frequency': 'Monthly'
            },
            {
                'name': 'Classic Literature Society',
                'description': 'Rediscover timeless classics and explore the greatest works of literature. From Shakespeare to Dickens, we celebrate literary heritage.',
                'category': 'Fiction',
                'location': 'Historic Library Main Hall',
                'frequency': 'Monthly'
            }
        ]
        
        for club_data in book_clubs_data:
            creator = random.choice(users)
            # Get image path for this category
            image_path = image_mapping.get(club_data['category'], 'bookclub_images/mystery_club.jpg')
            
            club = BookClub.objects.create(
                name=club_data['name'],
                description=club_data['description'],
                creator=creator,
                category=club_data['category'],
                image=image_path,
                location=club_data['location'],
                meeting_frequency=club_data['frequency'],
                max_members=random.randint(15, 50),
                is_private=random.choice([True, False])
            )
            
            # Add members to the club
            member_count = random.randint(8, 25)
            members = random.sample(users, min(member_count, len(users)))
            
            for member in members:
                role = 'admin' if member == creator else random.choices(
                    ['member', 'moderator'], weights=[0.8, 0.2]
                )[0]
                
                Membership.objects.create(
                    user=member,
                    book_club=club,
                    role=role,
                    joined_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone())
                )

    def seed_reading_sessions(self):
        self.stdout.write('Creating reading sessions...')
        fake = Faker()
        book_clubs = list(BookClub.objects.all())
        books = list(Book.objects.all())
        
        for club in book_clubs[:5]:  # Create sessions for first 5 clubs
            # Current reading session
            current_book = random.choice(books)
            start_date = timezone.now().date() - timedelta(days=random.randint(5, 20))
            end_date = start_date + timedelta(days=random.randint(20, 45))
            
            ReadingSession.objects.create(
                book_club=club,
                book=current_book,
                start_date=start_date,
                end_date=end_date,
                status='current',
                notes=fake.text(max_nb_chars=200)
            )
            
            # Past reading session
            past_book = random.choice([b for b in books if b != current_book])
            past_start = start_date - timedelta(days=random.randint(30, 60))
            past_end = past_start + timedelta(days=random.randint(20, 40))
            
            ReadingSession.objects.create(
                book_club=club,
                book=past_book,
                start_date=past_start,
                end_date=past_end,
                status='completed',
                notes=fake.text(max_nb_chars=200)
            )

    def seed_discussions_and_reviews(self):
        self.stdout.write('Creating discussions and reviews...')
        fake = Faker()
        book_clubs = list(BookClub.objects.all())
        
        for club in book_clubs:
            members = list(club.members.all())
            if not members:
                continue
                
            # Create discussions
            for _ in range(random.randint(2, 5)):
                Discussion.objects.create(
                    book_club=club,
                    author=random.choice(members),
                    title=fake.sentence(nb_words=6),
                    content=fake.text(max_nb_chars=400),
                    discussion_type=random.choice(['general', 'chapter', 'review']),
                    created_at=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone())
                )
            
            # Create reviews for books
            reading_sessions = club.reading_sessions.all()
            for session in reading_sessions:
                # Some members write reviews
                reviewers = random.sample(members, min(random.randint(2, 5), len(members)))
                for reviewer in reviewers:
                    # Check if review already exists to avoid unique constraint violation
                    if not Review.objects.filter(user=reviewer, book=session.book).exists():
                        Review.objects.create(
                            user=reviewer,
                            book=session.book,
                            rating=random.randint(3, 5),
                            title=fake.sentence(nb_words=4),
                            content=fake.text(max_nb_chars=300),
                            reading_session=session,
                            created_at=fake.date_time_between(start_date=session.start_date, end_date='now', tzinfo=timezone.get_current_timezone())
                        )

