from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product
from orders.models import Order, OrderItem
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for development'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample categories
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Clothing', 'description': 'Fashion and apparel'},
            {'name': 'Books', 'description': 'Books and educational materials'},
            {'name': 'Home & Garden', 'description': 'Home improvement and garden supplies'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': cat_data['name'].lower().replace(' ', '-'),
                    'description': cat_data['description']
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create sample products
        for i in range(20):
            category = random.choice(categories)
            product, created = Product.objects.get_or_create(
                name=f'Sample Product {i+1}',
                defaults={
                    'slug': f'sample-product-{i+1}',
                    'description': f'This is a sample product {i+1} description.',
                    'short_description': f'Sample product {i+1}',
                    'category': category,
                    'price': random.uniform(10, 500),
                    'stock_quantity': random.randint(0, 100),
                    'sku': f'SP{i+1:03d}',
                    'is_featured': random.choice([True, False])
                }
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        # Create sample user
        if not User.objects.filter(email='demo@example.com').exists():
            user = User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo123',
                first_name='Demo',
                last_name='User'
            )
            self.stdout.write('Created demo user (demo@example.com / demo123)')
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
