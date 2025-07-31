import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

from myapp.models import (
    Author, Genre, Book, BookClub, UserProfile, 
    Membership, ReadingSession, Discussion, Review, 
    ReadingProgress, BookRecommendation
)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Faker('user_name')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Faker('email')
    is_active = True
    is_staff = False
    is_superuser = False
    date_joined = Faker('date_time_this_year', tzinfo=timezone.utc)


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = SubFactory(UserFactory)
    bio = Faker('text', max_nb_chars=200)
    location = Faker('city')
    website = Faker('url')
    image_url = Faker('image_url')
    image_updated_at = Faker('date_time_this_month', tzinfo=timezone.utc)


class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author

    first_name = Faker('first_name')
    last_name = Faker('last_name')
    bio = Faker('text', max_nb_chars=300)
    birth_date = Faker('date_of_birth', minimum_age=30, maximum_age=100)
    website = Faker('url')


class GenreFactory(DjangoModelFactory):
    class Meta:
        model = Genre

    name = Faker('word')
    description = Faker('text', max_nb_chars=200)


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book

    title = Faker('sentence', nb_words=3)
    subtitle = Faker('sentence', nb_words=4)
    isbn = Faker('isbn13')
    isbn_10 = Faker('isbn10')
    description = Faker('text', max_nb_chars=500)
    publication_date = Faker('date_this_decade')
    publisher = Faker('company')
    page_count = Faker('random_int', min=100, max=800)
    language = 'English'
    image_url = Faker('image_url')
    image_updated_at = Faker('date_time_this_month', tzinfo=timezone.utc)
    external_id = Faker('uuid4')
    source = 'openlibrary'

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for author in extracted:
                self.authors.add(author)
        else:
            # Create a default author
            author = AuthorFactory()
            self.authors.add(author)

    @factory.post_generation
    def genres(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for genre in extracted:
                self.genres.add(genre)
        else:
            # Create 1-3 default genres
            for _ in range(factory.Faker('random_int', min=1, max=3).generate()):
                genre = GenreFactory()
                self.genres.add(genre)


class BookClubFactory(DjangoModelFactory):
    class Meta:
        model = BookClub

    name = Faker('sentence', nb_words=3)
    description = Faker('text', max_nb_chars=400)
    creator = SubFactory(UserFactory)
    image_url = Faker('image_url')
    image_updated_at = Faker('date_time_this_month', tzinfo=timezone.utc)
    category = Faker('random_element', elements=('Fiction', 'Mystery', 'Romance', 'Science Fiction', 'Fantasy'))
    is_private = Faker('boolean', chance_of_getting_true=30)
    max_members = Faker('random_int', min=10, max=100)
    location = Faker('city')
    meeting_frequency = Faker('random_element', elements=('Weekly', 'Bi-weekly', 'Monthly'))
    external_id = Faker('uuid4')
    source = 'manual'

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                MembershipFactory(user=user, book_club=self)
        else:
            # Create 3-8 default members
            for _ in range(factory.Faker('random_int', min=3, max=8).generate()):
                MembershipFactory(book_club=self)


class MembershipFactory(DjangoModelFactory):
    class Meta:
        model = Membership

    user = SubFactory(UserFactory)
    book_club = SubFactory(BookClubFactory)
    role = Faker('random_element', elements=('member', 'moderator', 'admin'))
    joined_at = Faker('date_time_this_year', tzinfo=timezone.utc)


class ReadingSessionFactory(DjangoModelFactory):
    class Meta:
        model = ReadingSession

    book_club = SubFactory(BookClubFactory)
    book = SubFactory(BookFactory)
    start_date = Faker('date_this_month')
    end_date = LazyAttribute(lambda obj: obj.start_date + timezone.timedelta(days=30))
    status = Faker('random_element', elements=('upcoming', 'current', 'completed'))
    meeting_date = LazyAttribute(lambda obj: obj.end_date + timezone.timedelta(days=7))
    meeting_location = Faker('address')
    meeting_notes = Faker('text', max_nb_chars=300)


class DiscussionFactory(DjangoModelFactory):
    class Meta:
        model = Discussion

    book_club = SubFactory(BookClubFactory)
    book = SubFactory(BookFactory)
    reading_session = SubFactory(ReadingSessionFactory)
    author = SubFactory(UserFactory)
    title = Faker('sentence', nb_words=5)
    content = Faker('text', max_nb_chars=500)
    discussion_type = Faker('random_element', elements=('general', 'chapter', 'review', 'meeting'))
    chapter_number = Faker('random_int', min=1, max=20)
    is_pinned = Faker('boolean', chance_of_getting_true=10)
    is_spoiler = Faker('boolean', chance_of_getting_true=30)


class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review

    user = SubFactory(UserFactory)
    book = SubFactory(BookFactory)
    rating = Faker('random_int', min=1, max=5)
    title = Faker('sentence', nb_words=4)
    content = Faker('text', max_nb_chars=400)
    is_spoiler = Faker('boolean', chance_of_getting_true=25)
    reading_session = SubFactory(ReadingSessionFactory)


class ReadingProgressFactory(DjangoModelFactory):
    class Meta:
        model = ReadingProgress

    user = SubFactory(UserFactory)
    book = SubFactory(BookFactory)
    reading_session = SubFactory(ReadingSessionFactory)
    current_page = Faker('random_int', min=0, max=400)
    is_finished = Faker('boolean', chance_of_getting_true=60)
    started_at = Faker('date_time_this_month', tzinfo=timezone.utc)
    finished_at = LazyAttribute(
        lambda obj: obj.started_at + timezone.timedelta(days=30) if obj.is_finished else None
    )
    notes = Faker('text', max_nb_chars=200)


class BookRecommendationFactory(DjangoModelFactory):
    class Meta:
        model = BookRecommendation

    book_club = SubFactory(BookClubFactory)
    book = SubFactory(BookFactory)
    recommended_by = SubFactory(UserFactory)
    reason = Faker('text', max_nb_chars=300)
    status = Faker('random_element', elements=('pending', 'approved', 'rejected', 'selected'))
    votes_for = Faker('random_int', min=0, max=20)
    votes_against = Faker('random_int', min=0, max=10)
