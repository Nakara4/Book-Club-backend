#!/bin/bash

# Run the Django development server locally
# Loads environment variables from .env

# Ensure .env exists
if [ ! -f .env ]; then
  echo "Error: .env file not found."
  exit 1
fi

# Export environment variables (filter out comments and empty lines)
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# Use virtual environment Python
venv/bin/python manage.py runserver 0.0.0.0:8000
