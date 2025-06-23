import django_filters
from .models import Product, Category

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    rating = django_filters.NumberFilter(method='filter_by_rating')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    
    class Meta:
        model = Product
        fields = ['category', 'is_featured']
    
    def filter_by_rating(self, queryset, name, value):
        # Filter products with average rating >= value
        from django.db.models import Avg
        return queryset.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__gte=value)
    
    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)
