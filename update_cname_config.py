"""
CNAME Configuration Update Script for NextSlot Custom Domains
Updates CNAME records for service provider domains to point to Cloudflare
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from django.conf import settings
from providers.models import ServiceProvider
from providers.domain_utils import (
    generate_unique_cname_target,
    generate_unique_txt_record_name,
)

def update_cname_records():
    """Update CNAME/TXT instructions for all service providers.

    Uses per-provider CNAME targets based on their booking slug:
        {unique_booking_url}.{PROVIDER_SUBDOMAIN_BASE}
    Example: okmentor.nextslot.in
    """

    base_domain = getattr(settings, 'PROVIDER_SUBDOMAIN_BASE', 'nextslot.in')

    print("\n" + "=" * 70)
    print("CNAME CONFIGURATION UPDATE FOR SERVICE PROVIDERS")
    print("=" * 70 + "\n")

    providers_with_domains = (
        ServiceProvider.objects.filter(custom_domain__isnull=False)
        .exclude(custom_domain='')
    )

    if not providers_with_domains.exists():
        print("✗ No providers with custom domains found")
        return

    print(f"Found {providers_with_domains.count()} provider(s) with custom domains\n")

    for provider in providers_with_domains:
        cname_target = generate_unique_cname_target(provider)
        txt_name = generate_unique_txt_record_name(provider)

        print(f"Provider: {provider.business_name}")
        print(f"Custom Domain: {provider.custom_domain}")
        print(f"Domain Type: {provider.custom_domain_type}")
        print(f"Domain Verified: {provider.domain_verified}")
        print(f"SSL Enabled: {provider.ssl_enabled}")
        print("\n📋 REQUIRED DNS RECORDS:")
        print("-" * 70)

        # CNAME Record
        print("\n1️⃣  CNAME RECORD:")
        print(f"   Name/Host: {provider.custom_domain}")
        print("   Type: CNAME")
        print(f"   Value/Target: {cname_target}")
        print("   TTL: 3600 (Auto)")

        # TXT Record for verification
        print("\n2️⃣  TXT RECORD (Domain verification):")
        print(f"   Name: {txt_name}.{provider.custom_domain}")
        print("   Type: TXT")
        print("   Value: (unique code provided in dashboard)")
        print("   TTL: 3600")

        # Persist targets to provider record
        updates = []
        if provider.cname_target != cname_target:
            provider.cname_target = cname_target
            updates.append('cname_target')
        if provider.txt_record_name != txt_name:
            provider.txt_record_name = txt_name
            updates.append('txt_record_name')
        if updates:
            provider.save(update_fields=updates)
            print(f"\n✅ Updated provider records: {', '.join(updates)}")
        else:
            print("\n✓ DNS targets already up to date")

        print("\n📝 SETUP INSTRUCTIONS:")
        print("-" * 70)
        print(
            """
1. Login to your domain registrar (GoDaddy, Namecheap, etc.)
2. Go to DNS Settings
3. Remove conflicting A/ALIAS records for the root if present
4. Add the CNAME record above pointing to your unique target
5. Add the TXT record for verification
6. Wait for DNS propagation (5-30 minutes)
7. SSL will be auto-provisioned by the platform/Let's Encrypt

✨ After DNS is set up, your domain will work once verification succeeds!
"""
        )

        print("\n" + "=" * 70 + "\n")

    print("\n📌 QUICK REFERENCE - CNAME TARGET FORMAT:")
    print("=" * 70)
    print(
        "Each provider should point their custom domain to:"
        f" <provider-slug>.{base_domain}"
    )
    print("Example: ramesh-salon." + base_domain)
    print("=" * 70 + "\n")

if __name__ == "__main__":
    update_cname_records()
