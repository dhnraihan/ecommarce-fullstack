import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

def validate_phone_number(value):
    """
    Validate phone number format
    """
    phone_regex = re.compile(r'^\+?1?\d{9,15}$')
    if not phone_regex.match(value):
        raise ValidationError('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')

def validate_rating(value):
    """
    Validate rating is between 1 and 5
    """
    if value < 1 or value > 5:
        raise ValidationError('Rating must be between 1 and 5.')

def validate_positive_decimal(value):
    """
    Validate positive decimal values
    """
    if value <= 0:
        raise ValidationError('Value must be positive.')

def validate_image_size(image):
    """
    Validate image file size (max 5MB)
    """
    max_size = 5 * 1024 * 1024  # 5MB
    if image.size > max_size:
        raise ValidationError('Image file too large ( > 5MB )')

def validate_image_format(image):
    """
    Validate image format
    """
    valid_formats = ['JPEG', 'JPG', 'PNG', 'WEBP']
    if image.image.format not in valid_formats:
        raise ValidationError('Unsupported image format. Use JPEG, PNG, or WEBP.')

# Regex validators
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

slug_validator = RegexValidator(
    regex=r'^[-a-zA-Z0-9_]+$',
    message='Slug can only contain letters, numbers, hyphens, and underscores.'
)
