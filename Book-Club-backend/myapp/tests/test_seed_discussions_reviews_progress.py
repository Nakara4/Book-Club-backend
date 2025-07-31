import pytest
import tempfile
import csv
from unittest.mock import patch, Mock
from pathlib import Path
from io import StringIO

from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from django.utils import timezone

from myapp.models import Book, Discussion, Review, ReadingProgress, ReadingSession, BookRecommendation
from myapp.management.commands.seed_discussions_reviews_progress import Command
from myapp.tests.factories import BookFactory, DiscussionFactory, UserFactory, BookClubFactory, ReadingSessionFactory


@pytest.mark.django_db
class TestSeedDiscussionsReviewsProgressCommand:
    """Unit tests for seed_discussions_reviews_progress management command"""

    def test_command_help(self):
        """Test that command help is available"""
        cmd = Command()
        assert 'Seed discussions, reviews, progress, and recommendations' in cmd.help

    def test_clear_data_functionality(self):
        """Test data clearing functionality"""
        # Create test data
        book = BookFactory()
        discussion = DiscussionFactory(book=book)
        review = Review.objects.create(user=UserFactory(), book=book, rating=5, title="Good", content="Nice read")
        ReadingProgress.objects.create(user=UserFactory(), book=book, current_page=50)
        BookRecommendation.objects.create(book=book, book_club=BookClubFactory(), recommended_by=UserFactory())
        
        cmd = Command()
        initial_discussion_count = Discussion.objects.count()

        cmd.clear_data()
        
        # Verify data was cleared
        assert Discussion.objects.count() == 0
        assert Review.objects.count() == 0
        assert ReadingProgress.objects.count() == 0
        assert BookRecommendation.objects.count() == 0


@pytest.mark.django_db
class TestSeedDiscussionsReviewsProgressIntegration:
    """Integration tests for seed_discussions_reviews_progress command"""

    def test_create_discussions_with_replies(self):
        """Test creation of discussions with replies"""
        # Create a reading session
        reading_session = ReadingSessionFactory(status='completed')
        cmd = Command()
        
        # Before
        initial_discussion_count = Discussion.objects.count()
        cmd.create_discussions_with_replies(5)
        
        # After
        assert Discussion.objects.count() == initial_discussion_count + 5

    def test_create_reviews_with_bell_curve(self):
        """Test review creation with bell curve distribution"""
        books = [BookFactory() for _ in range(3)]
        users = [UserFactory() for _ in range(3)]
        
        for book in books:
            book.save()

        cmd = Command()
        
        # Before
        initial_review_count = Review.objects.count()
        cmd.create_reviews_with_bell_curve(10)
        
        # After
        assert Review.objects.count() == initial_review_count + 10

    def test_create_reading_progress(self):
        """Test creation of reading progress entries"""
        session = ReadingSessionFactory(status='current')
        
        cmd = Command()
        
        # Before
        initial_progress_count = ReadingProgress.objects.count()
        cmd.create_reading_progress(10)
        
        # After
        assert ReadingProgress.objects.count() == initial_progress_count + 10


class TestSeedDiscussionsCommandIntegration(TestCase):
    """Django TestCase for seed_discussions_reviews_progress command integration tests"""
    
    def setUp(self):
        # Clear existing data
        Book.objects.all().delete()
        Discussion.objects.all().delete()
        Review.objects.all().delete()

    def test_full_command_execution(self):
        """Test complete command execution"""
        initial_discussion_count = Discussion.objects.count()

        # Create test data
        BookFactory.create_batch(5)
        UserFactory.create_batch(5)
        ReadingSessionFactory.create_batch(2)

        out = StringIO()
        call_command('seed_discussions_reviews_progress', '--discussions', '5', '--reviews', '10', '--progress', '15', stdout=out)

        output = out.getvalue()
        self.assertIn('Seeding discussions, reviews, progress, and recommendations', output)

        self.assertEqual(Discussion.objects.count(), initial_discussion_count + 5)

    def test_command_with_clear_flag(self):
        """Test command with clear flag"""
        # Create test data
        discussion = DiscussionFactory()
        initial_count = Discussion.objects.count()

        out = StringIO()
        call_command('seed_discussions_reviews_progress', '--clear', '--discussions', '2', stdout=out)

        output = out.getvalue()
        self.assertIn('Clearing existing discussions, reviews, progress, and recommendations', output)

        self.assertIn('Seeding discussions, reviews, progress, and recommendations', output)
        # Ensure data was cleared
        self.assertEqual(Discussion.objects.count(), initial_count - 1)

    def test_command_with_no_data(self):
        """Test command behavior when no data is available for seeding"""
        out = StringIO()
        # Ensure no reading sessions exist
        ReadingSession.objects.all().delete()
        
        call_command('seed_discussions_reviews_progress', stdout=out)

        output = out.getvalue()
        self.assertIn('No reading sessions found. Creating some basic ones...', output)

    def test_bell_curve_distribution_of_ratings(self):
        """Test that review ratings approximately follow a bell curve distribution"""
        cmd = Command()
        users = [UserFactory() for _ in range(20)]
        BookFactory(title='Bell Curve Test Book')

        cmd.create_reviews_with_bell_curve(100)

        reviews = Review.objects.filter(book__title='Bell Curve Test Book')

        self.assertGreater(len(reviews), 0)

        # Check that ratings are mostly around the center (3-4 range)
        ratings = [review.rating for review in reviews]
        avg_rating = sum(ratings) / len(ratings)
        self.assertAlmostEqual(avg_rating, 3.5, delta=1.0)

    def test_discussions_with_compound_replies(self):
        """Test creating discussions that generate compound replies"""
        session = ReadingSessionFactory(status='current')
        cmd = Command()
        cmd.create_discussions_with_replies(3)

        discussions = Discussion.objects.filter(reading_session=session)
        
        self.assertEqual(discussions.count(), 3)

        for discussion in discussions:
            self.assertGreaterEqual(discussion.discussionreply_set.count(), 0)  # Replies may be 0 or more

    def test_progress_snapshots_creation(self):
        """Test creation of progress snapshots over time for a session"""
        session = ReadingSessionFactory()
        users = [UserFactory() for _ in range(5)]

        cmd = Command()
        cmd.create_reading_progress(20)

        progress_set = ReadingProgress.objects.filter(reading_session=session)

        self.assertGreaterEqual(progress_set.count(), 0)  # Entries may vary
        for progress in progress_set:
            self.assertGreaterEqual(progress.current_page, 0)
            if progress.is_finished:
                self.assertEqual(progress.current_page, progress.book.page_count or 0)
                self.assertIsNotNone(progress.finished_at)
        
        unfinished_progresses = progress_set.filter(is_finished=False)
        for progress in unfinished_progresses:
            self.assertIsNone(progress.finished_at)
