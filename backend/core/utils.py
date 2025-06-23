import uuid
import os
from PIL import Image
from django.core.files.storage import default_storage
from django.conf import settings

def generate_unique_filename(instance, filename):
    """
    Generate a unique filename for uploaded files
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return filename

def compress_image(image_field, max_size=(800, 800), quality=85):
    """
    Compress uploaded images
    """
    if not image_field:
        return
    
    image = Image.open(image_field)
    
    # Convert to RGB if necessary
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    # Resize image
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save compressed image
    from io import BytesIO
    temp_handle = BytesIO()
    image.save(temp_handle, 'JPEG', quality=quality)
    temp_handle.seek(0)
    
    return temp_handle

def send_notification_email(user, subject, message):
    """
    Send notification email to user
    """
    from django.core.mail import send_mail
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def generate_order_number():
    """
    Generate unique order number
    """
    import time
    timestamp = str(int(time.time()))
    random_part = uuid.uuid4().hex[:6].upper()
    return f"ORD-{timestamp[-6:]}-{random_part}"

def calculate_discounted_price(original_price, discount_percentage):
    """
    Calculate discounted price
    """
    discount_amount = original_price * (discount_percentage / 100)
    return original_price - discount_amount

class PaginationMixin:
    """
    Common pagination settings
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
