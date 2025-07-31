import signal
import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Master seed command that orchestrates all seeding operations'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interrupted = False
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl-C gracefully"""
        self.stdout.write(self.style.WARNING('\n⚠️  Seeding interrupted by user. Rolling back transaction...'))
        self.interrupted = True
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            choices=['basic', 'full', 'production'],
            default='full',
            help='Seeding level: basic (minimal data for dev), full (complete dataset), or production (optimized for prod)'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Flush selected tables before seeding'
        )
    
    def handle(self, *args, **options):
        level = options['level']
        reset = options['reset']
        
        start_time = datetime.now()
        
        self.stdout.write(self.style.SUCCESS('🌱 Starting Master Seed Process'))
        self.stdout.write(f'📊 Level: {level.upper()}')
        self.stdout.write(f'🔄 Reset: {"Yes" if reset else "No"}')
        self.stdout.write('=' * 50)
        
        try:
            with transaction.atomic():
                # Step 1: Seed Users
                self.run_seed_step('👥 Seeding Users', 'seed_users', level, reset)
                if self.interrupted:
                    return
                
                # Step 2: Seed Books
                self.run_seed_step('📚 Seeding Books', 'seed_books', level, reset)
                if self.interrupted:
                    return
                
                # Step 3: Seed Book Clubs
                self.run_seed_step('🏛️  Seeding Book Clubs', 'seed_bookclubs', level, reset)
                if self.interrupted:
                    return
                
                # Step 4: Seed Reading Progress & Sessions (combined command)
                self.run_seed_step('📖 Seeding Reading Progress', 'seed_discussions_reviews_progress', level, reset)
                if self.interrupted:
                    return
                
                # Success message
                end_time = datetime.now()
                duration = end_time - start_time
                
                self.stdout.write('=' * 50)
                self.stdout.write(self.style.SUCCESS('✅ Master Seed Completed Successfully!'))
                self.stdout.write(f'⏱️  Total time: {duration.total_seconds():.1f} seconds')
                self.stdout.write('🎉 Your database is now populated with realistic data!')
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR('\n❌ Seeding was interrupted and rolled back'))
            sys.exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during seeding: {str(e)}'))
            self.stdout.write(self.style.WARNING('🔄 Transaction rolled back'))
            raise CommandError(f'Seeding failed: {str(e)}')
    
    def run_seed_step(self, description, command_name, level, reset):
        """Run a single seeding step with progress indication"""
        self.stdout.write(f'\n{description}...')
        
        try:
            # Prepare command arguments
            cmd_args = []
            cmd_kwargs = {}
            
            # Set count based on level
            if level == 'basic':
                if command_name == 'seed_users':
                    cmd_kwargs['count'] = 10
                elif command_name == 'seed_books':
                    cmd_kwargs['count'] = 20
                elif command_name == 'seed_bookclubs':
                    cmd_kwargs['count'] = 5
            elif level == 'production':
                # Production-optimized counts for realistic demo data
                if command_name == 'seed_users':
                    cmd_kwargs['count'] = 25
                elif command_name == 'seed_books':
                    cmd_kwargs['count'] = 50
                elif command_name == 'seed_bookclubs':
                    cmd_kwargs['count'] = 8
            else:  # full
                if command_name == 'seed_users':
                    cmd_kwargs['count'] = 50
                elif command_name == 'seed_books':
                    cmd_kwargs['count'] = 100
                elif command_name == 'seed_bookclubs':
                    cmd_kwargs['count'] = 15
            
            # Add reset flag if specified
            if reset:
                cmd_kwargs['clear'] = True
            
            # Run the command
            call_command(command_name, *cmd_args, **cmd_kwargs)
            
            self.stdout.write(self.style.SUCCESS(f'✅ {description} - Complete'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ {description} - Failed: {str(e)}'))
            raise
