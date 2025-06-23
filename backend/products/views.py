from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Min, Max
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import generics, filters, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, ProductImage
from .serializers import (
    ProductSerializer, ProductListSerializer, CategorySerializer,
    ProductImageSerializer, AdminProductSerializer
)
from .filters import ProductFilter
from core.permissions import IsAdminOrReadOnly

# Cache timeout (in seconds)
CACHE_TIMEOUT = 60 * 15  # 15 minutes

class ProductPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50

class ProductListView(generics.ListAPIView):
    """
    List all active products with filtering, searching, and sorting
    """
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'short_description', 'category__name', 'sku']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    pagination_class = ProductPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add annotations for better performance
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', distinct=True)
        )
        
        return queryset
    
    @method_decorator(cache_page(CACHE_TIMEOUT))
    @method_decorator(vary_on_headers('Authorization'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ProductDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single product by slug
    """
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        'images', 'reviews__user'
    )
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def get_object(self):
        # Try to get from cache first
        slug = self.kwargs.get('slug')
        cache_key = f'product_detail_{slug}'
        product = cache.get(cache_key)
        
        if product is None:
            product = super().get_object()
            cache.set(cache_key, product, CACHE_TIMEOUT)
        
        return product

class CategoryListView(generics.ListAPIView):
    """
    List all active categories
    """
    queryset = Category.objects.filter(is_active=True).prefetch_related('products')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    ordering = ['name']
    
    @method_decorator(cache_page(CACHE_TIMEOUT * 2))  # Cache categories longer
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class CategoryProductsView(generics.ListAPIView):
    """
    List products by category slug
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    pagination_class = ProductPagination
    
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        
        return Product.objects.filter(
            category=category, 
            is_active=True
        ).select_related('category').prefetch_related('images').annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', distinct=True)
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_page(CACHE_TIMEOUT)
def featured_products(request):
    """
    Get featured products
    """
    products = Product.objects.filter(
        is_featured=True, 
        is_active=True
    ).select_related('category').prefetch_related('images').annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True)
    )[:8]
    
    serializer = ProductListSerializer(products, many=True, context={'request': request})
    return Response({
        'count': len(products),
        'results': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def related_products(request, slug):
    """
    Get products related to the given product (same category)
    """
    try:
        product = Product.objects.get(slug=slug, is_active=True)
        related = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id).select_related('category').prefetch_related('images')[:6]
        
        serializer = ProductListSerializer(related, many=True, context={'request': request})
        return Response({
            'count': len(related),
            'results': serializer.data
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_page(CACHE_TIMEOUT)
def product_search_suggestions(request):
    """
    Get search suggestions based on query
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return Response({'suggestions': []})
    
    # Search in product names and categories
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(category__name__icontains=query),
        is_active=True
    ).values('name', 'slug')[:10]
    
    categories = Category.objects.filter(
        name__icontains=query,
        is_active=True
    ).values('name', 'slug')[:5]
    
    return Response({
        'suggestions': {
            'products': list(products),
            'categories': list(categories)
        }
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_page(CACHE_TIMEOUT * 3)  # Cache longer as this doesn't change often
def product_filters_data(request):
    """
    Get filter options for products (price range, categories, etc.)
    """
    # Get price range
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Get categories with product counts
    categories = Category.objects.filter(
        is_active=True,
        products__is_active=True
    ).annotate(
        product_count=Count('products')
    ).order_by('name')
    
    category_data = CategorySerializer(categories, many=True).data
    
    # Get rating options
    rating_options = [
        {'value': 4, 'label': '4 Stars & Up'},
        {'value': 3, 'label': '3 Stars & Up'},
        {'value': 2, 'label': '2 Stars & Up'},
        {'value': 1, 'label': '1 Star & Up'},
    ]
    
    return Response({
        'price_range': price_range,
        'categories': category_data,
        'rating_options': rating_options,
        'sort_options': [
            {'value': '-created_at', 'label': 'Newest First'},
            {'value': 'created_at', 'label': 'Oldest First'},
            {'value': 'price', 'label': 'Price: Low to High'},
            {'value': '-price', 'label': 'Price: High to Low'},
            {'value': 'name', 'label': 'Name: A to Z'},
            {'value': '-name', 'label': 'Name: Z to A'},
        ]
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_quick_view(request, slug):
    """
    Get basic product info for quick view modal
    """
    try:
        product = Product.objects.select_related('category').prefetch_related('images').get(
            slug=slug, is_active=True
        )
        
        # Return minimal data for quick view
        data = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'short_description': product.short_description,
            'price': product.price,
            'compare_price': product.compare_price,
            'stock_quantity': product.stock_quantity,
            'images': ProductImageSerializer(product.images.all()[:3], many=True, context={'request': request}).data,
            'category': product.category.name,
            'average_rating': product.average_rating,
            'review_count': product.review_count,
            'is_in_stock': product.is_in_stock,
            'discount_percentage': product.discount_percentage,
        }
        
        return Response(data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

# Admin Views (Protected)
class AdminProductListView(generics.ListCreateAPIView):
    """
    Admin view for listing and creating products
    """
    queryset = Product.objects.all().select_related('category').prefetch_related('images')
    serializer_class = AdminProductSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'category__name']
    ordering_fields = ['name', 'price', 'stock_quantity', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if specified
        status_filter = self.request.query_params.get('status', None)
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'featured':
            queryset = queryset.filter(is_featured=True)
        elif status_filter == 'out_of_stock':
            queryset = queryset.filter(stock_quantity=0)
        
        return queryset

class AdminProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin view for product detail, update, and delete
    """
    queryset = Product.objects.all().select_related('category').prefetch_related('images')
    serializer_class = AdminProductSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'
    
    def perform_destroy(self, instance):
        # Soft delete - just mark as inactive
        instance.is_active = False
        instance.save()

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def bulk_update_products(request):
    """
    Bulk update products (activate/deactivate, feature/unfeature)
    """
    product_ids = request.data.get('product_ids', [])
    action = request.data.get('action', '')
    
    if not product_ids or not action:
        return Response(
            {'error': 'product_ids and action are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    products = Product.objects.filter(id__in=product_ids)
    
    if action == 'activate':
        products.update(is_active=True)
        message = f'Activated {products.count()} products'
    elif action == 'deactivate':
        products.update(is_active=False)
        message = f'Deactivated {products.count()} products'
    elif action == 'feature':
        products.update(is_featured=True)
        message = f'Featured {products.count()} products'
    elif action == 'unfeature':
        products.update(is_featured=False)
        message = f'Unfeatured {products.count()} products'
    else:
        return Response(
            {'error': 'Invalid action'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({'message': message})

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def upload_product_images(request, product_id):
    """
    Upload multiple images for a product
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    images = request.FILES.getlist('images')
    if not images:
        return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    created_images = []
    for i, image in enumerate(images):
        product_image = ProductImage.objects.create(
            product=product,
            image=image,
            alt_text=request.data.get(f'alt_text_{i}', ''),
            order=i + 1,
            is_primary=(i == 0 and not product.images.filter(is_primary=True).exists())
        )
        created_images.append(product_image)
    
    serializer = ProductImageSerializer(created_images, many=True, context={'request': request})
    return Response({
        'message': f'Uploaded {len(created_images)} images',
        'images': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_dashboard_stats(request):
    """
    Get product statistics for admin dashboard
    """
    stats = {
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(is_active=True).count(),
        'featured_products': Product.objects.filter(is_featured=True).count(),
        'out_of_stock': Product.objects.filter(stock_quantity=0).count(),
        'low_stock': Product.objects.filter(stock_quantity__lte=10, stock_quantity__gt=0).count(),
        'total_categories': Category.objects.filter(is_active=True).count(),
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_sitemap(request):
    """
    Generate sitemap data for products (for SEO)
    """
    products = Product.objects.filter(is_active=True).values(
        'slug', 'updated_at'
    ).order_by('-updated_at')
    
    sitemap_data = []
    for product in products:
        sitemap_data.append({
            'url': f"/products/{product['slug']}/",
            'lastmod': product['updated_at'].isoformat(),
            'changefreq': 'weekly',
            'priority': '0.8'
        })
    
    return Response(sitemap_data)
