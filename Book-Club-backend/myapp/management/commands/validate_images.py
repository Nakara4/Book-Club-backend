import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from myapp.models import Book, BookClub, UserProfile
from library.images import get_placeholder, validate_url

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
REQUEST_TIMEOUT = 10
MAX_WORKERS = 10  # Number of concurrent validation threads
BATCH_SIZE = 100  # Process images in batches


class Command(BaseCommand):
    help = 'Validate all stored image URLs and replace 404s with placeholders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually updating records'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            choices=['books', 'bookclubs', 'users'],
            default=['books', 'bookclubs', 'users'],
            help='Which models to validate images for (default: all)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=BATCH_SIZE,
            help=f'Number of images to process in each batch (default: {BATCH_SIZE})'
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=MAX_WORKERS,
            help=f'Number of concurrent validation threads (default: {MAX_WORKERS})'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force validation even if image was recently updated'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        models_to_validate = options['models']
        batch_size = options['batch_size']
        max_workers = options['max_workers']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        self.stdout.write(self.style.SUCCESS('🖼️  Starting image URL validation'))
        self.stdout.write(f'📊 Models to validate: {", ".join(models_to_validate)}')
        self.stdout.write(f'🔢 Batch size: {batch_size}')
        self.stdout.write(f'🧵 Max workers: {max_workers}')
        self.stdout.write('=' * 60)

        total_validated = 0
        total_updated = 0
        total_errors = 0

        # Validate each model type
        if 'books' in models_to_validate:
            stats = self.validate_book_images(dry_run, batch_size, max_workers, force)
            total_validated += stats['validated']
            total_updated += stats['updated']
            total_errors += stats['errors']

        if 'bookclubs' in models_to_validate:
            stats = self.validate_bookclub_images(dry_run, batch_size, max_workers, force)
            total_validated += stats['validated']
            total_updated += stats['updated']
            total_errors += stats['errors']

        if 'users' in models_to_validate:
            stats = self.validate_user_images(dry_run, batch_size, max_workers, force)
            total_validated += stats['validated']
            total_updated += stats['updated']
            total_errors += stats['errors']

        # Print summary
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Image validation completed!'))
        self.stdout.write(f'📊 Total images validated: {total_validated}')
        self.stdout.write(f'🔄 Total images updated: {total_updated}')
        
        if total_errors > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Errors encountered: {total_errors}'))

    def validate_book_images(self, dry_run: bool, batch_size: int, max_workers: int, force: bool) -> Dict[str, int]:
        """Validate book cover images"""
        self.stdout.write('\n📚 Validating book cover images...')
        
        # Get books with image URLs that need validation
        queryset = Book.objects.filter(image_url__isnull=False)
        
        if not force:
            # Only validate images that haven't been checked in the last week
            one_week_ago = timezone.now() - timezone.timedelta(days=7)
            queryset = queryset.filter(
                Q(image_updated_at__isnull=True) | Q(image_updated_at__lt=one_week_ago)
            )

        total_books = queryset.count()
        if total_books == 0:
            self.stdout.write('   ℹ️  No books found that need image validation')
            return {'validated': 0, 'updated': 0, 'errors': 0}

        self.stdout.write(f'   📊 Found {total_books} books to validate')
        
        validated = 0
        updated = 0
        errors = 0

        # Process in batches
        for i in range(0, total_books, batch_size):
            batch = list(queryset[i:i + batch_size])
            batch_stats = self._validate_image_batch(
                batch, 'image_url', 'Book', dry_run, max_workers
            )
            validated += batch_stats['validated']
            updated += batch_stats['updated']
            errors += batch_stats['errors']

        self.stdout.write(f'   ✅ Books: {validated} validated, {updated} updated, {errors} errors')
        return {'validated': validated, 'updated': updated, 'errors': errors}

    def validate_bookclub_images(self, dry_run: bool, batch_size: int, max_workers: int, force: bool) -> Dict[str, int]:
        """Validate book club images"""
        self.stdout.write('\n🏛️  Validating book club images...')
        
        # Get book clubs with image URLs that need validation
        queryset = BookClub.objects.filter(image_url__isnull=False)
        
        if not force:
            # Only validate images that haven't been checked in the last week
            one_week_ago = timezone.now() - timezone.timedelta(days=7)
            queryset = queryset.filter(
                Q(image_updated_at__isnull=True) | Q(image_updated_at__lt=one_week_ago)
            )

        total_clubs = queryset.count()
        if total_clubs == 0:
            self.stdout.write('   ℹ️  No book clubs found that need image validation')
            return {'validated': 0, 'updated': 0, 'errors': 0}

        self.stdout.write(f'   📊 Found {total_clubs} book clubs to validate')
        
        validated = 0
        updated = 0
        errors = 0

        # Process in batches
        for i in range(0, total_clubs, batch_size):
            batch = list(queryset[i:i + batch_size])
            batch_stats = self._validate_image_batch(
                batch, 'image_url', 'BookClub', dry_run, max_workers
            )
            validated += batch_stats['validated']
            updated += batch_stats['updated']
            errors += batch_stats['errors']

        self.stdout.write(f'   ✅ Book clubs: {validated} validated, {updated} updated, {errors} errors')
        return {'validated': validated, 'updated': updated, 'errors': errors}

    def validate_user_images(self, dry_run: bool, batch_size: int, max_workers: int, force: bool) -> Dict[str, int]:
        """Validate user profile images"""
        self.stdout.write('\n👥 Validating user profile images...')
        
        # Get user profiles with image URLs that need validation
        queryset = UserProfile.objects.filter(image_url__isnull=False)
        
        if not force:
            # Only validate images that haven't been checked in the last week
            one_week_ago = timezone.now() - timezone.timedelta(days=7)
            queryset = queryset.filter(
                Q(image_updated_at__isnull=True) | Q(image_updated_at__lt=one_week_ago)
            )

        total_users = queryset.count()
        if total_users == 0:
            self.stdout.write('   ℹ️  No user profiles found that need image validation')
            return {'validated': 0, 'updated': 0, 'errors': 0}

        self.stdout.write(f'   📊 Found {total_users} user profiles to validate')
        
        validated = 0
        updated = 0
        errors = 0

        # Process in batches
        for i in range(0, total_users, batch_size):
            batch = list(queryset[i:i + batch_size])
            batch_stats = self._validate_image_batch(
                batch, 'image_url', 'UserProfile', dry_run, max_workers
            )
            validated += batch_stats['validated']
            updated += batch_stats['updated']
            errors += batch_stats['errors']

        self.stdout.write(f'   ✅ User profiles: {validated} validated, {updated} updated, {errors} errors')
        return {'validated': validated, 'updated': updated, 'errors': errors}

    def _validate_image_batch(self, batch: List[Any], url_field: str, model_name: str, 
                             dry_run: bool, max_workers: int) -> Dict[str, int]:
        """Validate a batch of images using concurrent requests"""
        
        # Prepare validation tasks
        validation_tasks = []
        for obj in batch:
            url = getattr(obj, url_field)
            if url:
                validation_tasks.append((obj, url))

        if not validation_tasks:
            return {'validated': 0, 'updated': 0, 'errors': 0}

        validated = 0
        updated = 0
        errors = 0

        # Validate URLs concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit validation tasks
            future_to_obj = {
                executor.submit(self._validate_single_url, url): (obj, url)
                for obj, url in validation_tasks
            }

            # Process completed validations
            for future in as_completed(future_to_obj):
                obj, original_url = future_to_obj[future]
                validated += 1

                try:
                    is_valid = future.result()
                    
                    if not is_valid:
                        # URL is invalid, replace with placeholder
                        if dry_run:
                            self.stdout.write(f'   🔄 Would replace invalid URL for {model_name} {obj.id}: {original_url}')
                        else:
                            # Generate appropriate placeholder
                            if model_name == 'Book':
                                placeholder_url = get_placeholder('M')
                            elif model_name == 'BookClub':
                                placeholder_url = get_placeholder('L')
                            else:  # UserProfile
                                placeholder_url = f'https://api.dicebear.com/7.x/avataaars/svg?seed={obj.user.username}'
                            
                            # Update the object
                            setattr(obj, url_field, placeholder_url)
                            obj.image_updated_at = timezone.now()
                            obj.save(update_fields=[url_field, 'image_updated_at'])
                            
                            logger.info(f'Replaced invalid {model_name} image URL: {original_url} -> {placeholder_url}')
                        
                        updated += 1
                    else:
                        # URL is valid, just update the timestamp
                        if not dry_run:
                            obj.image_updated_at = timezone.now()
                            obj.save(update_fields=['image_updated_at'])

                except Exception as e:
                    logger.error(f'Error validating {model_name} image URL {original_url}: {e}')
                    errors += 1

        return {'validated': validated, 'updated': updated, 'errors': errors}

    def _validate_single_url(self, url: str) -> bool:
        """Validate a single URL and return True if it's accessible"""
        try:
            return validate_url(url)
        except Exception as e:
            logger.debug(f'URL validation failed for {url}: {e}')
            return False

    def _is_placeholder_url(self, url: str) -> bool:
        """Check if URL is already a placeholder URL"""
        placeholder_domains = [
            'source.unsplash.com',
            'api.dicebear.com',
            'via.placeholder.com',
            'picsum.photos',
            'placehold.it'
        ]
        
        try:
            parsed_url = urlparse(url)
            return any(domain in parsed_url.netloc for domain in placeholder_domains)
        except Exception:
            return False
