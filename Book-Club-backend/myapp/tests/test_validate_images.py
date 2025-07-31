import pytest
from unittest.mock import patch, Mock
from io import StringIO

from django.core.management import call_command
from django.utils import timezone
from django.test import TestCase

from myapp.models import Book, BookClub, UserProfile
from myapp.management.commands.validate_images import Command
from myapp.tests.factories import BookFactory, BookClubFactory, UserProfileFactory


@pytest.mark.django_db
class TestValidateImagesCommand:
    """Unit tests for validate_images management command"""

    def test_command_help(self):
        """Test that command help is available"""
        cmd = Command()
        assert 'Validate all stored image URLs and replace 404s with placeholders' in cmd.help

    def test_is_placeholder_url(self):
        """Test placeholder URL detection"""
        cmd = Command()
        
        # Test placeholder URLs
        assert cmd._is_placeholder_url('https://source.unsplash.com/300x450/?book')
        assert cmd._is_placeholder_url('https://api.dicebear.com/7.x/avataaars/svg?seed=test')
        assert cmd._is_placeholder_url('https://via.placeholder.com/300x400')
        
        # Test non-placeholder URLs
        assert not cmd._is_placeholder_url('https://example.com/image.jpg')
        assert not cmd._is_placeholder_url('https://covers.openlibrary.org/b/isbn/123-L.jpg')

    @patch('myapp.management.commands.validate_images.validate_url')
    def test_validate_single_url(self, mock_validate_url):
        """Test single URL validation"""
        cmd = Command()
        
        # Test valid URL
        mock_validate_url.return_value = True
        result = cmd._validate_single_url('https://example.com/valid.jpg')
        assert result is True
        
        # Test invalid URL
        mock_validate_url.return_value = False
        result = cmd._validate_single_url('https://example.com/404.jpg')
        assert result is False
        
        # Test exception handling
        mock_validate_url.side_effect = Exception('Network error')
        result = cmd._validate_single_url('https://example.com/error.jpg')
        assert result is False

    def test_validate_book_images_no_books(self):
        """Test book image validation when no books need validation"""
        cmd = Command()
        
        # No books with image URLs
        result = cmd.validate_book_images(dry_run=False, batch_size=10, max_workers=1, force=False)
        
        assert result['validated'] == 0
        assert result['updated'] == 0
        assert result['errors'] == 0

    def test_validate_bookclub_images_no_clubs(self):
        """Test book club image validation when no clubs need validation"""
        cmd = Command()
        
        # No book clubs with image URLs
        result = cmd.validate_bookclub_images(dry_run=False, batch_size=10, max_workers=1, force=False)
        
        assert result['validated'] == 0
        assert result['updated'] == 0
        assert result['errors'] == 0

    def test_validate_user_images_no_users(self):
        """Test user image validation when no users need validation"""
        cmd = Command()
        
        # No user profiles with image URLs
        result = cmd.validate_user_images(dry_run=False, batch_size=10, max_workers=1, force=False)
        
        assert result['validated'] == 0
        assert result['updated'] == 0
        assert result['errors'] == 0


@pytest.mark.django_db
@pytest.mark.slow  # Mark as slow since it involves network operations
class TestValidateImagesIntegration:
    """Integration tests for validate_images command"""

    def test_validate_book_images_with_valid_urls(self):
        """Test validating books with valid image URLs"""
        # Create books with image URLs
        book1 = BookFactory(image_url='https://example.com/book1.jpg')
        book2 = BookFactory(image_url='https://example.com/book2.jpg')
        
        cmd = Command()
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            mock_validate.return_value = True  # All URLs are valid
            
            result = cmd.validate_book_images(dry_run=False, batch_size=10, max_workers=1, force=True)
            
            assert result['validated'] == 2
            assert result['updated'] == 0  # No invalid URLs to update
            assert result['errors'] == 0

    def test_validate_book_images_with_invalid_urls(self):
        """Test validating books with invalid image URLs"""
        # Create books with invalid image URLs
        book1 = BookFactory(image_url='https://example.com/404.jpg')
        book2 = BookFactory(image_url='https://example.com/broken.jpg')
        
        cmd = Command()
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            mock_validate.return_value = False  # All URLs are invalid
            
            with patch('library.images.get_placeholder') as mock_placeholder:
                mock_placeholder.return_value = 'https://source.unsplash.com/300x450/?book'
                
                result = cmd.validate_book_images(dry_run=False, batch_size=10, max_workers=1, force=True)
                
                assert result['validated'] == 2
                assert result['updated'] == 2  # Both URLs were invalid and updated
                assert result['errors'] == 0
                
                # Verify books were updated with placeholder URLs
                book1.refresh_from_db()
                book2.refresh_from_db()
                assert book1.image_url == 'https://source.unsplash.com/300x450/?book'
                assert book2.image_url == 'https://source.unsplash.com/300x450/?book'
                assert book1.image_updated_at is not None
                assert book2.image_updated_at is not None

    def test_validate_bookclub_images_with_mixed_validity(self):
        """Test validating book clubs with mixed valid/invalid URLs"""
        # Create book clubs with different URL validity
        club1 = BookClubFactory(image_url='https://example.com/valid.jpg')
        club2 = BookClubFactory(image_url='https://example.com/invalid.jpg')
        
        cmd = Command()
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            # First URL valid, second invalid
            mock_validate.side_effect = [True, False]
            
            with patch('library.images.get_placeholder') as mock_placeholder:
                mock_placeholder.return_value = 'https://source.unsplash.com/400x600/?book'
                
                result = cmd.validate_bookclub_images(dry_run=False, batch_size=10, max_workers=1, force=True)
                
                assert result['validated'] == 2
                assert result['updated'] == 1  # Only one URL was invalid
                assert result['errors'] == 0

    def test_validate_user_images_dry_run(self):
        """Test validating user images in dry run mode"""
        # Create user profiles with invalid URLs
        profile1 = UserProfileFactory(image_url='https://example.com/404.jpg')
        profile2 = UserProfileFactory(image_url='https://example.com/broken.jpg')
        
        cmd = Command()
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            mock_validate.return_value = False  # All URLs are invalid
            
            result = cmd.validate_user_images(dry_run=True, batch_size=10, max_workers=1, force=True)
            
            assert result['validated'] == 2
            assert result['updated'] == 2  # Would have updated both
            assert result['errors'] == 0
            
            # Verify profiles were NOT actually updated (dry run)
            profile1.refresh_from_db()
            profile2.refresh_from_db()
            assert profile1.image_url == 'https://example.com/404.jpg'  # Unchanged
            assert profile2.image_url == 'https://example.com/broken.jpg'  # Unchanged

    def test_force_validation_vs_normal(self):
        """Test difference between forced validation and normal validation"""
        # Create book with recently updated image
        recent_time = timezone.now() - timezone.timedelta(days=1)  # 1 day ago
        book = BookFactory(
            image_url='https://example.com/recent.jpg',
            image_updated_at=recent_time
        )
        
        cmd = Command()
        
        # Normal validation (should skip recently updated)
        result1 = cmd.validate_book_images(dry_run=True, batch_size=10, max_workers=1, force=False)
        assert result1['validated'] == 0  # Skipped due to recent update
        
        # Forced validation (should validate even recently updated)
        result2 = cmd.validate_book_images(dry_run=True, batch_size=10, max_workers=1, force=True)
        assert result2['validated'] == 1  # Validated despite recent update

    @patch('myapp.management.commands.validate_images.validate_url')
    def test_validation_error_handling(self, mock_validate_url):
        """Test error handling during validation"""
        # Create book with image URL
        book = BookFactory(image_url='https://example.com/test.jpg')
        
        # Mock validation to raise exception
        mock_validate_url.side_effect = Exception('Network timeout')
        
        cmd = Command()
        result = cmd.validate_book_images(dry_run=False, batch_size=10, max_workers=1, force=True)
        
        assert result['validated'] == 1
        assert result['updated'] == 0
        assert result['errors'] == 1  # Error was caught and counted


class TestValidateImagesCommandIntegration(TestCase):
    """Django TestCase for validate_images command integration tests"""
    
    def setUp(self):
        # Clear existing data
        Book.objects.all().delete()
        BookClub.objects.all().delete()
        UserProfile.objects.all().delete()

    def test_full_command_execution(self):
        """Test complete command execution"""
        # Create test data with image URLs
        BookFactory.create_batch(3, image_url='https://example.com/book.jpg')
        BookClubFactory.create_batch(2, image_url='https://example.com/club.jpg')
        UserProfileFactory.create_batch(2, image_url='https://example.com/user.jpg')
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            mock_validate.return_value = True  # All URLs valid
            
            out = StringIO()
            call_command('validate_images', '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('Starting image URL validation', output)
            self.assertIn('DRY RUN MODE', output)
            self.assertIn('Image validation completed', output)

    def test_command_with_specific_models(self):
        """Test command targeting specific models"""
        # Create test data
        BookFactory(image_url='https://example.com/book.jpg')
        BookClubFactory(image_url='https://example.com/club.jpg')
        UserProfileFactory(image_url='https://example.com/user.jpg')
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            mock_validate.return_value = True
            
            out = StringIO()
            call_command('validate_images', '--models', 'books', '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('Models to validate: books', output)
            self.assertIn('Validating book cover images', output)
            # Should not validate other models
            self.assertNotIn('Validating book club images', output)
            self.assertNotIn('Validating user profile images', output)

    def test_command_with_custom_batch_size(self):
        """Test command with custom batch size"""
        BookFactory.create_batch(10, image_url='https://example.com/book.jpg')
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            mock_validate.return_value = True
            
            out = StringIO()
            call_command('validate_images', '--batch-size', '5', '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('Batch size: 5', output)

    def test_command_with_force_flag(self):
        """Test command with force flag"""
        # Create book with recent image update
        recent_time = timezone.now() - timezone.timedelta(hours=1)
        BookFactory(
            image_url='https://example.com/book.jpg',
            image_updated_at=recent_time
        )
        
        with patch('myapp.management.commands.validate_images.validate_url') as mock_validate:
            mock_validate.return_value = True
            
            # Without force - should skip recent images
            out1 = StringIO()
            call_command('validate_images', '--dry-run', stdout=out1)
            output1 = out1.getvalue()
            
            # With force - should validate all images
            out2 = StringIO()
            call_command('validate_images', '--force', '--dry-run', stdout=out2)
            output2 = out2.getvalue()
            
            # Both should complete, but forced should validate more images
            self.assertIn('Image validation completed', output1)
            self.assertIn('Image validation completed', output2)
