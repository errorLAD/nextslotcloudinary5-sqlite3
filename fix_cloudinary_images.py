"""
Fix Cloudinary image URLs and verify images exist.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

import cloudinary
import cloudinary.api
from django.conf import settings
from providers.models import ServiceProvider

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

print("="*60)
print("Cloudinary Image Verification and Fix")
print("="*60)

# List all images in Cloudinary
print("\n1. Checking images in Cloudinary...")
try:
    resources = cloudinary.api.resources(
        type='upload',
        prefix='booking_app/',
        max_results=100
    )
    
    cloudinary_images = {}
    for resource in resources.get('resources', []):
        public_id = resource['public_id']
        cloudinary_images[public_id] = resource
        print(f"   Found: {public_id}")
    
    print(f"\n   Total images in Cloudinary: {len(cloudinary_images)}")
except Exception as e:
    print(f"   Error listing Cloudinary images: {e}")
    cloudinary_images = {}

# Check database images
print("\n2. Checking images in database...")
providers_with_logos = ServiceProvider.objects.exclude(logo='').exclude(logo__isnull=True)
print(f"   Providers with logos: {providers_with_logos.count()}")

for provider in providers_with_logos:
    print(f"\n   Provider: {provider.business_name}")
    print(f"   Logo field value: {provider.logo.name}")
    
    # Check if image exists in Cloudinary
    public_id = provider.logo.name
    
    if public_id in cloudinary_images:
        print(f"   [OK] Image exists in Cloudinary")
        print(f"   URL: {provider.logo.url}")
    else:
        print(f"   [WARNING] Image NOT found in Cloudinary")
        print(f"   Searching for similar images...")
        
        # Try to find similar images
        search_term = os.path.basename(public_id).split('_')[0]
        found_similar = False
        
        for cld_id in cloudinary_images.keys():
            if search_term.lower() in cld_id.lower():
                print(f"   [FOUND] Similar image: {cld_id}")
                found_similar = True
        
        if not found_similar:
            print(f"   [ERROR] No similar images found")
            print(f"   Action needed: Re-upload the logo for this provider")

# Provide fix instructions
print("\n" + "="*60)
print("SOLUTION")
print("="*60)

if not cloudinary_images:
    print("""
The images are not in Cloudinary yet. You need to:

1. Go to Django Admin or your provider dashboard
2. Re-upload the logo image
3. The image will automatically upload to Cloudinary

OR manually upload via shell:
    python manage.py shell
    >>> from providers.models import ServiceProvider
    >>> sp = ServiceProvider.objects.first()
    >>> # Re-save to trigger upload
    >>> if sp.logo:
    >>>     sp.save()
""")
else:
    print("""
Images found in Cloudinary. If URLs still show 404:

1. The URL format has been fixed (no more .auto extension)
2. Try accessing the image URL again
3. If still 404, the public_id might be mismatched

To re-upload all images:
    python manage.py shell
    >>> from providers.models import ServiceProvider
    >>> for sp in ServiceProvider.objects.filter(logo__isnull=False):
    >>>     if sp.logo:
    >>>         # This will re-upload to Cloudinary
    >>>         sp.save()
""")

print("\nUpdated URL format (without .auto extension):")
sp = ServiceProvider.objects.filter(logo__isnull=False).first()
if sp and sp.logo:
    print(f"  {sp.logo.url}")
