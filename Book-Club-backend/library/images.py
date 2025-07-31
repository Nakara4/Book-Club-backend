"""
Image management utilities for book covers.

This module provides functions to fetch, validate, and manage book cover image URLs
from various sources without any local file I/O operations.
"""

import requests
from typing import List, Optional, Dict, Any
from urllib.parse import quote
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 10

# Unsplash placeholder sizes
UNSPLASH_SIZES = {
    'S': '200x300',
    'M': '300x450', 
    'L': '400x600',
    'XL': '600x900'
}


def fetch_cover_urls(isbn: str) -> List[str]:
    """
    Fetch book cover URLs from multiple sources, ranked by quality.
    
    Args:
        isbn: The ISBN of the book (10 or 13 digits)
        
    Returns:
        List of cover image URLs, ordered by quality (best first)
    """
    urls = []
    
    # Clean ISBN (remove hyphens and spaces)
    clean_isbn = ''.join(filter(str.isdigit, isbn))
    
    if not clean_isbn:
        logger.warning(f"Invalid ISBN provided: {isbn}")
        return urls
    
    # Open Library covers (multiple sizes available)
    open_library_urls = _fetch_open_library_covers(clean_isbn)
    urls.extend(open_library_urls)
    
    # Google Books covers
    google_books_urls = _fetch_google_books_covers(clean_isbn)
    urls.extend(google_books_urls)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    logger.info(f"Found {len(unique_urls)} cover URLs for ISBN {isbn}")
    return unique_urls


def _fetch_open_library_covers(isbn: str) -> List[str]:
    """Fetch cover URLs from Open Library API."""
    urls = []
    
    try:
        # Open Library covers API - provides multiple sizes
        # Format: https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg
        # Sizes: S, M, L
        base_url = f"https://covers.openlibrary.org/b/isbn/{isbn}"
        
        # Add URLs in quality order (Large, Medium, Small)
        for size in ['L', 'M', 'S']:
            urls.append(f"{base_url}-{size}.jpg")
            
    except Exception as e:
        logger.error(f"Error fetching Open Library covers for ISBN {isbn}: {e}")
    
    return urls


def _fetch_google_books_covers(isbn: str) -> List[str]:
    """Fetch cover URLs from Google Books API."""
    urls = []
    
    try:
        # Google Books API
        api_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        
        response = requests.get(api_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            volume_info = data['items'][0].get('volumeInfo', {})
            image_links = volume_info.get('imageLinks', {})
            
            # Google Books provides multiple sizes, add in quality order
            size_priority = ['extraLarge', 'large', 'medium', 'small', 'thumbnail', 'smallThumbnail']
            
            for size in size_priority:
                if size in image_links:
                    # Convert HTTP to HTTPS for security
                    url = image_links[size].replace('http://', 'https://')
                    urls.append(url)
                    
    except requests.RequestException as e:
        logger.error(f"Error fetching Google Books covers for ISBN {isbn}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching Google Books covers for ISBN {isbn}: {e}")
    
    return urls


def validate_url(url: str) -> bool:
    """
    Validate that a URL returns a successful response (200-299 status code).
    
    Args:
        url: The URL to validate
        
    Returns:
        True if URL is valid and accessible, False otherwise
    """
    try:
        # Use HEAD request to avoid downloading the entire image
        response = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        
        # Check if status code is in 200-299 range
        is_valid = 200 <= response.status_code <= 299
        
        if not is_valid:
            logger.debug(f"URL validation failed for {url}: status {response.status_code}")
        
        return is_valid
        
    except requests.RequestException as e:
        logger.debug(f"URL validation failed for {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating URL {url}: {e}")
        return False


def get_placeholder(size: str = "M") -> str:
    """
    Get a placeholder image URL from Unsplash.
    
    Args:
        size: Size of the placeholder image (S, M, L, XL)
        
    Returns:
        URL to a placeholder image
    """
    if size not in UNSPLASH_SIZES:
        logger.warning(f"Invalid size '{size}', using default 'M'")
        size = "M"
    
    dimensions = UNSPLASH_SIZES[size]
    
    # Unsplash provides random placeholder images
    # Using their source API for book/library themed images
    placeholder_url = f"https://source.unsplash.com/{dimensions}/?book,library,reading"
    
    logger.debug(f"Generated placeholder URL: {placeholder_url}")
    return placeholder_url


def ensure_image(book: Dict[str, Any]) -> str:
    """
    Ensure a book has a valid cover image URL, using placeholder if necessary.
    
    Args:
        book: Dictionary containing book information, should have 'isbn' key
              and optionally 'cover_url' key
              
    Returns:
        A valid image URL (either existing valid URL or placeholder)
    """
    # Check if book already has a cover URL
    existing_url = book.get('cover_url')
    
    if existing_url and validate_url(existing_url):
        logger.debug(f"Using existing valid cover URL for book: {existing_url}")
        return existing_url
    
    # Try to fetch new cover URLs
    isbn = book.get('isbn')
    if isbn:
        cover_urls = fetch_cover_urls(isbn)
        
        # Try each URL until we find a valid one
        for url in cover_urls:
            if validate_url(url):
                logger.info(f"Found valid cover URL for ISBN {isbn}: {url}")
                return url
    
    # Fall back to placeholder
    placeholder_url = get_placeholder()
    logger.info(f"Using placeholder image for book with ISBN {isbn}")
    return placeholder_url


# Utility function to update book with cover URL
def update_book_cover(book: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a book dictionary with a valid cover URL.
    
    Args:
        book: Dictionary containing book information
        
    Returns:
        Updated book dictionary with 'cover_url' field
    """
    book = book.copy()  # Don't modify the original
    book['cover_url'] = ensure_image(book)
    return book
