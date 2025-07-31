import os
from django.core.wsgi import get_wsgi_application

# Use debug settings if ENV=debug is set
if os.environ.get('ENV') == 'debug':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Book-Club-backend.settings_debug')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Book-Club-backend.settings')

application = get_wsgi_application()
