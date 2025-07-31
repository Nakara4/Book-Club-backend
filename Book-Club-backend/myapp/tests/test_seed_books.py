import pytest
import tempfile
import json
import csv
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
from io import StringIO

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from myapp.models import Book, Author, Genre
from myapp.management.commands.seed_books import Command, OpenLibraryAPI
from myapp.tests.factories import AuthorFactory, GenreFactory, BookFactory


class OpenLibraryAPIMockData:
    """Mock data for Open Library API responses."""
    
    @staticmethod
    def get_search_response_success():
        """Mock successful search response from Open Library."""
        return {
            "numFound": 1,
            "start": 0,
            "numFoundExact": True,
            "docs": [
                {
                    "key": "/works/OL45804W",
                    "title": "Pride and Prejudice",
                    "author_name": ["Jane Austen"],
                    "first_publish_year": 1813,
                    "isbn": ["0141439513", "9780141439518"],
                    "publisher": ["Penguin Classics"],
                    "subject": ["Fiction", "Romance", "Classic literature"],
                    "number_of_pages_median": 432,
                    "language": ["eng"],
                    "cover_i": 8091016
                }
            ]
        }
    
    @staticmethod
    def get_search_response_empty():
        """Mock empty search response from Open Library."""
        return {
            "numFound": 0,
            "start": 0,
            "numFoundExact": True,
            "docs": []
        }
    
    @staticmethod
    def get_work_details_response():
        """Mock work details response from Open Library."""
        return {
            "description": {
                "type": "/type/text",
                "value": "Pride and Prejudice is a romantic novel by Jane Austen, first published in 1813."
            },
            "title": "Pride and Prejudice",
            "subjects": [
                "Fiction",
                "Romance", 
                "English literature",
                "19th century",
                "Social class",
                "Marriage"
            ],
            "key": "/works/OL45804W",
            "authors": [
                {
                    "author": {
                        "key": "/authors/OL21594A"
                    },
                    "type": {
                        "key": "/type/author_role"
                    }
                }
            ]
        }


class OpenLibraryAPITestCase(TestCase):
    """Test cases for OpenLibraryAPI class."""
    
    def setUp(self):
        self.api = OpenLibraryAPI(delay_seconds=0)  # No delay for tests
    
    @patch('time.sleep')
    @patch('requests.get')
    def test_rate_limiting(self, mock_get, mock_sleep):
        """Test that rate limiting works correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Set delay to test rate limiting
        self.api.delay_seconds = 1.0
        
        # Make two requests
        self.api._make_request("http://test.com")
        self.api._make_request("http://test.com")
        
        # Sleep should be called for rate limiting
        self.assertTrue(mock_sleep.called)
    
    @patch('requests.get')
    def test_search_book_success(self, mock_get):
        """Test successful book search."""
        mock_response = Mock()
        mock_response.json.return_value = OpenLibraryAPIMockData.get_search_response_success()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.search_book(title="Pride and Prejudice", author="Jane Austen")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "Pride and Prejudice")
        self.assertEqual(result['key'], "/works/OL45804W")
    
    @patch('requests.get')
    def test_search_book_not_found(self, mock_get):
        """Test book search with no results."""
        mock_response = Mock()
        mock_response.json.return_value = OpenLibraryAPIMockData.get_search_response_empty()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.search_book(title="Nonexistent Book", author="Unknown Author")
        
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_search_book_with_isbn(self, mock_get):
        """Test book search using ISBN."""
        mock_response = Mock()
        mock_response.json.return_value = OpenLibraryAPIMockData.get_search_response_success()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.search_book(isbn="9780141439518")
        
        self.assertIsNotNone(result)
        mock_get.assert_called_with(
            "https://openlibrary.org/search.json",
            params={"isbn": "9780141439518", "limit": 1},
            timeout=10
        )
    
    @patch('requests.get')
    def test_get_work_details_success(self, mock_get):
        """Test successful work details retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = OpenLibraryAPIMockData.get_work_details_response()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.get_work_details("/works/OL45804W")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "Pride and Prejudice")
        self.assertIn('description', result)
    
    @patch('requests.get')
    def test_request_retry_on_failure(self, mock_get):
        """Test that requests are retried on failure."""
        # First two calls fail, third succeeds
        mock_get.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            Mock(json=lambda: {"success": True}, raise_for_status=lambda: None)
        ]
        
        result = self.api._make_request("http://test.com")
        
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(result, {"success": True})
    
    @patch('requests.get')
    def test_request_max_retries_exceeded(self, mock_get):
        """Test that None is returned when max retries are exceeded."""
        mock_get.side_effect = Exception("Network error")
        
        result = self.api._make_request("http://test.com")
        
        self.assertEqual(mock_get.call_count, 3)  # MAX_RETRIES
        self.assertIsNone(result)


class SeedBooksCommandTestCase(TestCase):
    """Test cases for seed_books management command."""
    
    def setUp(self):
        self.command = Command()
        # Clear any existing data
        Book.objects.all().delete()
        Author.objects.all().delete()
        Genre.objects.all().delete()
    
    def create_test_csv_file(self, data):
        """Create a temporary CSV file with test data."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        temp_file.close()
        return Path(temp_file.name)
    
    def create_test_json_file(self, data):
        """Create a temporary JSON file with test data."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, temp_file)
        temp_file.close()
        return Path(temp_file.name)
    
    def test_load_csv_data_valid(self):
        """Test loading valid CSV data."""
        test_data = [
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'published_year': '1813',
                'isbn13': '9780141439518',
                'pages': '432'
            },
            {
                'title': '1984',
                'author': 'George Orwell',
                'published_year': '1949',
                'isbn13': '9780451524935',
                'pages': '328'
            }
        ]
        
        csv_file = self.create_test_csv_file(test_data)
        
        try:
            books = self.command._load_book_data(csv_file)
            
            self.assertEqual(len(books), 2)
            self.assertEqual(books[0]['title'], 'Pride and Prejudice')
            self.assertEqual(books[0]['author'], 'Jane Austen')
            self.assertEqual(books[0]['published_year'], 1813)
            self.assertEqual(books[0]['isbn'], '9780141439518')
            self.assertEqual(books[0]['pages'], 432)
        finally:
            csv_file.unlink()
    
    def test_load_csv_data_missing_required_fields(self):
        """Test loading CSV data with missing required fields."""
        test_data = [
            {
                'title': 'Pride and Prejudice',
                # Missing author field
                'published_year': '1813'
            }
        ]
        
        csv_file = self.create_test_csv_file(test_data)
        
        try:
            with self.assertRaises(ValueError) as context:
                self.command._load_book_data(csv_file)
            
            self.assertIn("Missing required CSV columns", str(context.exception))
        finally:
            csv_file.unlink()
    
    def test_load_json_data_valid(self):
        """Test loading valid JSON data."""
        test_data = [
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'published_year': 1813,
                'isbn13': '9780141439518',
                'pages': 432
            }
        ]
        
        json_file = self.create_test_json_file(test_data)
        
        try:
            books = self.command._load_book_data(json_file)
            
            self.assertEqual(len(books), 1)
            self.assertEqual(books[0]['title'], 'Pride and Prejudice')
            self.assertEqual(books[0]['author'], 'Jane Austen')
            self.assertEqual(books[0]['published_year'], 1813)
            self.assertEqual(books[0]['isbn'], '9780141439518')
        finally:
            json_file.unlink()
    
    def test_load_json_data_single_object(self):
        """Test loading JSON data with single object (not array)."""
        test_data = {
            'title': 'Pride and Prejudice',
            'author': 'Jane Austen',
            'published_year': 1813
        }
        
        json_file = self.create_test_json_file(test_data)
        
        try:
            books = self.command._load_book_data(json_file)
            
            self.assertEqual(len(books), 1)
            self.assertEqual(books[0]['title'], 'Pride and Prejudice')
        finally:
            json_file.unlink()
    
    def test_unsupported_file_format(self):
        """Test loading unsupported file format."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        temp_file.close()
        
        try:
            with self.assertRaises(ValueError) as context:
                self.command._load_book_data(Path(temp_file.name))
            
            self.assertIn("Unsupported file format", str(context.exception))
        finally:
            Path(temp_file.name).unlink()
    
    @patch('myapp.management.commands.seed_books.OpenLibraryAPI')
    @patch('library.images.ensure_image')
    def test_create_book_with_api_data(self, mock_ensure_image, mock_api_class):
        """Test creating a book with API data."""
        # Mock the API
        mock_api = Mock()
        mock_api.search_book.return_value = OpenLibraryAPIMockData.get_search_response_success()['docs'][0]
        mock_api.get_work_details.return_value = OpenLibraryAPIMockData.get_work_details_response()
        mock_api_class.return_value = mock_api
        
        # Mock image resolution
        mock_ensure_image.return_value = "http://covers.openlibrary.org/b/isbn/9780141439518-L.jpg"
        
        book_data = {
            'title': 'Pride and Prejudice',
            'author': 'Jane Austen',
            'isbn': '9780141439518'
        }
        
        metadata = self.command._fetch_book_metadata(mock_api, book_data['title'], book_data['author'], book_data['isbn'])
        book_fields = self.command._prepare_book_fields(book_data, metadata)
        result = self.command._create_book(book_fields, book_data['author'], metadata)
        
        self.assertEqual(result, 'created')
        
        # Verify book was created
        book = Book.objects.get(title='Pride and Prejudice')
        self.assertEqual(book.title, 'Pride and Prejudice')
        self.assertEqual(book.isbn, '9780141439518')
        self.assertEqual(book.source, 'openlibrary')
        self.assertIsNotNone(book.image_url)
        
        # Verify author was created and linked
        self.assertEqual(book.authors.count(), 1)
        author = book.authors.first()
        self.assertEqual(author.first_name, 'Jane')
        self.assertEqual(author.last_name, 'Austen')
        
        # Verify genres were created and linked
        self.assertTrue(book.genres.exists())
        genre_names = list(book.genres.values_list('name', flat=True))
        self.assertIn('Fiction', genre_names)
        self.assertIn('Romance', genre_names)
    
    @patch('myapp.management.commands.seed_books.OpenLibraryAPI')
    def test_update_existing_book(self, mock_api_class):
        """Test updating an existing book."""
        # Create existing book with minimal data
        existing_book = Book.objects.create(
            title='Pride and Prejudice',
            isbn='9780141439518',
            source='manual'
        )
        
        # Mock the API
        mock_api = Mock()
        mock_api.search_book.return_value = OpenLibraryAPIMockData.get_search_response_success()['docs'][0]
        mock_api.get_work_details.return_value = OpenLibraryAPIMockData.get_work_details_response()
        mock_api_class.return_value = mock_api
        
        book_data = {
            'title': 'Pride and Prejudice',
            'author': 'Jane Austen',
            'isbn': '9780141439518'
        }
        
        metadata = self.command._fetch_book_metadata(mock_api, book_data['title'], book_data['author'], book_data['isbn'])
        book_fields = self.command._prepare_book_fields(book_data, metadata)
        result = self.command._update_book(existing_book, book_fields, book_data['author'], metadata)
        
        self.assertEqual(result, 'updated')
        
        # Verify book was updated
        existing_book.refresh_from_db()
        self.assertEqual(existing_book.source, 'openlibrary')
        self.assertIsNotNone(existing_book.external_id)
        self.assertIsNotNone(existing_book.description)
    
    @patch('myapp.management.commands.seed_books.OpenLibraryAPI')
    def test_dry_run_mode(self, mock_api_class):
        """Test dry run mode doesn't create actual records."""
        # Mock the API
        mock_api = Mock()
        mock_api.search_book.return_value = OpenLibraryAPIMockData.get_search_response_success()['docs'][0]
        mock_api_class.return_value = mock_api
        
        book_data = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        
        result = self.command._process_single_book(book_data, mock_api, False, dry_run=True)
        
        self.assertEqual(result, 'created')
        
        # Verify no book was actually created
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Author.objects.count(), 0)
    
    def test_prepare_book_fields_isbn_handling(self):
        """Test ISBN handling in book field preparation."""
        book_data = {'title': 'Test Book', 'isbn': '978-0-14-143951-8'}
        metadata = {'isbn_list': ['9780141439518']}
        
        fields = self.command._prepare_book_fields(book_data, metadata)
        
        # Should clean and use ISBN from book_data
        self.assertEqual(fields['isbn'], '9780141439518')
    
    def test_prepare_book_fields_isbn10_handling(self):
        """Test ISBN-10 handling in book field preparation."""
        book_data = {'title': 'Test Book', 'isbn': '0141439513'}
        metadata = {}
        
        fields = self.command._prepare_book_fields(book_data, metadata)
        
        # Should recognize as ISBN-10
        self.assertEqual(fields['isbn_10'], '0141439513')
        self.assertNotIn('isbn', fields)
    
    def test_add_genres_from_subjects(self):
        """Test adding genres based on Open Library subjects."""
        book = Book.objects.create(title='Test Book')
        subjects = ['Fiction', 'Mystery', 'Thriller', 'Science fiction', 'Unknown genre']
        
        self.command._add_genres_from_subjects(book, subjects)
        
        genre_names = list(book.genres.values_list('name', flat=True))
        self.assertIn('Fiction', genre_names)
        self.assertIn('Mystery', genre_names)
        self.assertIn('Science Fiction', genre_names)
        # 'Thriller' should map to 'Mystery'
        # 'Unknown genre' should be ignored
    
    @patch('myapp.management.commands.seed_books.tqdm')
    def test_command_execution_with_csv(self, mock_tqdm):
        """Test full command execution with CSV file."""
        # Mock tqdm to avoid progress bar in tests
        mock_progress = Mock()
        mock_tqdm.return_value.__enter__.return_value = mock_progress
        
        test_data = [
            {
                'title': 'Test Book',
                'author': 'Test Author',
                'published_year': '2023',
                'isbn13': '9781234567890'
            }
        ]
        
        csv_file = self.create_test_csv_file(test_data)
        
        try:
            with patch('myapp.management.commands.seed_books.OpenLibraryAPI') as mock_api_class:
                # Mock API to return no results (simpler test)
                mock_api = Mock()
                mock_api.search_book.return_value = None
                mock_api_class.return_value = mock_api
                
                # Capture command output
                out = StringIO()
                
                call_command(
                    'seed_books',
                    str(csv_file),
                    '--dry-run',
                    stdout=out
                )
                
                output = out.getvalue()
                self.assertIn('Loaded 1 books', output)
                self.assertIn('DRY RUN MODE', output)
        finally:
            csv_file.unlink()
    
    def test_command_with_nonexistent_file(self):
        """Test command with nonexistent file raises error."""
        with self.assertRaises(CommandError) as context:
            call_command('seed_books', '/nonexistent/file.csv')
        
        self.assertIn('File not found', str(context.exception))
    
    def test_fetch_book_metadata_no_results(self):
        """Test fetching metadata when no results are found."""
        mock_api = Mock()
        mock_api.search_book.return_value = None
        
        metadata = self.command._fetch_book_metadata(mock_api, "Unknown Book", "Unknown Author")
        
        self.assertEqual(metadata, {})
    
    @patch('library.images.ensure_image')
    def test_prepare_book_fields_with_cover_image(self, mock_ensure_image):
        """Test book field preparation includes cover image URL."""
        mock_ensure_image.return_value = "http://example.com/cover.jpg"
        
        book_data = {'title': 'Test Book', 'isbn': '9781234567890'}
        metadata = {}
        
        fields = self.command._prepare_book_fields(book_data, metadata)
        
        self.assertEqual(fields['image_url'], "http://example.com/cover.jpg")
        self.assertIsNotNone(fields['image_updated_at'])
    
    def test_language_mapping(self):
        """Test language code mapping in book field preparation."""
        book_data = {'title': 'Test Book'}
        metadata = {'language': ['spa']}  # Spanish
        
        fields = self.command._prepare_book_fields(book_data, metadata)
        
        self.assertEqual(fields['language'], 'Spanish')
    
    def test_description_truncation(self):
        """Test description truncation in book field preparation."""
        long_description = "A" * 1500  # Longer than 1000 chars
        book_data = {'title': 'Test Book', 'description': long_description}
        metadata = {}
        
        fields = self.command._prepare_book_fields(book_data, metadata)
        
        self.assertEqual(len(fields['description']), 1000)
    
    def test_publication_date_conversion(self):
        """Test publication year to date conversion."""
        book_data = {'title': 'Test Book', 'published_year': 2023}
        metadata = {}
        
        fields = self.command._prepare_book_fields(book_data, metadata)
        
        self.assertEqual(fields['publication_date'], date(2023, 1, 1))
    
    def test_existing_book_not_updated_by_default(self):
        """Test that existing books are not updated by default."""
        # Create existing book
        Book.objects.create(title='Existing Book', isbn='9781234567890')
        
        mock_api = Mock()
        book_data = {'title': 'Existing Book', 'author': 'Test Author', 'isbn': '9781234567890'}
        
        result = self.command._process_single_book(book_data, mock_api, update_existing=False)
        
        self.assertIsNone(result)


class IntegrationTestCase(TestCase):
    """Integration tests for the complete seed_books workflow."""
    
    def setUp(self):
        # Clear any existing data
        Book.objects.all().delete()
        Author.objects.all().delete()
        Genre.objects.all().delete()
    
    @patch('requests.get')
    @patch('library.images.ensure_image')
    def test_full_workflow_with_mocked_api(self, mock_ensure_image, mock_requests_get):
        """Test the complete workflow with mocked API responses."""
        # Mock image resolution
        mock_ensure_image.return_value = "http://covers.openlibrary.org/b/isbn/9780141439518-L.jpg"
        
        # Mock API responses
        def mock_get_response(url, **kwargs):
            mock_response = Mock()
            
            if 'search.json' in url:
                mock_response.json.return_value = OpenLibraryAPIMockData.get_search_response_success()
            elif '/works/' in url:
                mock_response.json.return_value = OpenLibraryAPIMockData.get_work_details_response()
            else:
                mock_response.json.return_value = {}
            
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_requests_get.side_effect = mock_get_response
        
        # Create test data file
        test_data = [
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'published_year': '1813',
                'isbn13': '9780141439518',
                'pages': '432'
            }
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        fieldnames = test_data[0].keys()
        writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_data)
        temp_file.close()
        
        try:
            # Run the command
            out = StringIO()
            call_command('seed_books', temp_file.name, stdout=out)
            
            # Verify results
            self.assertEqual(Book.objects.count(), 1)
            
            book = Book.objects.first()
            self.assertEqual(book.title, 'Pride and Prejudice')
            self.assertEqual(book.isbn, '9780141439518')
            self.assertEqual(book.source, 'openlibrary')
            self.assertIsNotNone(book.description)
            self.assertIsNotNone(book.image_url)
            
            # Verify author
            self.assertEqual(book.authors.count(), 1)
            author = book.authors.first()
            self.assertEqual(author.first_name, 'Jane')
            self.assertEqual(author.last_name, 'Austen')
            
            # Verify genres
            self.assertTrue(book.genres.exists())
            
        finally:
            Path(temp_file.name).unlink()
