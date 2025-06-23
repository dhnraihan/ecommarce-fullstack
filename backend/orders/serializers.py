from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'total_amount', 'status', 'shipping_address',
            'billing_address', 'phone', 'email', 'payment_method', 'payment_status',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']

class CreateOrderSerializer(serializers.ModelSerializer):
    items = serializers.ListField(write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'shipping_address', 'billing_address', 'phone', 'email',
            'payment_method', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        validated_data['user'] = self.context['request'].user
        
        # Generate order number
        import uuid
        validated_data['order_number'] = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total
        total = 0
        for item_data in items_data:
            total += item_data['price'] * item_data['quantity']
        validated_data['total_amount'] = total
        
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        return order
