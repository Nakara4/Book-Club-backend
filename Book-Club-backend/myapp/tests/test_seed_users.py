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

from myapp.models import UserProfile, Book, BookClub, Membership, ReadingProgress, Review
from myapp.management.commands.seed_users import Command
from myapp.tests.factories import BookFactory, BookClubFactory, UserFactory


@pytest.mark.django_db
class TestSeedUsersCommand:
    """Unit tests for seed_users management command"""

    def test_command_help(self):
        """Test that command help is available"""
        cmd = Command()
        assert 'Seed the database with realistic user profiles' in cmd.help

    @patch('myapp.management.commands.seed_users.Faker')
    def test_generate_diverse_bio(self, mock_faker):
        """Test bio generation diversity"""
        mock_faker_instance = Mock()
        mock_faker_instance.city.return_value = "New York"
        mock_faker_instance.job.return_value = "Developer"
        mock_faker_instance.sentence.return_value = "Test sentence."
        mock_faker.return_value = mock_faker_instance

        cmd = Command()
        bio = cmd.generate_diverse_bio(mock_faker_instance)
        
        assert isinstance(bio, str)
        assert len(bio) > 0

    def test_safe_int_conversion(self):
        """Test safe integer conversion utility"""
        cmd = Command()
        
        assert cmd.safe_int('5') == 5
        assert cmd.safe_int('') == 0
        assert cmd.safe_int(None) == 0
        assert cmd.safe_int('invalid') == 0
        assert cmd.safe_int('10', default=5) == 10

    def test_load_goodreads_csv_valid(self):
        """Test loading valid Goodreads CSV data"""
        csv_content = '''Title,Author,My Rating,Date Read,Bookshelves
"The Great Gatsby","F. Scott Fitzgerald",5,"2023/01/15","read,favorites"
"1984","George Orwell",4,"2023/02/20","read,dystopian"'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            cmd = Command()
            result = cmd.load_goodreads_csv(f.name)
            
            assert result is not None
            assert len(result) == 2
            assert result[0]['title'] == 'The Great Gatsby'
            assert result[0]['author'] == 'F. Scott Fitzgerald'
            assert result[0]['rating'] == 5
            assert result[1]['title'] == '1984'
            assert result[1]['rating'] == 4

            Path(f.name).unlink()

    def test_load_goodreads_csv_missing_file(self):
        """Test handling of missing Goodreads CSV file"""
        cmd = Command()
        result = cmd.load_goodreads_csv('/nonexistent/file.csv')
        assert result is None

    def test_clear_data_functionality(self):
        """Test data clearing functionality"""
        # Create test data
        user = UserFactory()
        UserProfile.objects.create(user=user, bio="Test bio")
        book = BookFactory()
        ReadingProgress.objects.create(user=user, book=book, current_page=100)
        Review.objects.create(user=user, book=book, rating=5, title="Great!", content="Loved it")
        
        cmd = Command()
        initial_users = User.objects.filter(is_superuser=False).count()
        
        cmd.clear_data()
        
        # Verify data was cleared
        assert UserProfile.objects.count() == 0
        assert ReadingProgress.objects.count() == 0
        assert Review.objects.count() == 0
        assert Membership.objects.count() == 0
        assert User.objects.filter(is_superuser=False).count() == 0


@pytest.mark.django_db 
class TestSeedUsersIntegration:
    """Integration tests for seed_users command"""

    def test_seed_users_batch_creation(self):
        """Test batch user creation"""
        cmd = Command()
        
        initial_count = User.objects.count()
        
        # Create small batch for testing
        with patch('myapp.management.commands.seed_users.tqdm') as mock_tqdm:
            mock_progress = Mock()
            mock_tqdm.return_value.__enter__.return_value = mock_progress
            
            result = cmd.seed_users_batch(3, None, mock_progress, dry_run=False)
            
            assert result['created'] == 3
            assert result['errors'] == 0
            assert User.objects.count() == initial_count + 3
            
            # Verify user profiles were created
            assert UserProfile.objects.count() >= 3

    def test_assign_reading_history(self):
        """Test reading history assignment"""
        # Create test data
        user = UserFactory()
        books = [BookFactory() for _ in range(3)]
        
        cmd = Command()
        
        with patch('myapp.management.commands.seed_users.Faker') as mock_faker_class:
            mock_faker = Mock()
            mock_faker.date_time_between.return_value = timezone.now()
            mock_faker.sentence.return_value = "Test note"
            mock_faker.text.return_value = "Test review content"
            mock_faker_class.return_value = mock_faker
            
            cmd.assign_reading_history(user, None, mock_faker)
            
            # Verify reading progress was created
            assert ReadingProgress.objects.filter(user=user).count() > 0

    def test_assign_book_club_role(self):
        """Test book club role assignment"""
        user = UserFactory()
        clubs = [BookClubFactory() for _ in range(2)]
        
        cmd = Command()
        
        with patch('myapp.management.commands.seed_users.Faker') as mock_faker_class:
            mock_faker = Mock()
            mock_faker.catch_phrase.return_value = "Amazing"
            mock_faker.text.return_value = "Test description"
            mock_faker.city.return_value = "Test City"
            mock_faker.date_time_between.return_value = timezone.now()
            mock_faker_class.return_value = mock_faker
            
            cmd.assign_book_club_role(user, mock_faker)
            
            # User should be assigned to at least one club
            assert Membership.objects.filter(user=user).count() > 0

    def test_dry_run_mode(self):
        """Test dry run mode doesn't create records"""
        cmd = Command()
        initial_count = User.objects.count()
        
        with patch('myapp.management.commands.seed_users.tqdm') as mock_tqdm:
            mock_progress = Mock()
            mock_tqdm.return_value.__enter__.return_value = mock_progress
            
            result = cmd.seed_users_batch(2, None, mock_progress, dry_run=True)
            
            assert result['created'] == 2
            assert User.objects.count() == initial_count  # No actual users created

    @patch('myapp.management.commands.seed_users.random.choice')
    def test_diverse_user_creation(self, mock_choice):
        """Test creation of diverse users"""
        # Mock random choices to ensure diversity
        mock_choice.side_effect = lambda x: x[0]  # Always pick first option
        
        cmd = Command()
        
        with patch('myapp.management.commands.seed_users.tqdm') as mock_tqdm:
            mock_progress = Mock()
            mock_tqdm.return_value.__enter__.return_value = mock_progress
            
            result = cmd.seed_users_batch(1, None, mock_progress, dry_run=False)
            
            assert result['created'] == 1
            user = User.objects.last()
            profile = UserProfile.objects.get(user=user)
            
            assert user.first_name
            assert user.last_name
            assert user.email
            assert profile.bio
            assert profile.location


class TestSeedUsersCommandIntegration(TestCase):
    """Django TestCase for seed_users command integration tests"""
    
    def setUp(self):
        # Clear existing data
        User.objects.filter(is_superuser=False).delete()
        UserProfile.objects.all().delete()
        
    def test_full_command_execution(self):
        """Test complete command execution"""
        initial_count = User.objects.count()
        
        # Create some books and clubs for relationships
        BookFactory.create_batch(5)
        BookClubFactory.create_batch(3)
        
        out = StringIO()
        call_command('seed_users', '--count', '5', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('DRY RUN MODE', output)
        self.assertIn('Seeding 5 realistic users', output)
        
        # Should not have created actual users in dry run
        self.assertEqual(User.objects.count(), initial_count)

    def test_command_with_clear_flag(self):
        """Test command with clear flag"""
        # Create some test data
        user = UserFactory()
        UserProfile.objects.create(user=user, bio="Test")
        
        initial_count = User.objects.count()
        
        out = StringIO()
        call_command('seed_users', '--count', '2', '--clear', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Would clear existing user data', output)

    def test_command_with_goodreads_csv(self):
        """Test command with Goodreads CSV file"""
        # Create test CSV
        csv_content = '''Title,Author,My Rating,Date Read,Bookshelves
"Test Book","Test Author",5,"2023/01/15","read"'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            try:
                # Create a book that matches the CSV
                BookFactory(title__icontains="Test Book")
                
                out = StringIO()
                call_command(
                    'seed_users', 
                    '--count', '2', 
                    '--goodreads-csv', f.name,
                    '--dry-run',
                    stdout=out
                )
                
                output = out.getvalue()
                self.assertIn('Loaded 1 books from Goodreads CSV', output)
                
            finally:
                Path(f.name).unlink()

    def test_batch_processing(self):
        """Test batch processing functionality"""
        out = StringIO()
        call_command(
            'seed_users', 
            '--count', '10', 
            '--batch-size', '3',
            '--dry-run',
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn('Seeding 10 realistic users', output)
        # Should process in batches of 3

    def test_username_uniqueness_handling(self):
        """Test handling of username uniqueness conflicts"""
        # Create a user with a common username pattern
        UserFactory(username='testuser')
        
        cmd = Command()
        
        with patch('myapp.management.commands.seed_users.Faker') as mock_faker_class:
            mock_faker = Mock()
            # First few attempts return existing username
            mock_faker.unique.user_name.side_effect = [
                'testuser',  # Conflict
                'testuser2',  # Success
            ]
            mock_faker.unique.email.return_value = 'test@example.com'
            mock_faker.user_name.return_value = 'fallback_user'
            mock_faker.domain_name.return_value = 'example.com'
            mock_faker.random_int.return_value = 1234
            mock_faker_class.return_value = mock_faker
            
            # Mock other faker methods
            mock_faker.first_name.return_value = 'Test'
            mock_faker.last_name.return_value = 'User'
            mock_faker.date_time_between.return_value = timezone.now()
            mock_faker.country.return_value = 'Test Country'
            mock_faker.url.return_value = 'http://test.com'
            
            with patch('myapp.management.commands.seed_users.tqdm') as mock_tqdm:
                mock_progress = Mock()
                mock_tqdm.return_value.__enter__.return_value = mock_progress
                
                result = cmd.seed_users_batch(1, None, mock_progress, dry_run=False)
                
                self.assertEqual(result['created'], 1)
                # Should have created user with unique username
                self.assertTrue(User.objects.filter(username='testuser2').exists())
