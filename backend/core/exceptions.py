from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler with logging
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the exception
        logger.error(
            f"API Exception: {exc.__class__.__name__} - {str(exc)} - "
            f"View: {context['view'].__class__.__name__} - "
            f"Request: {context['request'].path}"
        )
        
        # Customize error response
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Handle specific exceptions
        if response.status_code == 404:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == 403:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == 401:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == 400:
            custom_response_data['message'] = 'Invalid request data'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'Internal server error'
            # Don't expose internal errors in production
            if not settings.DEBUG:
                custom_response_data['details'] = 'Something went wrong'
        
        response.data = custom_response_data
    
    return response

class APIException(Exception):
    """
    Custom API exception
    """
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
