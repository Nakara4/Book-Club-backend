"""
Custom exception handlers for consistent error formatting
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors in a consistent structure
    expected by the frontend: {'detail': 'error message'}
    
    For validation errors with multiple fields, it will format them appropriately.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get the original data
        original_data = response.data
        custom_response_data = {}
        
        # Handle different types of error responses
        if isinstance(original_data, dict):
            # Check if it's a validation error with multiple fields
            if any(isinstance(v, list) for v in original_data.values()) and len(original_data) > 1:
                # Multiple field validation errors - format as structured error
                custom_response_data = {
                    'detail': 'Validation failed',
                    'errors': {}
                }
                
                for field, errors in original_data.items():
                    if isinstance(errors, list):
                        custom_response_data['errors'][field] = errors
                    else:
                        custom_response_data['errors'][field] = [str(errors)]
                        
            elif 'detail' in original_data:
                # Already has detail field, keep it
                custom_response_data = {'detail': original_data['detail']}
                
            elif 'error' in original_data:
                # Convert 'error' to 'detail'
                custom_response_data = {'detail': original_data['error']}
                
            elif len(original_data) == 1:
                # Single field error - flatten to detail
                field, error = next(iter(original_data.items()))
                if isinstance(error, list):
                    custom_response_data = {'detail': error[0] if error else 'Validation error'}
                else:
                    custom_response_data = {'detail': str(error)}
                    
            else:
                # Multiple fields but not validation errors - create general message
                custom_response_data = {
                    'detail': 'An error occurred',
                    'errors': original_data
                }
                
        elif isinstance(original_data, list):
            # List of errors - take the first one as detail
            if original_data:
                custom_response_data = {'detail': str(original_data[0])}
            else:
                custom_response_data = {'detail': 'An error occurred'}
                
        else:
            # String or other type - convert to detail
            custom_response_data = {'detail': str(original_data)}
        
        # Update the response data
        response.data = custom_response_data
        
        # Log the error for debugging
        logger.warning(f"API Error: {response.status_code} - {custom_response_data.get('detail', 'Unknown error')}")
        
    else:
        # Handle exceptions that DRF doesn't handle by default
        if isinstance(exc, DjangoValidationError):
            custom_response_data = {
                'detail': 'Validation error',
                'errors': exc.message_dict if hasattr(exc, 'message_dict') else [str(exc)]
            }
            response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(exc, Http404):
            custom_response_data = {'detail': 'Not found'}
            response = Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
            
        elif isinstance(exc, IntegrityError):
            custom_response_data = {'detail': 'Database integrity error'}
            response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(exc, PermissionError):
            custom_response_data = {'detail': 'Permission denied'}
            response = Response(custom_response_data, status=status.HTTP_403_FORBIDDEN)
            
        # Log unhandled exceptions
        if response:
            logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}")
    
    return response


def format_validation_errors(errors):
    """
    Helper function to format validation errors consistently
    """
    if isinstance(errors, dict):
        formatted_errors = {}
        for field, field_errors in errors.items():
            if isinstance(field_errors, list):
                formatted_errors[field] = field_errors
            else:
                formatted_errors[field] = [str(field_errors)]
        return formatted_errors
    elif isinstance(errors, list):
        return {'non_field_errors': errors}
    else:
        return {'non_field_errors': [str(errors)]}
