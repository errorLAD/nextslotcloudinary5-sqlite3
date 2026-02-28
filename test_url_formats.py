"""
Test Cloudinary URL generation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

import cloudinary
from cloudinary import CloudinaryImage
from django.conf import settings

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

public_id = 'booking_app/provider_logos1_Black-and-Grey-Clean-Modern-Minima_d5f261e9'

print("Testing different URL formats:")
print("="*60)

# Simple URL
img = CloudinaryImage(public_id)
url1 = img.build_url(secure=True)
print(f"\n1. Simple URL:\n   {url1}")

# With quality
url2 = img.build_url(secure=True, quality='auto:good')
print(f"\n2. With quality:\n   {url2}")

# With transformations
url3 = img.build_url(secure=True, quality='auto:good', width=500, crop='limit')
print(f"\n3. With width limit:\n   {url3}")

# Current format (what storage uses)
url4 = img.build_url(
    secure=True,
    resource_type='image',
    quality='auto:good',
    fetch_format='auto',
    crop='limit',
    width=2000,
    height=2000
)
print(f"\n4. Current format (storage backend):\n   {url4}")

print("\n" + "="*60)
print("SOLUTION:")
print("="*60)
print("\nThe issue is 'f_auto' in the URL. Try these URLs in your browser:")
print(f"\n1. Direct URL (should work):\n   {url1}")
print(f"\n2. Copy and paste this URL to test:\n   {url1}")
print("\nIf URL #1 works, the storage backend needs to be updated.")
