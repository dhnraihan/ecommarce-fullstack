from django.db import models
from rest_framework import serializers

class UserQuerySetMixin:
    """
    Mixin to filter queryset by current user
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)

class TimestampSerializerMixin:
    """
    Mixin to add timestamp fields to serializers
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

class UserSerializerMixin:
    """
    Mixin to automatically set user field
    """
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class SoftDeleteQuerySet(models.QuerySet):
    """
    Custom QuerySet for soft delete functionality
    """
    def delete(self):
        from django.utils import timezone
        return self.update(is_deleted=True, deleted_at=timezone.now())
    
    def hard_delete(self):
        return super().delete()
    
    def alive(self):
        return self.filter(is_deleted=False)
    
    def dead(self):
        return self.filter(is_deleted=True)

class SoftDeleteManager(models.Manager):
    """
    Custom Manager for soft delete functionality
    """
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super().__init__(*args, **kwargs)
    
    def get_queryset(self):
        if self.alive_only:
            return SoftDeleteQuerySet(self.model).filter(is_deleted=False)
        return SoftDeleteQuerySet(self.model)
    
    def hard_delete(self):
        return self.get_queryset().hard_delete()
