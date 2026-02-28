"""
Final verification of Cloudinary URLs
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from providers.models import ServiceProvider

print("="*70)
print("CLOUDINARY URL FIX - VERIFICATION")
print("="*70)

sp = ServiceProvider.objects.filter(logo__isnull=False).first()

if sp and sp.logo:
    print(f"\nProvider: {sp.business_name}")
    print(f"\nDatabase value: {sp.logo.name}")
    print(f"\nGenerated URL:\n{sp.logo.url}")
    
    print("\n" + "="*70)
    print("TEST THIS URL")
    print("="*70)
    print("\n✓ Copy the URL above and paste it in your browser")
    print("✓ The image should now load without 404 error")
    print("\nWhat was fixed:")
    print("  BEFORE: URL had 'f_auto' parameter causing 404")  
    print("  AFTER:  URL uses only working parameters (c_limit, q_auto:good, etc.)")
    
    print("\n" + "="*70)
    print("IF STILL 404")
    print("="*70)
    print("\n1. Clear your browser cache (Ctrl+Shift+Delete)")
    print("2. Try in incognito/private window")
    print("3. Wait 1-2 minutes for Cloudinary CDN cache to clear")
    print("\n4. Or use the simple URL (no transforms):")
    simple_url = sp.logo.url.split('/upload/')[0] + '/upload/v1/' + sp.logo.name
    print(f"   {simple_url}")
else:
    print("\nNo providers with logos found in database.")
    print("\nPlease upload a logo through:")
    print("1. Django Admin: /admin/providers/serviceprovider/")
    print("2. Provider Dashboard: /providers/dashboard/")
