#!/bin/bash

# This script demonstrates how to run Django with debug settings
# Set the ENV environment variable to 'debug' to activate debug mode

echo "Running Django development server with debug settings..."
echo "Setting ENV=debug"

export ENV=debug
python manage.py runserver 0.0.0.0:8000

# Alternatively, you can run specific commands with debug settings:
# ENV=debug python manage.py check
# ENV=debug python manage.py migrate  
# ENV=debug python manage.py collectstatic
