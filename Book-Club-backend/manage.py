#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Use debug settings if ENV=debug is set
    if os.environ.get('ENV') == 'debug':
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Book-Club-backend.settings_debug")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Book-Club-backend.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
