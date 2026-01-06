import os
import sys
from dotenv import load_dotenv
import secrets
import string

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app.extensions import get_supabase_admin
from app.services.catalog_service import create_item
from app.services.product_enrichment_service import enrich_product


# Test organization
ORG_NAME = "Acme Corporation"

# Test users to create (email, role, full_name)
TEST_USERS = [
    # Admins
    ("admin1@acmecorp.test", "admin", "Alice Admin"),
    ("admin2@acmecorp.test", "admin", "Bob Administrator"),
    ("admin3@acmecorp.test", "admin", "Carol Chief"),
    # Reviewers
    ("reviewer1@acmecorp.test", "reviewer", "Diana Reviewer"),
    ("reviewer2@acmecorp.test", "reviewer", "Eve Evaluator"),
    ("reviewer3@acmecorp.test", "reviewer", "Frank Finance"),
    # Requesters
    ("requester1@acmecorp.test", "requester", "Grace General"),
    ("requester2@acmecorp.test", "requester", "Henry HR"),
    ("requester3@acmecorp.test", "requester", "Iris IT"),
    ("requester4@acmecorp.test", "requester", "Jack Junior"),
]

# ============================================================================
# ENTERPRISE PRODUCT CATALOG (~100 items)
# ============================================================================

# LAPTOPS (16 items - best from each brand)
LAPTOPS = [
    # MacBooks (3)
    "MacBook Pro 16 inch M3 Max 48GB RAM 1TB",
    "MacBook Pro 14 inch M3 Pro 18GB RAM 512GB",
    "MacBook Air 15 inch M3 16GB RAM 512GB",
    # ThinkPads (4)
    "Lenovo ThinkPad X1 Carbon Gen 11 i7 32GB 1TB",
    "Lenovo ThinkPad X1 Yoga Gen 8 i7 16GB 512GB",
    "Lenovo ThinkPad T14s Gen 4 AMD Ryzen 7 32GB 1TB",
    "Lenovo ThinkPad P16s Gen 2 i7 32GB 1TB RTX A500",
    # Dell (3)
    "Dell XPS 15 9530 i7 32GB 1TB RTX 4060",
    "Dell Latitude 7440 i7 32GB 1TB",
    "Dell Precision 5680 i9 64GB 2TB RTX 4000 Ada",
    # HP (3)
    "HP EliteBook 840 G10 i7 32GB 1TB",
    "HP ZBook Studio G10 i9 64GB 2TB RTX 4080",
    "HP Dragonfly G4 i7 32GB 1TB",
    # Gaming/Creative (3)
    "ASUS ROG Zephyrus G14 2024 RTX 4070 AMD Ryzen 9 32GB 1TB",
    "Razer Blade 15 RTX 4070 i7 32GB 1TB",
    "MSI Creator Z17 HX Studio RTX 4080 i9 64GB 2TB",
]

# DESKTOPS (6 items)
DESKTOPS = [
    "Apple Mac Studio M2 Ultra 192GB 8TB",
    "Apple Mac Mini M2 Pro 32GB 1TB",
    "Apple iMac 24 inch M3 16GB 512GB",
    "Dell Precision 5860 Tower Xeon 64GB 2TB RTX 4000",
    "HP Z4 G5 Workstation Xeon 64GB 2TB RTX 4000 Ada",
    "Lenovo ThinkStation P5 Xeon 64GB 2TB RTX 4000",
]

# MONITORS (10 items)
MONITORS = [
    "Dell UltraSharp U2723QE 27 inch 4K USB-C Hub",
    "Dell UltraSharp U3423WE 34 inch Curved WQHD",
    "LG UltraFine 5K 27MD5KL-B 27 inch",
    "LG UltraWide 40WP95C-W 40 inch Curved 5K2K Thunderbolt",
    "Samsung ViewFinity S9 27 inch 5K Matte Display",
    "Apple Studio Display 27 inch 5K Standard glass",
    "Apple Pro Display XDR 32 inch 6K Standard glass",
    "ASUS ProArt PA32UCG-K 32 inch 4K Mini LED",
    "BenQ PD3225U 32 inch 4K Thunderbolt 3",
    "Eizo ColorEdge CG2700X 27 inch 4K HDR",
]

# KEYBOARDS (8 items)
KEYBOARDS = [
    "Apple Magic Keyboard with Touch ID and Numeric Keypad",
    "Logitech MX Keys S Wireless",
    "Logitech MX Mechanical Wireless Tactile",
    "Logitech Ergo K860 Split Wireless",
    "Keychron Q1 Pro QMK 75% Wireless",
    "HHKB Professional Hybrid Type-S",
    "Kinesis Advantage360 Pro Split",
    "ZSA Moonlander Mark I Split",
]

# MICE (8 items)
MICE = [
    "Logitech MX Master 3S Wireless",
    "Logitech MX Vertical Advanced Ergonomic",
    "Logitech MX Ergo Wireless Trackball",
    "Apple Magic Trackpad Multi-Touch",
    "Microsoft Surface Precision Mouse",
    "Razer Pro Click Wireless",
    "Kensington SlimBlade Pro Trackball",
    "3Dconnexion SpaceMouse Pro Wireless",
]

# HEADSETS (8 items)
HEADSETS = [
    "Jabra Evolve2 85 Wireless ANC",
    "Poly Voyager Focus 2 UC Wireless ANC",
    "Sony WH-1000XM5 Wireless ANC",
    "Bose QuietComfort Ultra Headphones",
    "Apple AirPods Max",
    "Apple AirPods Pro 2nd Gen USB-C",
    "EPOS IMPACT 1061 ANC Wireless",
    "Logitech Zone Wireless 2",
]

# WEBCAMS (5 items)
WEBCAMS = [
    "Logitech Brio 4K Pro Webcam",
    "Elgato Facecam Pro 4K60",
    "Dell UltraSharp Webcam WB7022",
    "Poly Studio P15 Personal Video Bar",
    "Jabra PanaCast 20 AI 4K Webcam",
]

# DOCKS (5 items)
DOCKS = [
    "CalDigit TS4 Thunderbolt 4 Dock 18-Port",
    "OWC Thunderbolt 4 Dock",
    "Belkin Thunderbolt 4 Dock Pro",
    "Dell Thunderbolt Dock WD22TB4",
    "Lenovo ThinkPad Thunderbolt 4 Dock",
]

# CHAIRS (8 items)
CHAIRS = [
    "Herman Miller Aeron Chair Size B Graphite",
    "Herman Miller Embody Chair Rhythm Fabric",
    "Steelcase Leap V2 Chair Fabric",
    "Steelcase Gesture Chair with Headrest",
    "Humanscale Freedom Chair with Headrest",
    "Secretlab Titan Evo 2022 Regular",
    "Haworth Fern Chair",
    "Branch Ergonomic Chair",
]

# DESKS (6 items)
DESKS = [
    "UPLIFT V2 Standing Desk 60x30 Bamboo",
    "Fully Jarvis Standing Desk 60x30 Bamboo",
    "Autonomous SmartDesk Pro 53x29",
    "Vari Electric Standing Desk 60x30",
    "Herman Miller Nevi Standing Desk",
    "Secretlab MAGNUS Pro",
]

# STORAGE (6 items)
STORAGE = [
    "Samsung T7 Shield Portable SSD 2TB",
    "SanDisk Extreme Pro Portable SSD 4TB",
    "LaCie Rugged SSD Pro 4TB Thunderbolt",
    "Synology DiskStation DS923+ NAS 4-Bay",
    "Samsung 990 Pro 4TB NVMe",
    "WD Black SN850X 4TB NVMe",
]

# PRINTERS (4 items)
PRINTERS = [
    "HP Color LaserJet Pro MFP M479fdw",
    "Brother MFC-L8900CDW Color Laser",
    "Epson EcoTank Pro ET-5880",
    "Fujitsu ScanSnap iX1600 Scanner",
]

# ============================================================================
# SAAS & SOFTWARE (deduplicated by purpose - ~40 items)
# ============================================================================

SAAS_PROJECT_MANAGEMENT = [
    "Jira Software Premium (per user/year)",
    "Asana Business (per user/year)",
    "Linear Standard (per user/year)",
]

SAAS_DOCUMENTATION = [
    "Confluence Premium (per user/year)",
    "Notion Team Plan (per user/year)",
]

SAAS_COMMUNICATION = [
    "Slack Business Plus (per user/year)",
    "Zoom Workplace Business (per user/year)",
    "Google Workspace Business Plus (per user/year)",
    "Microsoft 365 Business Premium (per user/year)",
]

SAAS_DESIGN = [
    "Figma Professional (per editor/year)",
    "Adobe Creative Cloud All Apps (per license/year)",
    "Canva for Teams (per user/year)",
    "Final Cut Pro",
]

SAAS_DEVELOPMENT = [
    "GitHub Enterprise Cloud (per user/year)",
    "GitLab Ultimate (per user/year)",
    "Vercel Pro (per member/year)",
    "AWS Reserved Instances (annual)",
    "Datadog Pro (per host/year)",
    "PagerDuty Business (per user/year)",
    "Sentry Team (per user/year)",
    "Snyk Team (per user/year)",
]

SAAS_CRM_SALES = [
    "Salesforce Sales Cloud Enterprise (per user/year)",
    "HubSpot Sales Hub Professional (per user/year)",
    "Zendesk Suite Professional (per user/year)",
    "Intercom (per seat/year)",
]

SAAS_HR_FINANCE = [
    "Workday HCM (per employee/year)",
    "BambooHR Pro (per employee/year)",
    "Rippling Unity (per employee/month)",
    "Greenhouse Recruiting Pro",
    "QuickBooks Online Advanced (annual)",
    "NetSuite ERP (per user/year)",
    "Expensify Control (per user/year)",
    "Ramp Corporate Card Platform",
]

SAAS_SECURITY = [
    "1Password Business (per user/year)",
    "Okta Workforce Identity Cloud (per user/year)",
    "CrowdStrike Falcon Pro (per endpoint/year)",
    "Cloudflare Zero Trust Enterprise",
    "Vanta Trust Management Platform",
]

# Combine all SaaS
SAAS_SERVICES = (
    SAAS_PROJECT_MANAGEMENT +
    SAAS_DOCUMENTATION +
    SAAS_COMMUNICATION +
    SAAS_DESIGN +
    SAAS_DEVELOPMENT +
    SAAS_CRM_SALES +
    SAAS_HR_FINANCE +
    SAAS_SECURITY
)

# Combine all hardware
HARDWARE_PRODUCTS = (
    LAPTOPS +
    DESKTOPS +
    MONITORS +
    KEYBOARDS +
    MICE +
    HEADSETS +
    WEBCAMS +
    DOCKS +
    CHAIRS +
    DESKS +
    STORAGE +
    PRINTERS
)


def generate_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(alphabet) for _ in range(16))


def create_test_user(email, password, full_name):
    supabase = get_supabase_admin()

    try:
        # Create user via Supabase Auth Admin API
        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "full_name": full_name
            }
        })

        if response.user:
            return response.user.id
        else:
            print(f"   Failed to create user {email}: No user returned")
            return None

    except Exception as e:
        print(f"   Failed to create user {email}: {str(e)}")
        return None


def seed_organization():
    supabase = get_supabase_admin()

    print("\n[ORG] Creating Organization...")

    # Check if org already exists
    existing = supabase.table('orgs').select('*').eq('name', ORG_NAME).execute()
    if existing.data:
        print(f"   Organization '{ORG_NAME}' already exists (ID: {existing.data[0]['id']})")
        return existing.data[0]

    # Create new org
    org_response = supabase.table('orgs').insert({
        'name': ORG_NAME
    }).execute()

    if not org_response.data:
        raise Exception("Failed to create organization")

    org = org_response.data[0]
    print(f"   Created: {org['name']} (ID: {org['id']})")
    return org


def seed_users(org_id):
    supabase = get_supabase_admin()

    print(f"\n[USERS] Creating {len(TEST_USERS)} Test Users...")

    user_map = {}

    for email, role, full_name in TEST_USERS:
        # Generate secure password
        password = generate_password()

        print(f"\n   Creating: {full_name} ({email}) - {role.upper()}")

        # Create user via Auth API
        user_id = create_test_user(email, password, full_name)
        if not user_id:
            continue

        user_map[email] = user_id
        print(f"   User created (ID: {user_id})")

        # Add to organization
        try:
            supabase.table('org_memberships').insert({
                'org_id': org_id,
                'user_id': user_id,
                'role': role
            }).execute()
            print(f"   Added to org with role: {role}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        except Exception as e:
            print(f"   Failed to add to org: {str(e)}")

    print(f"\n   Created {len(user_map)}/{len(TEST_USERS)} users successfully")
    return user_map


def seed_catalog_items(org_id, admin_user_id, use_ai=True):
    all_products = HARDWARE_PRODUCTS + SAAS_SERVICES
    total = len(all_products)

    print(f"\n[CATALOG] Seeding {total} Catalog Items...")
    print(f"   - {len(HARDWARE_PRODUCTS)} Hardware Products")
    print(f"   - {len(SAAS_SERVICES)} SaaS Services")

    if use_ai:
        print("\n   AI Enrichment: ENABLED (using Gemini)")
    else:
        print("\n   AI Enrichment: DISABLED (manual data only)")

    success_count = 0
    fail_count = 0

    for i, product_name in enumerate(all_products, 1):
        try:
            print(f"\n[{i}/{total}] {product_name}")

            if use_ai:
                # Use Gemini to enrich product
                enriched = enrich_product(product_name=product_name)

                print(f"   Vendor: {enriched.get('vendor', 'N/A')}")
                print(f"   Category: {enriched.get('category', 'N/A')}")
                if enriched.get('price'):
                    print(f"   Price: ${enriched.get('price'):.2f}")

                # Create catalog item with AI-enriched data
                item = create_item(
                    org_id=org_id,
                    name=enriched.get('name', product_name),
                    description=enriched.get('description', ''),
                    category=enriched.get('category', 'Uncategorized'),
                    created_by=admin_user_id,
                    price=enriched.get('price'),
                    pricing_type=enriched.get('pricing_type'),
                    vendor=enriched.get('vendor'),
                    sku=enriched.get('sku'),
                    product_url=enriched.get('product_url'),
                    metadata={
                        **enriched.get('metadata', {}),
                        'ai_enriched': True,
                        'ai_confidence': enriched.get('confidence', 'unknown'),
                        'seeded_at': 'automated_seed_script'
                    }
                )
            else:
                # Create with minimal data
                category = 'SaaS' if product_name in SAAS_SERVICES else 'Hardware'
                item = create_item(
                    org_id=org_id,
                    name=product_name,
                    description=f'Test item: {product_name}',
                    category=category,
                    created_by=admin_user_id,
                    metadata={'ai_enriched': False, 'seeded_at': 'automated_seed_script'}
                )

            print(f"   Created (ID: {item['id']})")
            success_count += 1

        except Exception as e:
            print(f"   Failed: {str(e)}")
            fail_count += 1

    print(f"\n   Catalog Seeding Complete: {success_count} succeeded, {fail_count} failed")


def seed_sample_requests(org_id, user_map):
    supabase = get_supabase_admin()

    # Get requester user IDs
    requesters = [
        user_map.get(email)
        for email, role, _ in TEST_USERS
        if role == 'requester' and email in user_map
    ]

    if not requesters:
        print("\n   No requester users found, skipping sample requests")
        return

    print("\n[REQUESTS] Creating Sample Requests...")

    sample_requests = [
        {
            'org_id': org_id,
            'created_by': requesters[0],
            'search_query': 'laptop for video editing',
            'justification': 'Need a powerful laptop for our video production team',
            'status': 'pending'
        },
        {
            'org_id': org_id,
            'created_by': requesters[1],
            'search_query': 'project management software',
            'justification': 'Current PM tools are insufficient for growing team',
            'status': 'pending'
        },
        {
            'org_id': org_id,
            'created_by': requesters[2] if len(requesters) > 2 else requesters[0],
            'search_query': 'ergonomic office chair',
            'justification': 'Employee wellness initiative for remote workers',
            'status': 'pending'
        },
    ]

    created = 0
    for req_data in sample_requests:
        try:
            response = supabase.table('requests').insert(req_data).execute()
            if response.data:
                print(f"   Created request: {req_data['search_query']}")
                created += 1
        except Exception as e:
            print(f"   Failed to create request: {str(e)}")

    print(f"\n   Created {created}/{len(sample_requests)} sample requests")


def clear_seeded_items(org_id):
    supabase = get_supabase_admin()

    print("\n[CLEAR] Removing previously seeded catalog items...")

    try:
        # Delete items that were created by the seed script
        response = supabase.table('catalog_items') \
            .delete() \
            .eq('org_id', org_id) \
            .eq('metadata->>seeded_at', 'automated_seed_script') \
            .execute()

        deleted_count = len(response.data) if response.data else 0
        print(f"   Deleted {deleted_count} seeded items")
        return deleted_count
    except Exception as e:
        print(f"   Failed to clear items: {str(e)}")
        return 0


def seed_items_only():
    print("=" * 70)
    print("CatalogAI - Regenerate Catalog Items")
    print("=" * 70)

    # Check for required environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("\nERROR: Missing required environment variables")
        return

    supabase = get_supabase_admin()

    # Check for Gemini API key
    gemini_key = os.getenv('GEMINI_API_KEY')
    use_ai = bool(gemini_key)

    if not use_ai:
        print("\nWARNING: GEMINI_API_KEY not found - AI enrichment disabled")
        resp = input("   Continue without AI enrichment? (y/n): ")
        if resp.lower() != 'y':
            return

    try:
        # Get existing org
        org_response = supabase.table('orgs').select('*').eq('name', ORG_NAME).execute()
        if not org_response.data:
            print(f"\nERROR: Organization '{ORG_NAME}' not found. Run full seed first.")
            return

        org = org_response.data[0]
        print(f"\nUsing organization: {ORG_NAME} (ID: {org['id']})")

        # Get an admin user
        memberships = supabase.table('org_memberships') \
            .select('user_id') \
            .eq('org_id', org['id']) \
            .eq('role', 'admin') \
            .limit(1) \
            .execute()

        if not memberships.data:
            print("\nERROR: No admin user found. Run full seed first.")
            return

        admin_user_id = memberships.data[0]['user_id']

        # Clear old seeded items
        clear_seeded_items(org['id'])

        # Seed new items
        seed_catalog_items(org['id'], admin_user_id, use_ai=use_ai)

        print("\n" + "=" * 70)
        print("CATALOG REGENERATION COMPLETE!")
        print("=" * 70)
        print(f"\nCatalog Items: {len(HARDWARE_PRODUCTS) + len(SAAS_SERVICES)}")
        print(f"   - {len(HARDWARE_PRODUCTS)} Hardware Products")
        print(f"   - {len(SAAS_SERVICES)} SaaS Services")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\nFAILED: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    print("=" * 70)
    print("CatalogAI Automated Seeding Script")
    print("=" * 70)

    # Check for required environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("\nERROR: Missing required environment variables")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        print("   Make sure .env file is configured correctly")
        return

    # Check for Gemini API key (optional, for AI enrichment)
    gemini_key = os.getenv('GEMINI_API_KEY')
    use_ai = bool(gemini_key)

    if not use_ai:
        print("\nWARNING: GEMINI_API_KEY not found - AI enrichment will be disabled")
        print("   Products will be created with minimal data")
        response = input("\n   Continue without AI enrichment? (y/n): ")
        if response.lower() != 'y':
            print("\nAborted. Set GEMINI_API_KEY in .env to enable AI enrichment.")
            return

    try:
        # 1. Create organization
        org = seed_organization()

        # 2. Create users and add to org
        user_map = seed_users(org['id'])

        if not user_map:
            print("\nNo users created. Cannot proceed with seeding.")
            return

        # Get first admin user for catalog item creation
        admin_user_id = next(
            (uid for email, uid in user_map.items()
             if any(e == email and r == 'admin' for e, r, _ in TEST_USERS)),
            None
        )

        if not admin_user_id:
            print("\nNo admin user found. Cannot create catalog items.")
            return

        # 3. Seed catalog items
        seed_catalog_items(org['id'], admin_user_id, use_ai=use_ai)

        # 4. Create sample requests
        seed_sample_requests(org['id'], user_map)

        # Summary
        print("\n" + "=" * 70)
        print("SEEDING COMPLETE!")
        print("=" * 70)
        print(f"\nOrganization: {ORG_NAME}")
        print(f"   ID: {org['id']}")
        print(f"\nUsers Created: {len(user_map)}")
        print(f"   - {sum(1 for _, r, _ in TEST_USERS if r == 'admin')} Admins")
        print(f"   - {sum(1 for _, r, _ in TEST_USERS if r == 'reviewer')} Reviewers")
        print(f"   - {sum(1 for _, r, _ in TEST_USERS if r == 'requester')} Requesters")
        print(f"\nCatalog Items: {len(HARDWARE_PRODUCTS) + len(SAAS_SERVICES)}")
        print(f"   - {len(HARDWARE_PRODUCTS)} Hardware Products")
        print(f"   - {len(SAAS_SERVICES)} SaaS Services")
        print("\nUser Credentials:")
        print("   (See output above for email/password combinations)")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\nSEEDING FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Seed CatalogAI database')
    parser.add_argument('--items-only', action='store_true',
                        help='Only regenerate catalog items (clears old seeded items first)')
    args = parser.parse_args()

    if args.items_only:
        seed_items_only()
    else:
        main()
