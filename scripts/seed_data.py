"""Seed script for CatalogAI test data."""
import os
import sys
import secrets
import string
import argparse
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from app.extensions import get_supabase_admin
from app.services.catalog_service import create_item
from app.services.product_enrichment_service import enrich_product

ORG_NAME = "Acme Corporation"

TEST_USERS = [
    ("admin1@acmecorp.test", "admin", "Alice Admin"),
    ("admin2@acmecorp.test", "admin", "Bob Administrator"),
    ("admin3@acmecorp.test", "admin", "Carol Chief"),
    ("reviewer1@acmecorp.test", "reviewer", "Diana Reviewer"),
    ("reviewer2@acmecorp.test", "reviewer", "Eve Evaluator"),
    ("reviewer3@acmecorp.test", "reviewer", "Frank Finance"),
    ("requester1@acmecorp.test", "requester", "Grace General"),
    ("requester2@acmecorp.test", "requester", "Henry HR"),
    ("requester3@acmecorp.test", "requester", "Iris IT"),
    ("requester4@acmecorp.test", "requester", "Jack Junior"),
]

LAPTOPS = [
    "MacBook Pro 16 inch M3 Max 48GB RAM 1TB",
    "MacBook Pro 14 inch M3 Pro 18GB RAM 512GB",
    "MacBook Air 15 inch M3 16GB RAM 512GB",
    "Lenovo ThinkPad X1 Carbon Gen 11 i7 32GB 1TB",
    "Lenovo ThinkPad X1 Yoga Gen 8 i7 16GB 512GB",
    "Lenovo ThinkPad T14s Gen 4 AMD Ryzen 7 32GB 1TB",
    "Lenovo ThinkPad P16s Gen 2 i7 32GB 1TB RTX A500",
    "Dell XPS 15 9530 i7 32GB 1TB RTX 4060",
    "Dell Latitude 7440 i7 32GB 1TB",
    "Dell Precision 5680 i9 64GB 2TB RTX 4000 Ada",
    "HP EliteBook 840 G10 i7 32GB 1TB",
    "HP ZBook Studio G10 i9 64GB 2TB RTX 4080",
    "HP Dragonfly G4 i7 32GB 1TB",
    "ASUS ROG Zephyrus G14 2024 RTX 4070 AMD Ryzen 9 32GB 1TB",
    "Razer Blade 15 RTX 4070 i7 32GB 1TB",
    "MSI Creator Z17 HX Studio RTX 4080 i9 64GB 2TB",
]

DESKTOPS = [
    "Apple Mac Studio M2 Ultra 192GB 8TB",
    "Apple Mac Mini M2 Pro 32GB 1TB",
    "Apple iMac 24 inch M3 16GB 512GB",
    "Dell Precision 5860 Tower Xeon 64GB 2TB RTX 4000",
    "HP Z4 G5 Workstation Xeon 64GB 2TB RTX 4000 Ada",
    "Lenovo ThinkStation P5 Xeon 64GB 2TB RTX 4000",
]

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

WEBCAMS = [
    "Logitech Brio 4K Pro Webcam",
    "Elgato Facecam Pro 4K60",
    "Dell UltraSharp Webcam WB7022",
    "Poly Studio P15 Personal Video Bar",
    "Jabra PanaCast 20 AI 4K Webcam",
]

DOCKS = [
    "CalDigit TS4 Thunderbolt 4 Dock 18-Port",
    "OWC Thunderbolt 4 Dock",
    "Belkin Thunderbolt 4 Dock Pro",
    "Dell Thunderbolt Dock WD22TB4",
    "Lenovo ThinkPad Thunderbolt 4 Dock",
]

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

DESKS = [
    "UPLIFT V2 Standing Desk 60x30 Bamboo",
    "Fully Jarvis Standing Desk 60x30 Bamboo",
    "Autonomous SmartDesk Pro 53x29",
    "Vari Electric Standing Desk 60x30",
    "Herman Miller Nevi Standing Desk",
    "Secretlab MAGNUS Pro",
]

STORAGE = [
    "Samsung T7 Shield Portable SSD 2TB",
    "SanDisk Extreme Pro Portable SSD 4TB",
    "LaCie Rugged SSD Pro 4TB Thunderbolt",
    "Synology DiskStation DS923+ NAS 4-Bay",
    "Samsung 990 Pro 4TB NVMe",
    "WD Black SN850X 4TB NVMe",
]

PRINTERS = [
    "HP Color LaserJet Pro MFP M479fdw",
    "Brother MFC-L8900CDW Color Laser",
    "Epson EcoTank Pro ET-5880",
    "Fujitsu ScanSnap iX1600 Scanner",
]

SAAS_SERVICES = [
    "Jira Software Premium (per user/year)",
    "Asana Business (per user/year)",
    "Linear Standard (per user/year)",
    "Confluence Premium (per user/year)",
    "Notion Team Plan (per user/year)",
    "Slack Business Plus (per user/year)",
    "Zoom Workplace Business (per user/year)",
    "Google Workspace Business Plus (per user/year)",
    "Microsoft 365 Business Premium (per user/year)",
    "Figma Professional (per editor/year)",
    "Adobe Creative Cloud All Apps (per license/year)",
    "Canva for Teams (per user/year)",
    "Final Cut Pro",
    "GitHub Enterprise Cloud (per user/year)",
    "GitLab Ultimate (per user/year)",
    "Vercel Pro (per member/year)",
    "AWS Reserved Instances (annual)",
    "Datadog Pro (per host/year)",
    "PagerDuty Business (per user/year)",
    "Sentry Team (per user/year)",
    "Snyk Team (per user/year)",
    "Salesforce Sales Cloud Enterprise (per user/year)",
    "HubSpot Sales Hub Professional (per user/year)",
    "Zendesk Suite Professional (per user/year)",
    "Intercom (per seat/year)",
    "Workday HCM (per employee/year)",
    "BambooHR Pro (per employee/year)",
    "Rippling Unity (per employee/month)",
    "Greenhouse Recruiting Pro",
    "QuickBooks Online Advanced (annual)",
    "NetSuite ERP (per user/year)",
    "Expensify Control (per user/year)",
    "Ramp Corporate Card Platform",
    "1Password Business (per user/year)",
    "Okta Workforce Identity Cloud (per user/year)",
    "CrowdStrike Falcon Pro (per endpoint/year)",
    "Cloudflare Zero Trust Enterprise",
    "Vanta Trust Management Platform",
]

HARDWARE_PRODUCTS = (
    LAPTOPS + DESKTOPS + MONITORS + KEYBOARDS + MICE +
    HEADSETS + WEBCAMS + DOCKS + CHAIRS + DESKS + STORAGE + PRINTERS
)


def generate_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(alphabet) for _ in range(16))


def create_test_user(email, password, full_name):
    supabase = get_supabase_admin()
    try:
        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name}
        })
        return response.user.id if response.user else None
    except Exception as e:
        print(f"   Failed to create user {email}: {str(e)}")
        return None


def seed_organization():
    supabase = get_supabase_admin()
    print("\n[ORG] Creating Organization...")

    existing = supabase.table('orgs').select('*').eq('name', ORG_NAME).execute()
    if existing.data:
        print(f"   Organization '{ORG_NAME}' already exists (ID: {existing.data[0]['id']})")
        return existing.data[0]

    org_response = supabase.table('orgs').insert({'name': ORG_NAME}).execute()
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
        password = generate_password()
        print(f"\n   Creating: {full_name} ({email}) - {role.upper()}")

        user_id = create_test_user(email, password, full_name)
        if not user_id:
            continue

        user_map[email] = user_id
        print(f"   User created (ID: {user_id})")

        try:
            supabase.table('org_memberships').insert({
                'org_id': org_id,
                'user_id': user_id,
                'role': role
            }).execute()
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        except Exception as e:
            print(f"   Failed to add to org: {str(e)}")

    print(f"\n   Created {len(user_map)}/{len(TEST_USERS)} users")
    return user_map


def seed_catalog_items(org_id, admin_user_id, use_ai=True):
    all_products = HARDWARE_PRODUCTS + SAAS_SERVICES
    total = len(all_products)

    print(f"\n[CATALOG] Seeding {total} Catalog Items...")
    print(f"   AI Enrichment: {'ENABLED' if use_ai else 'DISABLED'}")

    success_count = 0
    for i, product_name in enumerate(all_products, 1):
        try:
            print(f"\n[{i}/{total}] {product_name}")

            if use_ai:
                enriched = enrich_product(product_name=product_name)
                print(f"   Vendor: {enriched.get('vendor', 'N/A')}")
                if enriched.get('price'):
                    print(f"   Price: ${enriched.get('price'):.2f}")

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

    print(f"\n   Complete: {success_count}/{total} items created")


def seed_sample_requests(org_id, user_map):
    supabase = get_supabase_admin()

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
        {'org_id': org_id, 'created_by': requesters[0],
         'search_query': 'laptop for video editing',
         'justification': 'Need a powerful laptop for our video production team',
         'status': 'pending'},
        {'org_id': org_id, 'created_by': requesters[1],
         'search_query': 'project management software',
         'justification': 'Current PM tools are insufficient for growing team',
         'status': 'pending'},
        {'org_id': org_id, 'created_by': requesters[min(2, len(requesters)-1)],
         'search_query': 'ergonomic office chair',
         'justification': 'Employee wellness initiative for remote workers',
         'status': 'pending'},
    ]

    created = 0
    for req_data in sample_requests:
        try:
            response = supabase.table('requests').insert(req_data).execute()
            if response.data:
                print(f"   Created: {req_data['search_query']}")
                created += 1
        except Exception as e:
            print(f"   Failed: {str(e)}")

    print(f"\n   Created {created}/{len(sample_requests)} requests")


def clear_seeded_items(org_id):
    supabase = get_supabase_admin()
    print("\n[CLEAR] Removing previously seeded items...")

    try:
        response = supabase.table('catalog_items') \
            .delete() \
            .eq('org_id', org_id) \
            .eq('metadata->>seeded_at', 'automated_seed_script') \
            .execute()
        deleted_count = len(response.data) if response.data else 0
        print(f"   Deleted {deleted_count} items")
        return deleted_count
    except Exception as e:
        print(f"   Failed: {str(e)}")
        return 0


def seed_items_only():
    print("=" * 60)
    print("CatalogAI - Regenerate Catalog Items")
    print("=" * 60)

    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        print("\nERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    supabase = get_supabase_admin()
    use_ai = bool(os.getenv('GEMINI_API_KEY'))

    if not use_ai:
        print("\nWARNING: GEMINI_API_KEY not found")
        if input("   Continue without AI? (y/n): ").lower() != 'y':
            return

    try:
        org_response = supabase.table('orgs').select('*').eq('name', ORG_NAME).execute()
        if not org_response.data:
            print(f"\nERROR: Organization '{ORG_NAME}' not found. Run full seed first.")
            return

        org = org_response.data[0]
        print(f"\nUsing organization: {ORG_NAME} (ID: {org['id']})")

        memberships = supabase.table('org_memberships') \
            .select('user_id').eq('org_id', org['id']).eq('role', 'admin').limit(1).execute()

        if not memberships.data:
            print("\nERROR: No admin user found. Run full seed first.")
            return

        clear_seeded_items(org['id'])
        seed_catalog_items(org['id'], memberships.data[0]['user_id'], use_ai=use_ai)

        print("\n" + "=" * 60)
        print("COMPLETE!")
        print("=" * 60)

    except Exception as e:
        print(f"\nFAILED: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    print("=" * 60)
    print("CatalogAI Seed Script")
    print("=" * 60)

    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        print("\nERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    use_ai = bool(os.getenv('GEMINI_API_KEY'))
    if not use_ai:
        print("\nWARNING: GEMINI_API_KEY not found - AI enrichment disabled")
        if input("   Continue? (y/n): ").lower() != 'y':
            return

    try:
        org = seed_organization()
        user_map = seed_users(org['id'])

        if not user_map:
            print("\nNo users created. Aborting.")
            return

        admin_user_id = next(
            (uid for email, uid in user_map.items()
             if any(e == email and r == 'admin' for e, r, _ in TEST_USERS)),
            None
        )

        if not admin_user_id:
            print("\nNo admin user found. Aborting.")
            return

        seed_catalog_items(org['id'], admin_user_id, use_ai=use_ai)
        seed_sample_requests(org['id'], user_map)

        print("\n" + "=" * 60)
        print("SEEDING COMPLETE!")
        print("=" * 60)
        print(f"\nOrganization: {ORG_NAME} (ID: {org['id']})")
        print(f"Users: {len(user_map)}")
        print(f"Items: {len(HARDWARE_PRODUCTS) + len(SAAS_SERVICES)}")
        print("\nCredentials printed above.")
        print("=" * 60)

    except Exception as e:
        print(f"\nFAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed CatalogAI database')
    parser.add_argument('--items-only', action='store_true',
                        help='Only regenerate catalog items')
    args = parser.parse_args()

    if args.items_only:
        seed_items_only()
    else:
        main()
