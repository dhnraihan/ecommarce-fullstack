from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Profile
    path('user/', views.user_profile, name='user_profile'),
    path('user/update/', views.update_profile, name='update_profile'),
    path('user/change-password/', views.change_password, name='change_password'),
    path('user/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    
    # Password Reset
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset-confirm/<int:uid>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Email Verification
    path('verify-email/', views.send_verification_email, name='send_verification_email'),
    path('verify-email-confirm/<int:uid>/<str:token>/', views.verify_email_confirm, name='verify_email_confirm'),
    
    # User Management (Admin)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Social Authentication (if needed later)
    # path('social/google/', views.google_auth, name='google_auth'),
    # path('social/facebook/', views.facebook_auth, name='facebook_auth'),
]
