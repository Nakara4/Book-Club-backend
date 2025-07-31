# Book Club Backend Makefile
# Provides common development tasks

.PHONY: help install test test-unit test-integration lint format clean seed validate-images run migrate shell

# Default target
help:
	@echo "Available commands:"
	@echo "  install          - Install project dependencies"
	@echo "  test             - Run all tests"
	@echo "  test-unit        - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  lint             - Run all linting checks"
	@echo "  format           - Format code with black and isort"
	@echo "  clean            - Clean up cache files"
	@echo "  migrate          - Run Django migrations"
	@echo "  run              - Start development server"
	@echo "  shell            - Open Django shell"
	@echo "  seed             - Run all seeding commands"
	@echo "  seed-books       - Seed books from sample CSV"
	@echo "  seed-users       - Seed users"
	@echo "  seed-discussions - Seed discussions and reviews"
	@echo "  validate-images  - Validate all image URLs"

# Installation
install:
	pip install -r requirements.txt

# Testing
test:
	python manage.py test --verbosity=2
	pytest -v

test-unit:
	pytest -v -m "unit"

test-integration:
	pytest -v -m "integration"

test-coverage:
	pytest -v --cov=myapp --cov-report=html --cov-report=term-missing

# Linting and formatting
lint:
	@echo "Running Black check..."
	black --check --diff .
	@echo "Running isort check..."
	isort --check-only --diff .
	@echo "Running flake8..."
	flake8 .

format:
	@echo "Formatting with Black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

# Django management
migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python manage.py runserver

shell:
	python manage.py shell

# Seeding commands
seed: seed-users seed-books seed-discussions
	@echo "All seeding completed!"

seed-books:
	python manage.py seed_books sample_books.csv --delay 0.2

seed-users:
	python manage.py seed_users --count 50

seed-discussions:
	python manage.py seed_discussions_reviews_progress

validate-images:
	python manage.py validate_images --dry-run

validate-images-force:
	python manage.py validate_images --force

# Utility commands
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .tox/
	rm -rf build/
	rm -rf dist/

# Development setup
setup: install migrate
	@echo "Creating superuser..."
	python manage.py createsuperuser --noinput --username admin --email admin@example.com || true
	@echo "Setup completed! Run 'make run' to start the server."

# CI/CD commands (for GitHub Actions)
ci-test: lint test-coverage

# Database commands
reset-db:
	python manage.py flush --noinput
	python manage.py migrate

# Backup commands
backup-db:
	python manage.py dumpdata --natural-foreign --natural-primary > backup.json

restore-db:
	python manage.py loaddata backup.json
