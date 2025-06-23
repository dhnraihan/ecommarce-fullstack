from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.orders.models import Order
from apps.products.models import Product
from .utils import send_notification_email

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile when user is created
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """
    Send notification when order status changes
    """
    if not created:
        # Check if status was changed
        old_instance = Order.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            subject = f"Order {instance.order_number} Status Updated"
            message = f"Your order status has been changed to: {instance.get_status_display()}"
            send_notification_email(instance.user, subject, message)

@receiver(post_save, sender=Order)
def order_created_notification(sender, instance, created, **kwargs):
    """
    Send notification when new order is created
    """
    if created:
        subject = f"Order Confirmation - {instance.order_number}"
        message = f"Thank you for your order! Your order number is {instance.order_number}"
        send_notification_email(instance.user, subject, message)

@receiver(pre_delete, sender=Product)
def product_deletion_cleanup(sender, instance, **kwargs):
    """
    Clean up related data when product is deleted
    """
    # Delete product images from storage
    for image in instance.images.all():
        if image.image:
            image.image.delete(save=False)
