from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint
    """
    return Response({
        'status': 'healthy',
        'message': 'API is running successfully'
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def site_stats(request):
    """
    Get site statistics for admin dashboard
    """
    stats = {
        'total_users': User.objects.count(),
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'active_products': Product.objects.filter(is_active=True).count(),
        'featured_products': Product.objects.filter(is_featured=True).count(),
    }
    return Response(stats)
