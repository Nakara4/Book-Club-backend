import pytest
from unittest.mock import patch, Mock
from io import StringIO

from django.core.management import call_command
from django.contrib.auth.models import User
from django.test import TestCase

from myapp.models import Book, UserProfile, Membership, Discussion, Review, ReadingProgress, BookRecommendation
from myapp.management.commands.master_seed import Command
from myapp.tests.factories import BookFactory, BookClubFactory, UserFactory


@pytest.mark.django_db
class TestMasterSeedCommand:
    """Unit tests for master_seed management command"""

    def test_command_help(self):
        """Test that command help is available"""
        cmd = Command()
        assert 'Master seed command that orchestrates all seeding operations' in cmd.help

    def test_run_seed_step_basic_level(self):
        """Test run_seed_step with basic level"""
        # This test assumes individual seed commands work correctly
        cmd = Command()

        with patch('myapp.management.commands.master_seed.call_command') as mock_call_command:
            cmd.run_seed_step('Test Seeding Users', 'seed_users', 'basic', False)
            mock_call_command.assert_called_with('seed_users', count=10)

    def test_run_seed_step_full_level(self):
        """Test run_seed_step with full level"""
        cmd = Command()

        with patch('myapp.management.commands.master_seed.call_command') as mock_call_command:
            cmd.run_seed_step('Test Seeding Books', 'seed_books', 'full', False)
            mock_call_command.assert_called_with('seed_books', count=100)


@pytest.mark.django_db
class TestMasterSeedIntegration:
    """Integration tests for master_seed command"""

    def test_full_seeding_workflow(self):
        """Test complete seeding workflow"""
        initial_user_count = User.objects.count()
        initial_book_count = Book.objects.count()

        out = StringIO()
        call_command('master_seed', '--level', 'basic', stdout=out)

        output = out.getvalue()
        assert 'Starting Master Seed Process' in output
        
        # Verify that some users and books were created
        assert User.objects.count() > initial_user_count
        assert Book.objects.count() > initial_book_count

    def test_command_with_reset(self):
        """Test command with reset flag"""
        # Populate initial data
        UserFactory.create_batch(5)
        BookFactory.create_batch(5)
        
        initial_user_count = User.objects.count()
        initial_book_count = Book.objects.count()

        out = StringIO()
        call_command('master_seed', '--level', 'full', '--reset', stdout=out)

        output = out.getvalue()
        assert 'Reset: Yes' in output

        # Verify that users and books were reset and created again
        assert User.objects.count() != initial_user_count
        assert Book.objects.count() != initial_book_count
