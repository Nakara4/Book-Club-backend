# Seed Books Command

The `seed_books` management command allows you to bulk-import book data from CSV or JSON files, enriching it with metadata from the Open Library API.

## Features

- ✅ **Multiple file formats**: Supports both CSV and JSON input files
- ✅ **Open Library API integration**: Automatically fetches metadata (subjects, descriptions, page counts)
- ✅ **Cover image resolution**: Automatically resolves cover image URLs using utility functions
- ✅ **Bulk operations**: Uses `get_or_create` for efficient database operations
- ✅ **Progress tracking**: Shows progress with `tqdm` progress bars
- ✅ **Rate limiting**: Implements proper API rate limiting with configurable delays
- ✅ **Retry logic**: Handles API failures with exponential backoff
- ✅ **Dry run mode**: Preview what would be done without making changes
- ✅ **Comprehensive tests**: Full test coverage with mocked API responses

## Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

The command requires these additional packages:
- `tqdm` - for progress bars
- `faker` - for generating test data (if needed)

## Usage

### Basic Usage

```bash
# Seed books from a CSV file
python manage.py seed_books sample_books.csv

# Seed books from a JSON file
python manage.py seed_books books_data.json
```

### Command Options

```bash
python manage.py seed_books <file_path> [options]

Options:
  --delay SECONDS          Delay between API requests (default: 0.5)
  --batch-size SIZE        Database transaction batch size (default: 100)
  --dry-run               Preview changes without creating records
  --update-existing       Update existing books with new API data
  --help                  Show help message
```

### Examples

```bash
# Dry run to see what would be imported
python manage.py seed_books sample_books.csv --dry-run

# Import with slower API requests (1 second delay)
python manage.py seed_books sample_books.csv --delay 1.0

# Import and update existing books
python manage.py seed_books sample_books.csv --update-existing

# Import with smaller batch size for memory-constrained environments
python manage.py seed_books large_dataset.csv --batch-size 50
```

## File Formats

### CSV Format

Required columns:
- `title` - Book title
- `author` - Author name

Optional columns:
- `published_year` - Publication year
- `isbn13` or `isbn` - ISBN for better API matching
- `pages` - Page count
- `description` - Book description

Example CSV:
```csv
title,author,published_year,isbn13,pages
Pride and Prejudice,Jane Austen,1813,9780141439518,432
1984,George Orwell,1949,9780451524935,328
```

### JSON Format

The JSON file can contain either a single book object or an array of book objects:

```json
[
  {
    "title": "Pride and Prejudice",
    "author": "Jane Austen",
    "published_year": 1813,
    "isbn13": "9780141439518",
    "pages": 432
  },
  {
    "title": "1984",
    "author": "George Orwell",
    "published_year": 1949,
    "isbn13": "9780451524935",
    "pages": 328
  }
]
```

## How It Works

1. **File Loading**: Parses CSV or JSON files and validates required fields
2. **Duplicate Detection**: Checks for existing books by ISBN or title+author
3. **API Enrichment**: For each book:
   - Searches Open Library API by title, author, or ISBN
   - Fetches detailed work information including description
   - Maps subjects to book genres
   - Resolves cover image URLs
4. **Database Operations**: Creates books, authors, and genres with proper relationships
5. **Progress Tracking**: Shows real-time progress with estimated completion time

## API Rate Limiting

The command implements responsible API usage:

- **Default delay**: 500ms between requests (2 requests/second)
- **Retry logic**: Up to 3 retries with exponential backoff
- **Timeout handling**: 10-second request timeout
- **Error logging**: Detailed logging of API failures

## Database Operations

- **Books**: Created with `external_id` and `source='openlibrary'` for idempotency
- **Authors**: Automatically created and linked (supports single author per book)
- **Genres**: Created from Open Library subjects using intelligent mapping
- **Cover Images**: URLs resolved and stored in `image_url` field

## Testing

Run the comprehensive test suite:

```bash
# Run all seed_books tests
python manage.py test myapp.tests.test_seed_books

# Run specific test classes
python manage.py test myapp.tests.test_seed_books.OpenLibraryAPITestCase
python manage.py test myapp.tests.test_seed_books.SeedBooksCommandTestCase
python manage.py test myapp.tests.test_seed_books.IntegrationTestCase
```

Test coverage includes:
- API wrapper functionality with mocked responses
- File loading and validation
- Data processing and field mapping  
- Database operations
- Error handling and edge cases
- Full integration workflow

## Sample Data

The repository includes `sample_books.csv` with 20 popular titles for testing:

```bash
python manage.py seed_books sample_books.csv --dry-run
```

## Troubleshooting

### Common Issues

**"File not found" error**
- Ensure the file path is correct and the file exists
- Use absolute paths if relative paths don't work

**API rate limiting errors**
- Increase the delay with `--delay 1.0` or higher
- The Open Library API is free but has reasonable limits

**Memory issues with large files**
- Reduce batch size with `--batch-size 25`
- Process files in smaller chunks

**ISBN formatting issues**
- The command accepts ISBNs with or without hyphens
- Both ISBN-10 and ISBN-13 formats are supported

### Logging

Enable debug logging to see detailed API interactions:

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'myapp.management.commands.seed_books': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Performance Tips

- **Use ISBNs**: Books with ISBNs have better API match rates
- **Batch processing**: Default batch size (100) works well for most cases
- **Rate limiting**: Default delay (0.5s) balances speed with API courtesy
- **Dry run first**: Always test with `--dry-run` before importing large datasets

## Contributing

When adding features to the seed_books command:

1. Add comprehensive tests with mocked API responses
2. Update this documentation
3. Follow the existing code patterns for error handling
4. Ensure rate limiting is respected
5. Add logging for important operations
