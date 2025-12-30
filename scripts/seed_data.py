"""
Automated seeding script for CatalogAI.

Creates a test organization with:
- 10 test users (3 admins, 3 reviewers, 4 requesters)
- 20 hardware products (laptops, accessories, furniture, office supplies)
- 10 SaaS services (software subscriptions)
- Sample requests and proposals

Fully automated - no manual steps required.
"""
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

# Hardware products (20 items)
HARDWARE_PRODUCTS = [
    # Laptops & Computers
    "MacBook Pro 16 inch M3 Max",
    "Dell XPS 15 9530",
    "Lenovo ThinkPad X1 Carbon Gen 11",
    "HP EliteBook 840 G10",
    # Peripherals
    "Logitech MX Master 3S",
    "Apple Magic Keyboard",
    "Dell UltraSharp U2723DE 27 inch Monitor",
    "Jabra Evolve2 65 Headset",
    # Office Furniture
    "Herman Miller Aeron Chair Size B",
    "Steelcase Leap V2 Chair",
    "UPLIFT V2 Standing Desk 60x30",
    "Fully Jarvis Bamboo Standing Desk",
    # Office Equipment
    "HP OfficeJet Pro 9015e Printer",
    "Brother HL-L2395DW Laser Printer",
    "Fellowes Powershred 99Ci Shredder",
    # Office Supplies
    "Staples Copy Paper 8.5x11 10 Ream Case",
    "Sharpie Permanent Markers Assorted 12 Pack",
    "Post-it Notes Super Sticky 3x3 24 Pads",
    # Storage & Accessories
    "Samsung T7 Portable SSD 1TB",
    "WD My Book Desktop Hard Drive 8TB",
]

# SaaS Services (10 items)
SAAS_SERVICES = [
    "Slack Business Plus",
    "GitHub Enterprise Cloud",
    "Zoom Workspace Pro",
    "Notion Team Plan",
    "Figma Professional",
    "Jira Software Premium",
    "Confluence Premium",
    "Google Workspace Business Standard",
    "Microsoft 365 Business Premium",
    "Salesforce Professional Edition",
]


def generate_password():
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(alphabet) for _ in range(16))


def create_test_user(email, password, full_name):
    """
    Create a test user via Supabase Auth API.

    Returns user_id on success, None on failure.
    """
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
            print(f"   ❌ Failed to create user {email}: No user returned")
            return None

    except Exception as e:
        print(f"   ❌ Failed to create user {email}: {str(e)}")
        return None


def seed_organization():
    """Create test organization."""
    supabase = get_supabase_admin()

    print("\n📦 Creating Organization...")

    # Check if org already exists
    existing = supabase.table('orgs').select('*').eq('name', ORG_NAME).execute()
    if existing.data:
        print(f"   ⚠️  Organization '{ORG_NAME}' already exists (ID: {existing.data[0]['id']})")
        return existing.data[0]

    # Create new org
    org_response = supabase.table('orgs').insert({
        'name': ORG_NAME
    }).execute()

    if not org_response.data:
        raise Exception("Failed to create organization")

    org = org_response.data[0]
    print(f"   ✅ Created: {org['name']} (ID: {org['id']})")
    return org


def seed_users(org_id):
    """
    Create test users and add them to the organization.

    Returns dict mapping email -> user_id
    """
    supabase = get_supabase_admin()

    print(f"\n👥 Creating {len(TEST_USERS)} Test Users...")

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
        print(f"   ✅ User created (ID: {user_id})")

        # Add to organization
        try:
            supabase.table('org_memberships').insert({
                'org_id': org_id,
                'user_id': user_id,
                'role': role
            }).execute()
            print(f"   ✅ Added to org with role: {role}")
            print(f"   📧 Email: {email}")
            print(f"   🔑 Password: {password}")
        except Exception as e:
            print(f"   ❌ Failed to add to org: {str(e)}")

    print(f"\n✅ Created {len(user_map)}/{len(TEST_USERS)} users successfully")
    return user_map


def seed_catalog_items(org_id, admin_user_id, use_ai=True):
    """
    Seed catalog with hardware products and SaaS services.

    Args:
        org_id: Organization ID
        admin_user_id: Admin user ID for created_by
        use_ai: Whether to use Gemini AI enrichment (default: True)
    """
    all_products = HARDWARE_PRODUCTS + SAAS_SERVICES
    total = len(all_products)

    print(f"\n📦 Seeding {total} Catalog Items...")
    print(f"   ├─ {len(HARDWARE_PRODUCTS)} Hardware Products")
    print(f"   └─ {len(SAAS_SERVICES)} SaaS Services")

    if use_ai:
        print("\n🤖 AI Enrichment: ENABLED (using Gemini 3.0 Flash)")
    else:
        print("\n📝 AI Enrichment: DISABLED (manual data only)")

    success_count = 0
    fail_count = 0

    for i, product_name in enumerate(all_products, 1):
        try:
            print(f"\n[{i}/{total}] {product_name}")

            if use_ai:
                # Use Gemini to enrich product
                enriched = enrich_product(product_name=product_name)

                print(f"   ├─ Vendor: {enriched.get('vendor', 'N/A')}")
                print(f"   ├─ Category: {enriched.get('category', 'N/A')}")
                print(f"   ├─ Price: ${enriched.get('price', 0):.2f}" if enriched.get('price') else "   ├─ Price: N/A")
                print(f"   ├─ Type: {enriched.get('pricing_type', 'N/A')}")
                print(f"   └─ Confidence: {enriched.get('confidence', 'unknown')}")

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

            print(f"   ✅ Created catalog item (ID: {item['id']})")
            success_count += 1

        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            fail_count += 1

    print(f"\n✅ Catalog Seeding Complete: {success_count} succeeded, {fail_count} failed")


def seed_sample_requests(org_id, user_map):
    """
    Create sample requests from requester users.

    Args:
        org_id: Organization ID
        user_map: Dict mapping email -> user_id
    """
    supabase = get_supabase_admin()

    # Get requester user IDs
    requesters = [
        user_map.get(email)
        for email, role, _ in TEST_USERS
        if role == 'requester' and email in user_map
    ]

    if not requesters:
        print("\n⚠️  No requester users found, skipping sample requests")
        return

    print(f"\n📋 Creating Sample Requests...")

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
                print(f"   ✅ Created request: {req_data['search_query']}")
                created += 1
        except Exception as e:
            print(f"   ❌ Failed to create request: {str(e)}")

    print(f"\n✅ Created {created}/{len(sample_requests)} sample requests")


def main():
    """Main seeding function."""
    print("=" * 70)
    print("🌱 CatalogAI Automated Seeding Script")
    print("=" * 70)

    # Check for required environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("\n❌ ERROR: Missing required environment variables")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        print("   Make sure .env file is configured correctly")
        return

    # Check for Gemini API key (optional, for AI enrichment)
    gemini_key = os.getenv('GEMINI_API_KEY')
    use_ai = bool(gemini_key)

    if not use_ai:
        print("\n⚠️  GEMINI_API_KEY not found - AI enrichment will be disabled")
        print("   Products will be created with minimal data")
        response = input("\n   Continue without AI enrichment? (y/n): ")
        if response.lower() != 'y':
            print("\n❌ Aborted. Set GEMINI_API_KEY in .env to enable AI enrichment.")
            return

    try:
        # 1. Create organization
        org = seed_organization()

        # 2. Create users and add to org
        user_map = seed_users(org['id'])

        if not user_map:
            print("\n❌ No users created. Cannot proceed with seeding.")
            return

        # Get first admin user for catalog item creation
        admin_user_id = next(
            (uid for email, uid in user_map.items()
             if any(e == email and r == 'admin' for e, r, _ in TEST_USERS)),
            None
        )

        if not admin_user_id:
            print("\n❌ No admin user found. Cannot create catalog items.")
            return

        # 3. Seed catalog items
        seed_catalog_items(org['id'], admin_user_id, use_ai=use_ai)

        # 4. Create sample requests
        seed_sample_requests(org['id'], user_map)

        # Summary
        print("\n" + "=" * 70)
        print("✅ SEEDING COMPLETE!")
        print("=" * 70)
        print(f"\n📋 Organization: {ORG_NAME}")
        print(f"   ID: {org['id']}")
        print(f"\n👥 Users Created: {len(user_map)}")
        print(f"   - {sum(1 for _, r, _ in TEST_USERS if r == 'admin')} Admins")
        print(f"   - {sum(1 for _, r, _ in TEST_USERS if r == 'reviewer')} Reviewers")
        print(f"   - {sum(1 for _, r, _ in TEST_USERS if r == 'requester')} Requesters")
        print(f"\n📦 Catalog Items: {len(HARDWARE_PRODUCTS) + len(SAAS_SERVICES)}")
        print(f"   - {len(HARDWARE_PRODUCTS)} Hardware Products")
        print(f"   - {len(SAAS_SERVICES)} SaaS Services")
        print(f"\n🔐 User Credentials:")
        print("   (See output above for email/password combinations)")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ SEEDING FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
