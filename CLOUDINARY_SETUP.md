# Cloudinary Image Hosting Setup Guide

This guide explains how to set up Cloudinary for image hosting in your booking application, replacing the local/DigitalOcean Spaces storage.

## Overview

Cloudinary provides:
- **Automatic image optimization** (format conversion, quality adjustment)
- **CDN delivery** for fast loading globally
- **Transformations** (resize, crop, filters) via URL parameters
- **Secure storage** with backup and redundancy
- **Cost-effective** pay-as-you-go pricing

## Setup Steps

### 1. Create Cloudinary Account

1. Sign up at [cloudinary.com](https://cloudinary.com)
2. Choose the **Free** plan (sufficient for development)
3. Verify your email address

### 2. Get Cloudinary Credentials

From your Cloudinary dashboard:
1. Go to **Settings** → **Account**
2. Copy your **Cloud Name**
3. Go to **Settings** → **Security**
4. Copy your **API Key** and **API Secret**

### 3. Configure Environment Variables

Add these to your `.env` file:

```bash
# Enable Cloudinary
USE_CLOUDINARY=True

# Cloudinary Credentials
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_FOLDER=booking_app

# Disable DigitalOcean Spaces
USE_DO_SPACES=False
```

### 4. Install Dependencies

```bash
pip install cloudinary>=1.36.0 django-cloudinary-storage>=0.3.0
```

### 5. Update Django Settings

The settings are already configured in `booking_saas/settings.py`:
- Cloudinary is added to `INSTALLED_APPS`
- Storage backend is set to `CloudinaryMediaStorage`
- Automatic image transformations are enabled

### 6. Migrate Existing Images (Optional)

If you have existing images in DigitalOcean Spaces:

```python
# Run this script to migrate images to Cloudinary
python manage.py shell
```

```python
from providers.models import ServiceProvider, HeroImage, TeamMember, Testimonial
import cloudinary.uploader

def migrate_to_cloudinary():
    # Migrate ServiceProvider images
    for provider in ServiceProvider.objects.all():
        if provider.logo and hasattr(provider.logo, 'url'):
            try:
                result = cloudinary.uploader.upload(
                    provider.logo.url,
                    public_id=f"provider_logos/{provider.id}_logo",
                    folder="booking_app"
                )
                provider.logo = result['public_id']
                provider.save()
                print(f"Migrated logo for {provider.business_name}")
            except Exception as e:
                print(f"Failed to migrate logo for {provider.business_name}: {e}")
    
    # Migrate Hero Images
    for hero in HeroImage.objects.all():
        if hero.image and hasattr(hero.image, 'url'):
            try:
                result = cloudinary.uploader.upload(
                    hero.image.url,
                    public_id=f"hero_images/{hero.id}_image",
                    folder="booking_app"
                )
                hero.image = result['public_id']
                hero.save()
                print(f"Migrated hero image for {hero.service_provider.business_name}")
            except Exception as e:
                print(f"Failed to migrate hero image: {e}")
    
    # Migrate Team Photos
    for member in TeamMember.objects.all():
        if member.photo and hasattr(member.photo, 'url'):
            try:
                result = cloudinary.uploader.upload(
                    member.photo.url,
                    public_id=f"team_photos/{member.id}_photo",
                    folder="booking_app"
                )
                member.photo = result['public_id']
                member.save()
                print(f"Migrated photo for {member.name}")
            except Exception as e:
                print(f"Failed to migrate photo for {member.name}: {e}")
    
    # Migrate Testimonial Photos
    for testimonial in Testimonial.objects.all():
        if testimonial.client_photo and hasattr(testimonial.client_photo, 'url'):
            try:
                result = cloudinary.uploader.upload(
                    testimonial.client_photo.url,
                    public_id=f"testimonial_photos/{testimonial.id}_photo",
                    folder="booking_app"
                )
                testimonial.client_photo = result['public_id']
                testimonial.save()
                print(f"Migrated photo for {testimonial.client_name}")
            except Exception as e:
                print(f"Failed to migrate photo for {testimonial.client_name}: {e}")

# Run the migration
migrate_to_cloudinary()
```

## Cloudinary Features

### Automatic Optimization

Images are automatically optimized:
- **Format conversion**: WebP for supported browsers, JPEG as fallback
- **Quality adjustment**: `auto:good` quality for balance
- **Size limits**: Max 2000x2000px to prevent oversized uploads

### URL Transformations

You can modify images via URL parameters:

```html
<!-- Original image -->
<img src="https://res.cloudinary.com/your-cloud/image/upload/booking_app/image.jpg">

<!-- Resized to 300x300 -->
<img src="https://res.cloudinary.com/your-cloud/image/upload/w_300,h_300/booking_app/image.jpg">

<!-- Circular crop -->
<img src="https://res.cloudinary.com/your-cloud/image/upload/w_150,h_150,c_fill,r_max/booking_app/image.jpg">

<!-- Grayscale filter -->
<img src="https://res.cloudinary.com/your-cloud/image/upload/e_grayscale/booking_app/image.jpg">
```

### Storage Classes

The app includes three storage classes:

1. **CloudinaryMediaStorage**: Default for all media files
2. **CloudinaryThumbnailStorage**: For thumbnails (300x300 with smart crop)
3. **CloudinaryStorage**: Base class with no transformations

## Benefits Over Local Storage

| Feature | Local Storage | Cloudinary |
|---------|---------------|------------|
| **Performance** | Server-dependent | Global CDN |
| **Scalability** | Limited disk space | Unlimited cloud storage |
| **Optimization** | Manual | Automatic |
| **Transformations** | None | URL-based |
| **Backup** | Manual | Automatic |
| **Cost** | Server storage costs | Pay-as-you-go |

## Testing the Setup

1. **Upload Test Image**:
   ```python
   from django.core.files.uploadedfile import SimpleUploadedFile
   from providers.models import ServiceProvider
   
   # Create test image
   test_image = SimpleUploadedFile(
       "test.jpg", 
       b"fake_image_data", 
       content_type="image/jpeg"
   )
   
   # Upload to Cloudinary
   provider = ServiceProvider.objects.first()
   provider.logo = test_image
   provider.save()
   
   # Check the URL
   print(provider.logo.url)
   ```

2. **Verify URL Format**:
   Should return: `https://res.cloudinary.com/your-cloud/image/auto/booking_app/...`

## Troubleshooting

### Common Issues

1. **"Invalid cloud name" error**
   - Check `CLOUDINARY_CLOUD_NAME` in `.env`
   - Verify Cloudinary account is active

2. **"Invalid credentials" error**
   - Check `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET`
   - Ensure API keys have proper permissions

3. **Images not displaying**
   - Check `USE_CLOUDINARY=True` in settings
   - Verify `CLOUDINARY_FOLDER` matches your Cloudinary folder

4. **Upload failures**
   - Check file size limits (Cloudinary free tier: 10MB per file)
   - Verify file format is supported (JPG, PNG, GIF, WebP)

### Debug Mode

Enable debug output by setting `DEBUG=True` in settings. You'll see:
- Which storage backend is being used
- Cloudinary configuration values
- Upload URLs and public IDs

## Production Considerations

1. **Security**: API secrets are never exposed in URLs
2. **Performance**: All images served via Cloudinary CDN
3. **Cost**: Free tier includes 25 credits/month (sufficient for most apps)
4. **Backup**: Cloudinary provides automatic redundancy

## Switching Back

To switch back to local storage:
```bash
# In .env
USE_CLOUDINARY=False
USE_DO_SPACES=False
```

The app will fall back to local/database storage automatically.

## Support

- Cloudinary Documentation: [cloudinary.com/docs](https://cloudinary.com/docs)
- Django Integration: [cloudinary.com/documentation/django_integration](https://cloudinary.com/documentation/django_integration)
- Free Tier Limits: [cloudinary.com/pricing](https://cloudinary.com/pricing)
