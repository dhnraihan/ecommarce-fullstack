from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .models import User, UserProfile
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer, UserProfileSerializer, UserListSerializer
)

User = get_user_model()

# Authentication Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        self.send_verification_email(request, user)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User registered successfully. Please check your email to verify your account.',
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    
    def send_verification_email(self, request, user):
        current_site = get_current_site(request)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        verification_url = f"http://{current_site.domain}/api/auth/verify-email-confirm/{uid}/{token}/"
        
        subject = 'Verify Your Email Address'
        message = render_to_string('emails/verify_email.html', {
            'user': user,
            'verification_url': verification_url,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Login successful',
        'user': UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logout successful'})
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

# User Profile Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({
        'message': 'Profile updated successfully',
        'user': serializer.data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    
    return Response({'message': 'Password changed successfully'})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_avatar(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if 'avatar' in request.FILES:
        profile.avatar = request.FILES['avatar']
        profile.save()
        
        return Response({
            'message': 'Avatar uploaded successfully',
            'avatar_url': profile.avatar.url if profile.avatar else None
        })
    
    return Response({'error': 'No avatar file provided'}, status=status.HTTP_400_BAD_REQUEST)

# Password Reset Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset(request):
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    try:
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Send password reset email
        current_site = get_current_site(request)
        reset_url = f"http://{current_site.domain}/reset-password/{uid}/{token}/"
        
        subject = 'Password Reset Request'
        message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return Response({'message': 'Password reset email sent successfully'})
    except User.DoesNotExist:
        # Don't reveal if email exists
        return Response({'message': 'Password reset email sent successfully'})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request, uid, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            serializer = PasswordResetConfirmSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user.set_password(serializer.validated_data['password'])
            user.save()
            
            return Response({'message': 'Password reset successful'})
        else:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

# Email Verification Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_verification_email(request):
    user = request.user
    if user.is_verified:
        return Response({'message': 'Email already verified'})
    
    current_site = get_current_site(request)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_url = f"http://{current_site.domain}/api/auth/verify-email-confirm/{uid}/{token}/"
    
    subject = 'Verify Your Email Address'
    message = render_to_string('emails/verify_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    
    return Response({'message': 'Verification email sent successfully'})

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email_confirm(request, uid, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            
            return Response({'message': 'Email verified successfully'})
        else:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

# Admin User Management Views
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return queryset.order_by('-date_joined')

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def toggle_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    
    status_text = 'activated' if user.is_active else 'deactivated'
    return Response({
        'message': f'User {status_text} successfully',
        'is_active': user.is_active
    })
