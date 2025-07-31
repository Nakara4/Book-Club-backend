import csv
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from urllib.parse import quote
from pathlib import Path

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm

from myapp.models import Book, Author, Genre
from library.images import ensure_image, update_book_cover


# Configure logging
logger = logging.getLogger(__name__)

# Open Library API configuration
OPENLIBRARY_BASE_URL = "https://openlibrary.org"
OPENLIBRARY_SEARCH_URL = f"{OPENLIBRARY_BASE_URL}/search.json"
OPENLIBRARY_WORKS_URL = f"{OPENLIBRARY_BASE_URL}/works"

# Rate limiting configuration (Open Library allows reasonable request rates)
DEFAULT_DELAY_SECONDS = 0.5  # 500ms between requests
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2

# Request timeout
REQUEST_TIMEOUT = 10


class OpenLibraryAPI:
    """Wrapper for Open Library API with rate limiting and error handling."""
    
    def __init__(self, delay_seconds: float = DEFAULT_DELAY_SECONDS):
        self.delay_seconds = delay_seconds
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting between API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a rate-limited request to the API with retries."""
        self._rate_limit()
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts: {e}")
                    return None
                else:
                    wait_time = self.delay_seconds * (RETRY_BACKOFF_FACTOR ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
        
        return None
    
    def search_book(self, title: str, author: str = None, isbn: str = None) -> Optional[Dict[str, Any]]:
        """Search for a book using title, author, and/or ISBN."""
        params = {}
        
        if isbn:
            params['isbn'] = isbn
        elif title:
            params['title'] = title
            if author:
                params['author'] = author
        else:
            logger.warning("Must provide either ISBN or title for search")
            return None
        
        params['limit'] = 1  # We only need the first match
        
        data = self._make_request(OPENLIBRARY_SEARCH_URL, params)
        
        if data and 'docs' in data and len(data['docs']) > 0:
            return data['docs'][0]
        
        return None
    
    def get_work_details(self, work_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a work."""
        if not work_key.startswith('/works/'):
            work_key = f"/works/{work_key}"
        
        url = f"{OPENLIBRARY_BASE_URL}{work_key}.json"
        return self._make_request(url)


class Command(BaseCommand):
    help = 'Seed books from CSV/JSON file using Open Library API'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to CSV or JSON file containing book data'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=DEFAULT_DELAY_SECONDS,
            help=f'Delay between API requests in seconds (default: {DEFAULT_DELAY_SECONDS})'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of books to process in each database transaction (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating records'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing books with new data from API'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file_path'])
        
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")
        
        # Initialize API client
        api = OpenLibraryAPI(delay_seconds=options['delay'])
        
        # Load book data from file
        try:
            book_data = self._load_book_data(file_path)
        except Exception as e:
            raise CommandError(f"Error loading book data: {e}")
        
        if not book_data:
            raise CommandError("No book data found in file")
        
        self.stdout.write(f"Loaded {len(book_data)} books from {file_path}")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Process books with progress bar
        batch_size = options['batch_size']
        update_existing = options['update_existing']
        dry_run = options['dry_run']
        
        processed_count = 0
        created_count = 0
        updated_count = 0
        error_count = 0
        
        with tqdm(total=len(book_data), desc="Processing books") as pbar:
            # Process in batches for better database performance
            for i in range(0, len(book_data), batch_size):
                batch = book_data[i:i + batch_size]
                
                if not dry_run:
                    with transaction.atomic():
                        batch_results = self._process_batch(batch, api, update_existing, pbar)
                else:
                    batch_results = self._process_batch(batch, api, update_existing, pbar, dry_run=True)
                
                created_count += batch_results['created']
                updated_count += batch_results['updated']
                error_count += batch_results['errors']
                processed_count += len(batch)
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f"\nSeeding completed!"))
        self.stdout.write(f"Books processed: {processed_count}")
        self.stdout.write(f"Books created: {created_count}")
        self.stdout.write(f"Books updated: {updated_count}")
        
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"Errors encountered: {error_count}"))

    def _load_book_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load book data from CSV or JSON file."""
        if file_path.suffix.lower() == '.csv':
            return self._load_csv_data(file_path)
        elif file_path.suffix.lower() == '.json':
            return self._load_json_data(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _load_csv_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load book data from CSV file."""
        books = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Validate required columns
            required_fields = ['title', 'author']
            optional_fields = ['published_year', 'isbn13', 'isbn', 'description', 'pages']
            
            if not all(field in reader.fieldnames for field in required_fields):
                missing = [f for f in required_fields if f not in reader.fieldnames]
                raise ValueError(f"Missing required CSV columns: {missing}")
            
            for row in reader:
                # Clean and validate row data
                book = {}
                
                # Required fields
                book['title'] = row['title'].strip()
                book['author'] = row['author'].strip()
                
                if not book['title'] or not book['author']:
                    logger.warning(f"Skipping row with empty title or author: {row}")
                    continue
                
                # Optional fields
                if 'published_year' in row and row['published_year']:
                    try:
                        book['published_year'] = int(row['published_year'])
                    except ValueError:
                        logger.warning(f"Invalid published_year '{row['published_year']}' for {book['title']}")
                
                # ISBN (prefer isbn13 over isbn)
                isbn = row.get('isbn13') or row.get('isbn')
                if isbn:
                    book['isbn'] = isbn.strip()
                
                # Optional text fields
                for field in ['description']:
                    if field in row and row[field]:
                        book[field] = row[field].strip()
                
                # Pages
                if 'pages' in row and row['pages']:
                    try:
                        book['pages'] = int(row['pages'])
                    except ValueError:
                        logger.warning(f"Invalid pages '{row['pages']}' for {book['title']}")
                
                books.append(book)
        
        return books

    def _load_json_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load book data from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Handle both single book object and array of books
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("JSON must contain an object or array of objects")
        
        books = []
        for item in data:
            if not isinstance(item, dict):
                logger.warning(f"Skipping non-object item: {item}")
                continue
            
            # Validate required fields
            if not item.get('title') or not item.get('author'):
                logger.warning(f"Skipping item missing title or author: {item}")
                continue
            
            # Clean the data
            book = {
                'title': str(item['title']).strip(),
                'author': str(item['author']).strip()
            }
            
            # Optional fields
            for field in ['published_year', 'pages']:
                if field in item and item[field] is not None:
                    try:
                        book[field] = int(item[field])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid {field} '{item[field]}' for {book['title']}")
            
            for field in ['isbn13', 'isbn', 'description']:
                if field in item and item[field]:
                    book[field] = str(item[field]).strip()
            
            # Prefer isbn13 over isbn
            if 'isbn13' in book:
                book['isbn'] = book.pop('isbn13')
            
            books.append(book)
        
        return books

    def _process_batch(self, batch: List[Dict[str, Any]], api: OpenLibraryAPI, 
                      update_existing: bool, pbar: tqdm, dry_run: bool = False) -> Dict[str, int]:
        """Process a batch of books."""
        results = {'created': 0, 'updated': 0, 'errors': 0}
        
        for book_data in batch:
            try:
                result = self._process_single_book(book_data, api, update_existing, dry_run)
                if result == 'created':
                    results['created'] += 1
                elif result == 'updated':
                    results['updated'] += 1
            except Exception as e:
                logger.error(f"Error processing book '{book_data.get('title', 'Unknown')}': {e}")
                results['errors'] += 1
            
            pbar.update(1)
        
        return results

    def _process_single_book(self, book_data: Dict[str, Any], api: OpenLibraryAPI, 
                           update_existing: bool, dry_run: bool = False) -> Optional[str]:
        """Process a single book and return the operation performed."""
        title = book_data['title']
        author_name = book_data['author']
        isbn = book_data.get('isbn')
        
        # Check if book already exists
        existing_book = None
        if isbn:
            existing_book = Book.objects.filter(isbn=isbn).first()
        
        if not existing_book:
            # Try to find by title and author
            author, _ = Author.objects.get_or_create(
                first_name=author_name.split()[0] if author_name.split() else author_name,
                last_name=' '.join(author_name.split()[1:]) if len(author_name.split()) > 1 else '',
                defaults={'bio': f'Author of {title}'}
            )
            
            existing_book = Book.objects.filter(
                title__iexact=title,
                authors=author
            ).first()
        
        if existing_book and not update_existing:
            logger.debug(f"Book already exists: {title}")
            return None
        
        # Fetch metadata from Open Library
        metadata = self._fetch_book_metadata(api, title, author_name, isbn)
        
        # Prepare book data for creation/update
        book_fields = self._prepare_book_fields(book_data, metadata)
        
        if dry_run:
            if existing_book:
                self.stdout.write(f"Would update: {title}")
                return 'updated'
            else:
                self.stdout.write(f"Would create: {title}")
                return 'created'
        
        # Create or update the book
        if existing_book:
            return self._update_book(existing_book, book_fields, author_name, metadata)
        else:
            return self._create_book(book_fields, author_name, metadata)

    def _fetch_book_metadata(self, api: OpenLibraryAPI, title: str, author: str, isbn: str = None) -> Dict[str, Any]:
        """Fetch book metadata from Open Library API."""
        metadata = {}
        
        # Search for the book
        search_result = api.search_book(title=title, author=author, isbn=isbn)
        
        if not search_result:
            logger.warning(f"No search results found for: {title} by {author}")
            return metadata
        
        # Extract basic information from search result
        metadata.update({
            'openlibrary_key': search_result.get('key', ''),
            'subjects': search_result.get('subject', []),
            'first_publish_year': search_result.get('first_publish_year'),
            'number_of_pages_median': search_result.get('number_of_pages_median'),
            'publishers': search_result.get('publisher', []),
            'isbn_list': search_result.get('isbn', []),
            'language': search_result.get('language', ['eng']),
        })
        
        # Get detailed work information if available
        work_key = search_result.get('key')
        if work_key and work_key.startswith('/works/'):
            work_details = api.get_work_details(work_key)
            if work_details:
                description = work_details.get('description')
                if isinstance(description, dict):
                    metadata['description'] = description.get('value', '')
                elif isinstance(description, str):
                    metadata['description'] = description
                
                metadata['subjects'].extend(work_details.get('subjects', []))
        
        return metadata

    def _prepare_book_fields(self, book_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare book fields for database insertion/update."""
        fields = {
            'title': book_data['title'],
            'source': 'openlibrary',
        }
        
        # External ID from Open Library
        if metadata.get('openlibrary_key'):
            fields['external_id'] = metadata['openlibrary_key'].replace('/works/', '')
        
        # ISBN (prefer from original data)
        isbn = book_data.get('isbn') or (metadata.get('isbn_list', [{}])[0] if metadata.get('isbn_list') else None)
        if isbn:
            # Clean ISBN and determine if it's ISBN-10 or ISBN-13
            clean_isbn = ''.join(filter(str.isdigit, str(isbn)))
            if len(clean_isbn) == 13:
                fields['isbn'] = clean_isbn
            elif len(clean_isbn) == 10:
                fields['isbn_10'] = clean_isbn
        
        # Description (prefer from API if available)
        description = metadata.get('description') or book_data.get('description')
        if description:
            fields['description'] = description[:1000]  # Truncate if too long
        
        # Publication year
        pub_year = book_data.get('published_year') or metadata.get('first_publish_year')
        if pub_year:
            try:
                # Convert to date (assuming January 1st)
                from datetime import date
                fields['publication_date'] = date(int(pub_year), 1, 1)
            except (ValueError, TypeError):
                logger.warning(f"Invalid publication year: {pub_year}")
        
        # Page count (prefer from original data)
        pages = book_data.get('pages') or metadata.get('number_of_pages_median')
        if pages:
            try:
                fields['page_count'] = int(pages)
            except (ValueError, TypeError):
                logger.warning(f"Invalid page count: {pages}")
        
        # Publisher (use first one if multiple)
        publishers = metadata.get('publishers', [])
        if publishers:
            fields['publisher'] = str(publishers[0])[:200]  # Truncate if too long
        
        # Language (use first one, default to English)
        languages = metadata.get('language', ['eng'])
        if languages:
            lang_code = languages[0]
            lang_map = {
                'eng': 'English',
                'spa': 'Spanish',
                'fre': 'French',
                'ger': 'German',
                'ita': 'Italian',
                'por': 'Portuguese',
            }
            fields['language'] = lang_map.get(lang_code, 'English')
        
        # Resolve cover image URL
        book_with_isbn = {'isbn': isbn} if isbn else {}
        cover_url = ensure_image(book_with_isbn)
        if cover_url:
            from django.utils import timezone
            fields['image_url'] = cover_url
            fields['image_updated_at'] = timezone.now()
        
        return fields

    def _create_book(self, book_fields: Dict[str, Any], author_name: str, metadata: Dict[str, Any]) -> str:
        """Create a new book in the database."""
        from django.utils import timezone
        
        # Create the book
        book = Book.objects.create(**book_fields)
        
        # Add author
        author, _ = Author.objects.get_or_create(
            first_name=author_name.split()[0] if author_name.split() else author_name,
            last_name=' '.join(author_name.split()[1:]) if len(author_name.split()) > 1 else '',
            defaults={'bio': f'Author of {book.title}'}
        )
        book.authors.add(author)
        
        # Add genres based on subjects
        self._add_genres_from_subjects(book, metadata.get('subjects', []))
        
        logger.info(f"Created book: {book.title}")
        return 'created'

    def _update_book(self, book: Book, book_fields: Dict[str, Any], author_name: str, metadata: Dict[str, Any]) -> str:
        """Update an existing book in the database."""
        from django.utils import timezone
        
        updated = False
        
        # Update fields if they're empty or we have better data
        for field, value in book_fields.items():
            if field in ['source', 'external_id']:  # Always update these
                setattr(book, field, value)
                updated = True
            elif not getattr(book, field) and value:  # Only update if current field is empty
                setattr(book, field, value)
                updated = True
        
        if updated:
            book.save()
        
        # Add genres from subjects if none exist
        if not book.genres.exists():
            self._add_genres_from_subjects(book, metadata.get('subjects', []))
            updated = True
        
        if updated:
            logger.info(f"Updated book: {book.title}")
            return 'updated'
        
        return None

    def _add_genres_from_subjects(self, book: Book, subjects: List[str]):
        """Add genres to book based on Open Library subjects."""
        if not subjects:
            return
        
        # Map Open Library subjects to our genres
        subject_to_genre = {
            'fiction': 'Fiction',
            'mystery': 'Mystery',
            'romance': 'Romance',
            'science fiction': 'Science Fiction',
            'fantasy': 'Fantasy',
            'biography': 'Biography',
            'history': 'History',
            'self-help': 'Self-Help',
            'young adult': 'Young Adult',
            'literary fiction': 'Literary Fiction',
            'thriller': 'Mystery',  # Map to closest existing genre
            'horror': 'Fiction',  # Map to Fiction if no Horror genre
            'drama': 'Fiction',
            'poetry': 'Fiction',
            'philosophy': 'History',  # Map to closest existing genre
        }
        
        genres_to_add = set()
        
        for subject in subjects[:10]:  # Limit to first 10 subjects
            subject_lower = subject.lower().strip()
            
            # Direct match
            if subject_lower in subject_to_genre:
                genres_to_add.add(subject_to_genre[subject_lower])
                continue
            
            # Partial match
            for key, genre in subject_to_genre.items():
                if key in subject_lower:
                    genres_to_add.add(genre)
                    break
        
        # Add genres to book
        for genre_name in genres_to_add:
            genre, _ = Genre.objects.get_or_create(
                name=genre_name,
                defaults={'description': f'Books categorized as {genre_name}'}
            )
            book.genres.add(genre)
