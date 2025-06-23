from django.urls import path
from . import views

urlpatterns = [
    path('product/<slug:product_slug>/', views.ProductReviewsView.as_view(), name='product_reviews'),
    path('product/<slug:product_slug>/create/', views.CreateReviewView.as_view(), name='create_review'),
    path('<int:review_id>/helpful/', views.toggle_helpful, name='toggle_helpful'),
]
