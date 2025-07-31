from faker import Faker
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from myapp.models import (
    BookClub, Book, ReadingSession, Discussion, DiscussionReply, 
    Review, ReadingProgress, BookRecommendation, Membership
)
import random
from datetime import datetime, timedelta
import numpy as np

class Command(BaseCommand):
    help = 'Seed discussions, reviews, progress, and recommendations with realistic book-themed content'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
        parser.add_argument('--discussions', type=int, default=50, help='Number of discussions to create')
        parser.add_argument('--reviews', type=int, default=100, help='Number of reviews to create')
        parser.add_argument('--progress', type=int, default=200, help='Number of progress snapshots to create')

    def handle(self, *args, **options):
        self.fake = Faker()
        
        if options['clear']:
            self.stdout.write('Clearing existing discussions, reviews, progress, and recommendations...')
            self.clear_data()
        
        self.stdout.write('Seeding discussions, reviews, progress, and recommendations...')
        self.create_discussions_with_replies(options['discussions'])
        self.create_reviews_with_bell_curve(options['reviews'])
        self.create_reading_progress(options['progress'])
        self.create_recommendations()
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

    def clear_data(self):
        """Clear existing data"""
        DiscussionReply.objects.all().delete()
        Discussion.objects.all().delete()
        Review.objects.all().delete()
        ReadingProgress.objects.all().delete()
        BookRecommendation.objects.all().delete()

    def get_book_character_content(self, book_title):
        """Generate content that references book characters and themes"""
        # Map of book titles to character/theme content
        book_content_map = {
            'Pride and Prejudice': [
                "Elizabeth Bennet's wit reminds me of my own struggles with first impressions.",
                "Mr. Darcy's character development is one of the most compelling arcs in literature.",
                "The theme of social class barriers feels surprisingly relevant today.",
                "Jane and Bingley's relationship is so pure compared to the drama around them.",
                "Mrs. Bennet's obsession with marriage is both hilarious and tragic."
            ],
            'Murder on the Orient Express': [
                "Poirot's methodical approach to solving mysteries is fascinating to watch unfold.",
                "The confined setting of the train creates such perfect tension.",
                "Each passenger's backstory adds layers to the overall mystery.",
                "Christie's red herrings had me completely fooled until the reveal.",
                "The moral ambiguity of the ending still makes me think."
            ],
            'The Shining': [
                "Jack Torrance's descent into madness is terrifyingly well-written.",
                "The Overlook Hotel almost becomes a character itself.",
                "Wendy's strength in the face of terror is often underappreciated.",
                "Danny's psychic abilities add such an eerie supernatural element.",
                "The isolation theme hits differently after recent world events."
            ],
            '1984': [
                "Winston Smith's rebellion feels both hopeless and necessary.",
                "Big Brother's surveillance parallels our modern privacy concerns.",
                "The concept of doublethink is more relevant than ever.",
                "Julia's pragmatic rebellion contrasts beautifully with Winston's idealism.",
                "The Room 101 scenes still give me chills."
            ],
            "Harry Potter and the Philosopher's Stone": [
                "Harry's journey from neglect to belonging is so heartwarming.",
                "Hermione's intelligence and determination make her my favorite character.",
                "The friendship between Harry, Ron, and Hermione is the heart of the story.",
                "Hogwarts feels like a character itself - so richly detailed.",
                "Snape's complexity becomes more apparent with each re-read."
            ]
        }
        
        # Generic content for books not in the map
        generic_content = [
            "The character development throughout this book is extraordinary.",
            "I love how the author weaves themes of identity and belonging.",
            "The dialogue feels so authentic and natural.",
            "This book made me question my own assumptions about life.",
            "The ending left me with so many emotions to process.",
            "The world-building is incredibly detailed and immersive.",
            "I found myself relating to the protagonist's internal struggles.",
            "The author's use of symbolism adds depth to every chapter.",
            "This story will stay with me long after finishing it.",
            "The themes of love and loss are handled with such care."
        ]
        
        content_options = book_content_map.get(book_title, generic_content)
        return random.choice(content_options)

    def create_discussions_with_replies(self, num_discussions):
        """Create threaded discussions with book-themed content"""
        self.stdout.write(f'Creating {num_discussions} discussions with replies...')
        
        reading_sessions = list(ReadingSession.objects.all())
        if not reading_sessions:
            self.stdout.write(self.style.WARNING('No reading sessions found. Creating some basic ones...'))
            return

        for _ in range(num_discussions):
            session = random.choice(reading_sessions)
            club_members = list(session.book_club.members.all())
            
            if not club_members:
                continue

            author = random.choice(club_members)
            
            # Create discussion with book-themed content
            discussion_types = ['general', 'chapter', 'review', 'meeting']
            discussion_type = random.choice(discussion_types)
            
            # Generate title based on discussion type
            if discussion_type == 'chapter':
                title = f"Chapter {random.randint(1, 20)} Discussion - {session.book.title}"
            elif discussion_type == 'review':
                title = f"Overall thoughts on {session.book.title}"
            elif discussion_type == 'meeting':
                title = f"Meeting Discussion: {session.book.title}"
            else:
                title = f"Thoughts on {session.book.title}"

            # Generate content that references the book
            content = self.get_book_character_content(session.book.title)
            content += f" {self.fake.text(max_nb_chars=200)}"

            # Create discussion with believable timeline
            created_time = self.fake.date_time_between(
                start_date=max(session.start_date, timezone.now().date() - timedelta(days=30)),
                end_date=min(session.end_date, timezone.now().date()),
                tzinfo=timezone.utc
            )

            discussion = Discussion.objects.create(
                book_club=session.book_club,
                book=session.book,
                reading_session=session,
                author=author,
                title=title,
                content=content,
                discussion_type=discussion_type,
                chapter_number=random.randint(1, 20) if discussion_type == 'chapter' else None,
                is_pinned=random.choice([True, False]) if random.random() < 0.1 else False,
                is_spoiler=random.choice([True, False]) if random.random() < 0.3 else False,
                created_at=created_time,
                updated_at=created_time
            )

            # Create replies (threaded)
            num_replies = random.randint(0, 8)
            for _ in range(num_replies):
                reply_author = random.choice(club_members)
                reply_content = self.get_book_character_content(session.book.title)
                reply_content += f" {self.fake.text(max_nb_chars=150)}"
                
                reply_time = self.fake.date_time_between(
                    start_date=created_time,
                    end_date=min(session.end_date, timezone.now().date()),
                    tzinfo=timezone.utc
                )

                DiscussionReply.objects.create(
                    discussion=discussion,
                    author=reply_author,
                    content=reply_content,
                    is_spoiler=random.choice([True, False]) if random.random() < 0.2 else False,
                    created_at=reply_time,
                    updated_at=reply_time
                )

    def create_reviews_with_bell_curve(self, num_reviews):
        """Create reviews with bell curve rating distribution"""
        self.stdout.write(f'Creating {num_reviews} reviews with bell curve rating distribution...')
        
        books = list(Book.objects.all())
        users = list(User.objects.all())
        
        if not books or not users:
            self.stdout.write(self.style.WARNING('No books or users found.'))
            return

        # Generate ratings with bell curve (normal distribution centered at 3.5)
        ratings = np.random.normal(loc=3.5, scale=0.8, size=num_reviews)
        ratings = np.clip(np.round(ratings), 1, 5).astype(int)

        created_reviews = 0
        attempts = 0
        max_attempts = num_reviews * 3

        while created_reviews < num_reviews and attempts < max_attempts:
            attempts += 1
            user = random.choice(users)
            book = random.choice(books)
            
            # Check if review already exists
            if Review.objects.filter(user=user, book=book).exists():
                continue

            rating = ratings[created_reviews]
            
            # Generate review title and content
            if rating >= 4:
                titles = [
                    f"Absolutely loved {book.title}!",
                    f"A masterpiece - {book.title}",
                    f"{book.title} exceeded all expectations",
                    f"Brilliant work - highly recommend {book.title}"
                ]
            elif rating >= 3:
                titles = [
                    f"Good read - {book.title}",
                    f"Solid book - {book.title}",
                    f"{book.title} was enjoyable",
                    f"Worth reading - {book.title}"
                ]
            else:
                titles = [
                    f"Disappointed by {book.title}",
                    f"{book.title} didn't work for me",
                    f"Not my cup of tea - {book.title}",
                    f"Mixed feelings about {book.title}"
                ]

            title = random.choice(titles)
            content = self.get_book_character_content(book.title)
            content += f" {self.fake.text(max_nb_chars=250)}"

            # Find associated reading session if available
            reading_session = ReadingSession.objects.filter(book=book).first()
            
            # Create review with believable timeline
            if reading_session:
                created_time = self.fake.date_time_between(
                    start_date=reading_session.start_date,
                    end_date=timezone.now().date(),
                    tzinfo=timezone.utc
                )
            else:
                created_time = self.fake.date_time_between(
                    start_date='-1y',
                    end_date='now',
                    tzinfo=timezone.utc
                )

            Review.objects.create(
                user=user,
                book=book,
                rating=rating,
                title=title,
                content=content,
                is_spoiler=random.choice([True, False]) if random.random() < 0.25 else False,
                reading_session=reading_session,
                created_at=created_time,
                updated_at=created_time
            )
            
            created_reviews += 1

    def create_reading_progress(self, num_progress):
        """Create reading progress snapshots for active readers"""
        self.stdout.write(f'Creating {num_progress} reading progress entries...')
        
        active_sessions = ReadingSession.objects.filter(
            status__in=['current', 'upcoming']
        )
        
        if not active_sessions:
            self.stdout.write(self.style.WARNING('No active reading sessions found.'))
            return

        created_progress = 0
        
        for session in active_sessions:
            club_members = list(session.book_club.members.all())
            
            # Select random subset of members to have progress
            if len(club_members) < 3:
                active_readers = club_members
            else:
                active_readers = random.sample(
                    club_members, 
                    random.randint(min(3, len(club_members)), len(club_members))
                )
            
            for user in active_readers:
                if created_progress >= num_progress:
                    break
                    
                # Generate realistic progress
                if session.book.page_count:
                    if session.status == 'current':
                        # Current sessions should have varied progress
                        max_page = min(
                            session.book.page_count,
                            int(session.book.page_count * random.uniform(0.1, 0.9))
                        )
                        current_page = random.randint(0, max_page)
                    else:  # upcoming
                        # Upcoming sessions might have some early readers
                        current_page = random.randint(0, min(50, session.book.page_count // 4))
                else:
                    current_page = random.randint(0, 200)
                
                is_finished = current_page == session.book.page_count if session.book.page_count else False
                
                # Generate timeline
                if session.status == 'current':
                    started_at = self.fake.date_time_between(
                        start_date=session.start_date,
                        end_date=timezone.now(),
                        tzinfo=timezone.utc
                    )
                    updated_at = self.fake.date_time_between(
                        start_date=started_at,
                        end_date=timezone.now(),
                        tzinfo=timezone.utc
                    )
                else:  # upcoming
                    started_at = None if current_page == 0 else self.fake.date_time_between(
                        start_date=max(session.start_date - timedelta(days=7), timezone.now().date() - timedelta(days=30)),
                        end_date=timezone.now(),
                        tzinfo=timezone.utc
                    )
                    updated_at = timezone.now()

                finished_at = updated_at if is_finished else None

                # Check if progress already exists for this user, book, and session
                if not ReadingProgress.objects.filter(
                    user=user, 
                    book=session.book, 
                    reading_session=session
                ).exists():
                    ReadingProgress.objects.create(
                        user=user,
                        book=session.book,
                        reading_session=session,
                        current_page=current_page,
                        is_finished=is_finished,
                        started_at=started_at,
                        finished_at=finished_at,
                        notes=self.fake.text(max_nb_chars=100) if random.random() < 0.3 else None,
                        updated_at=updated_at
                    )
                else:
                    continue  # Skip if progress already exists
                
                created_progress += 1

    def create_recommendations(self):
        """Create book recommendations using collaborative filtering placeholder"""
        self.stdout.write('Creating book recommendations...')
        
        users = list(User.objects.all())
        books = list(Book.objects.all())
        book_clubs = list(BookClub.objects.all())
        
        if not all([users, books, book_clubs]):
            self.stdout.write(self.style.WARNING('Insufficient data for recommendations.'))
            return

        # Simple collaborative filtering: users who liked X also liked Y
        user_book_ratings = {}
        
        # Build user-book rating matrix from existing reviews
        for review in Review.objects.select_related('user', 'book'):
            if review.user.id not in user_book_ratings:
                user_book_ratings[review.user.id] = {}
            user_book_ratings[review.user.id][review.book.id] = review.rating

        # Create recommendations based on similar user preferences
        for club in book_clubs:
            club_members = list(club.members.all())
            available_books = [b for b in books if not club.reading_sessions.filter(book=b).exists()]
            
            # Create 2-5 recommendations per club
            for _ in range(random.randint(2, 5)):
                if not available_books:
                    break
                    
                book = random.choice(available_books)
                available_books.remove(book)  # Avoid duplicates
                
                recommender = random.choice(club_members)
                
                # Generate recommendation reason based on collaborative filtering
                similar_books = []
                if recommender.id in user_book_ratings:
                    user_ratings = user_book_ratings[recommender.id]
                    high_rated_books = [book_id for book_id, rating in user_ratings.items() if rating >= 4]
                    
                    if high_rated_books:
                        similar_book_id = random.choice(high_rated_books)
                        try:
                            similar_book = Book.objects.get(id=similar_book_id)
                            reason = f"If you enjoyed {similar_book.title}, you'll love this one! {self.fake.text(max_nb_chars=100)}"
                        except Book.DoesNotExist:
                            reason = f"This book has themes similar to others our club has enjoyed. {self.fake.text(max_nb_chars=100)}"
                    else:
                        reason = f"This looks like a great fit for our club's interests. {self.fake.text(max_nb_chars=100)}"
                else:
                    reason = f"I think this would be perfect for our next read! {self.fake.text(max_nb_chars=100)}"

                status_choices = ['pending', 'approved', 'rejected', 'selected']
                status_weights = [0.4, 0.3, 0.1, 0.2]
                status = random.choices(status_choices, weights=status_weights)[0]
                
                # Generate realistic vote counts
                total_members = len(club_members)
                if total_members <= 2:
                    # Small clubs - simple voting
                    votes_for = random.randint(0, total_members)
                    votes_against = random.randint(0, total_members - votes_for)
                else:
                    if status == 'approved' or status == 'selected':
                        votes_for = random.randint(max(1, total_members // 3), total_members - 1)
                        votes_against = random.randint(0, total_members // 4)
                    elif status == 'rejected':
                        votes_for = random.randint(0, total_members // 4)
                        votes_against = random.randint(max(1, total_members // 3), total_members - 1)
                    else:  # pending
                        votes_for = random.randint(0, total_members // 2)
                        votes_against = random.randint(0, total_members // 3)

                created_time = self.fake.date_time_between(
                    start_date='-60d',
                    end_date='now',
                    tzinfo=timezone.utc
                )

                try:
                    BookRecommendation.objects.create(
                        book_club=club,
                        book=book,
                        recommended_by=recommender,
                        reason=reason,
                        status=status,
                        votes_for=votes_for,
                        votes_against=votes_against,
                        created_at=created_time,
                        updated_at=created_time
                    )
                except Exception as e:
                    # Skip if recommendation already exists
                    continue

        self.stdout.write(f'Created recommendations with collaborative filtering logic.')
