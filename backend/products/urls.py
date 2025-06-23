from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs
urlpatterns = [
    # Public Product URLs
    path('', views.ProductListView.as_view(), name='product_list'),
    path('featured/', views.featured_products, name='featured_products'),
    path('search-suggestions/', views.product_search_suggestions, name='product_search_suggestions'),
    path('filters/', views.product_filters_data, name='product_filters_data'),
    path('sitemap/', views.product_sitemap, name='product_sitemap'),
    
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:category_slug>/', views.CategoryProductsView.as_view(), name='category_products'),
    
    # Individual Product URLs
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<slug:slug>/related/', views.related_products, name='related_products'),
    path('<slug:slug>/quick-view/', views.product_quick_view, name='product_quick_view'),
    
    # Admin URLs (Protected)
    path('admin/products/', views.AdminProductListView.as_view(), name='admin_product_list'),
    path('admin/products/<slug:slug>/', views.AdminProductDetailView.as_view(), name='admin_product_detail'),
    path('admin/products/<int:product_id>/images/', views.upload_product_images, name='upload_product_images'),
    path('admin/bulk-update/', views.bulk_update_products, name='bulk_update_products'),
    path('admin/dashboard/stats/', views.admin_dashboard_stats, name='admin_dashboard_stats'),
]

# Alternative URL patterns for different API versioning (if needed)
# You can also organize URLs like this:

# Public API v1
public_v1_patterns = [
    path('', views.ProductListView.as_view(), name='product_list_v1'),
    path('featured/', views.featured_products, name='featured_products_v1'),
    path('categories/', views.CategoryListView.as_view(), name='category_list_v1'),
    path('search/', views.product_search_suggestions, name='product_search_v1'),
    path('filters/', views.product_filters_data, name='product_filters_v1'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail_v1'),
    path('<slug:slug>/related/', views.related_products, name='related_products_v1'),
    path('<slug:slug>/quick-view/', views.product_quick_view, name='product_quick_view_v1'),
    path('category/<slug:category_slug>/', views.CategoryProductsView.as_view(), name='category_products_v1'),
]

# Admin API v1
admin_v1_patterns = [
    path('', views.AdminProductListView.as_view(), name='admin_product_list_v1'),
    path('<slug:slug>/', views.AdminProductDetailView.as_view(), name='admin_product_detail_v1'),
    path('<int:product_id>/images/', views.upload_product_images, name='upload_product_images_v1'),
    path('bulk-update/', views.bulk_update_products, name='bulk_update_products_v1'),
    path('stats/', views.admin_dashboard_stats, name='admin_dashboard_stats_v1'),
]

# If you want to use versioned URLs, uncomment these and comment the main urlpatterns above:
# urlpatterns = [
#     path('v1/', include(public_v1_patterns)),
#     path('v1/admin/', include(admin_v1_patterns)),
# ]

# Additional URL patterns for specific use cases
app_name = 'products'

# If you want to add more specific patterns:
urlpatterns += [
    # SEO friendly URLs
    path('category/<slug:category_slug>/page/<int:page>/', 
         views.CategoryProductsView.as_view(), 
         name='category_products_paginated'),
    
    # Search URLs
    path('search/<str:query>/', 
         views.ProductListView.as_view(), 
         name='product_search'),
    
    # Price range URLs
    path('price-range/<int:min_price>-<int:max_price>/', 
         views.ProductListView.as_view(), 
         name='products_by_price_range'),
]
