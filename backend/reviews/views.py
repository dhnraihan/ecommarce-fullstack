from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.products.models import Product
from .models import Review, ReviewHelpful
from .serializers import ReviewSerializer, CreateReviewSerializer

class ProductReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        product_slug = self.kwargs['product_slug']
        product = get_object_or_404(Product, slug=product_slug)
        return Review.objects.filter(product=product)

class CreateReviewView(generics.CreateAPIView):
    serializer_class = CreateReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        product_slug = self.kwargs['product_slug']
        product = get_object_or_404(Product, slug=product_slug)
        context['product_id'] = product.id
        return context

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_helpful(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    helpful, created = ReviewHelpful.objects.get_or_create(
        user=request.user, review=review
    )
    
    if not created:
        helpful.delete()
        review.helpful_count -= 1
        is_helpful = False
    else:
        review.helpful_count += 1
        is_helpful = True
    
    review.save()
    return Response({'is_helpful': is_helpful, 'helpful_count': review.helpful_count})
