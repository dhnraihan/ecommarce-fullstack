from rest_framework import serializers
from .models import Review, ReviewImage
from apps.accounts.serializers import UserSerializer

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'rating', 'title', 'content', 'is_verified_purchase',
            'helpful_count', 'images', 'can_edit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'helpful_count', 'is_verified_purchase']
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'content']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['product_id'] = self.context['product_id']
        return super().create(validated_data)
