import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all requests with timing information
    """
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(
                f"{request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.2f}s"
            )
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}  # In production, use Redis
    
    def __call__(self, request):
        client_ip = self.get_client_ip(request)
        
        # Rate limit: 100 requests per minute
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if req_time > minute_ago
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= 100:
            return JsonResponse(
                {'error': 'Rate limit exceeded'}, 
                status=429
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to responses
    """
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        if settings.DEBUG:
            response['X-Debug-Mode'] = 'True'
        
        return response
