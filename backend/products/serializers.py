from rest_framework import serializers
from .models import Product, Category, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    category = serializers.StringRelatedField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'category',
            'price', 'compare_price', 'primary_image', 'average_rating',
            'review_count', 'is_featured', 'is_in_stock', 'discount_percentage'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        return None

class ProductSerializer(serializers.ModelSerializer):
    """Detailed serializer for product detail"""
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'price', 'compare_price', 'stock_quantity',
            'sku', 'weight', 'dimensions', 'images', 'average_rating',
            'review_count', 'is_featured', 'is_in_stock', 'discount_percentage',
            'meta_title', 'meta_description', 'created_at'
        ]

class AdminProductSerializer(serializers.ModelSerializer):
    """Serializer for admin product management"""
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['slug', 'created_at']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        product = Product.objects.create(**validated_data)
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        instance = super().update(instance, validated_data)
        
        # Update images
        if images_data is not None:
            existing_images = instance.images.all()
            existing_ids = set(img.id for img in existing_images)
            new_ids = set()
            
            for image_data in images_data:
                img_id = image_data.get('id', None)
                if img_id:
                    new_ids.add(img_id)
                    try:
                        img = existing_images.get(id=img_id)
                        for attr, value in image_data.items():
                            setattr(img, attr, value)
                        img.save()
                    except ProductImage.DoesNotExist:
                        continue
                else:
                    ProductImage.objects.create(product=instance, **image_data)
            
            # Delete images not in the new set
            for img in existing_images:
                if img.id not in new_ids:
                    img.delete()
        
        return instance
