"""
Centralized configuration for the API, including pagination and other defaults
"""

# ============================================================================
# PAGINATION CONFIGURATION
# ============================================================================
# This dictionary centralizes pagination settings to be used in views.
# This makes it easy to maintain consistency and update pagination behavior across the API.

PAGINATION_CONFIG = {
    'Standard': 'myapp.pagination.StandardResultsSetPagination',
    'Large': 'myapp.pagination.LargeResultsSetPagination',
    'Small': 'myapp.pagination.SmallResultsSetPagination',
    'Search': 'myapp.pagination.SearchResultsPagination',
}

# Default page size for standard pagination
DEFAULT_PAGE_SIZE = 12


# ============================================================================
# GLOBAL API SETTINGS
# ============================================================================

# Default filtering backends used across most views
DEFAULT_FILTER_BACKENDS = [
    'django_filters.rest_framework.DjangoFilterBackend',
    'rest_framework.filters.SearchFilter',
    'rest_framework.filters.OrderingFilter',
]

# Default permission classes for most endpoints
# More restrictive permissions should be set on a per-view basis
DEFAULT_PERMISSION_CLASSES = [
    'rest_framework.permissions.IsAuthenticatedOrReadOnly',
]


# ============================================================================
# AUTHENTICATION AND ERROR HANDLING
# ============================================================================

# Custom exception handler for consistent error formatting
CUSTOM_EXCEPTION_HANDLER = 'myapp.exceptions.custom_exception_handler'

# Custom authentication classes
DEFAULT_AUTHENTICATION_CLASSES = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
    'rest_framework.authentication.TokenAuthentication',
    'rest_framework.authentication.SessionAuthentication',
]

