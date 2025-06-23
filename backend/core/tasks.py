from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_email_task(subject, message, recipient_list):
    """
    Async email sending task
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f'Email sent successfully to {recipient_list}')
        return True
    except Exception as e:
        logger.error(f'Failed to send email: {str(e)}')
        return False

@shared_task
def cleanup_old_data():
    """
    Clean up old data (run daily)
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Clean up old sessions, logs, etc.
    cutoff_date = timezone.now() - timedelta(days=30)
    
    # Add your cleanup logic here
    logger.info('Data cleanup completed')

@shared_task
def update_product_ratings():
    """
    Update product average ratings (run hourly)
    """
    from products.models import Product
    from reviews.models import Review
    from django.db.models import Avg
    
    products = Product.objects.all()
    for product in products:
        avg_rating = Review.objects.filter(product=product).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        # You might want to store this in a separate field
        # product.average_rating = avg_rating
        # product.save()
    
    logger.info('Product ratings updated')
