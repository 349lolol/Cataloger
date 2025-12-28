"""
Seed script to populate database with test data.
Creates a test organization and sample catalog items.
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app.extensions import get_supabase_admin
from app.services.catalog_service import create_item


def seed_organization():
    """Create a test organization."""
    supabase = get_supabase_admin()

    # Create test org
    org_response = supabase.table('orgs').insert({
        'name': 'Acme Corp (Test Organization)'
    }).execute()

    if not org_response.data:
        print("Failed to create organization")
        return None

    org = org_response.data[0]
    print(f"✅ Created organization: {org['name']} (ID: {org['id']})")
    return org


def seed_catalog_items(org_id: str, user_id: str):
    """Create sample catalog items with realistic product data."""
    sample_items = [
        {
            'name': 'Dell Latitude 7430 Laptop',
            'description': '14" laptop with Intel Core i7, 16GB RAM, 512GB SSD. Perfect for business use.',
            'category': 'Electronics',
            'price': 1299.99,
            'pricing_type': 'one_time',
            'vendor': 'Dell',
            'sku': 'LAT-7430-i7-16-512',
            'product_url': 'https://www.dell.com/latitude-7430',
            'metadata': {'warranty': '3 years', 'weight': '3.2 lbs'}
        },
        {
            'name': 'Logitech MX Master 3 Mouse',
            'description': 'Wireless ergonomic mouse with precision scrolling and customizable buttons.',
            'category': 'Electronics',
            'price': 99.99,
            'pricing_type': 'one_time',
            'vendor': 'Logitech',
            'sku': 'MX-MASTER-3',
            'product_url': 'https://www.logitech.com/mx-master-3',
            'metadata': {'wireless': True, 'battery_life': '70 days'}
        },
        {
            'name': 'Herman Miller Aeron Chair',
            'description': 'Ergonomic office chair with adjustable lumbar support and breathable mesh.',
            'category': 'Furniture',
            'price': 1395.00,
            'pricing_type': 'one_time',
            'vendor': 'Herman Miller',
            'sku': 'AERON-SIZE-B',
            'product_url': 'https://www.hermanmiller.com/aeron',
            'metadata': {'warranty': '12 years', 'size': 'B (Medium)'}
        },
        {
            'name': 'Printer Paper (Ream)',
            'description': 'Standard 8.5x11 white paper, 500 sheets per ream.',
            'category': 'Office Supplies',
            'price': 7.99,
            'pricing_type': 'one_time',
            'vendor': 'Staples',
            'sku': 'PAPER-8.5X11-500',
            'metadata': {'quantity': 500, 'brightness': '92'}
        },
        {
            'name': 'AWS EC2 t3.medium Instance',
            'description': 'Cloud compute instance with 2 vCPUs, 4GB RAM. Pay-as-you-go pricing.',
            'category': 'Services',
            'price': 0.0416,
            'pricing_type': 'usage_based',
            'vendor': 'Amazon Web Services',
            'sku': 'EC2-T3-MEDIUM-US-EAST',
            'product_url': 'https://aws.amazon.com/ec2/instance-types/t3',
            'metadata': {'region': 'us-east-1', 'unit': 'per hour'}
        },
        {
            'name': 'Microsoft 365 Business Standard',
            'description': 'Office apps, cloud storage, email, and collaboration tools.',
            'category': 'Services',
            'price': 12.50,
            'pricing_type': 'monthly',
            'vendor': 'Microsoft',
            'sku': 'M365-BUS-STD',
            'product_url': 'https://www.microsoft.com/microsoft-365/business',
            'metadata': {'storage': '1TB per user', 'includes': 'Teams, Exchange, SharePoint'}
        }
    ]

    for item_data in sample_items:
        try:
            item = create_item(
                org_id=org_id,
                name=item_data['name'],
                description=item_data['description'],
                category=item_data['category'],
                created_by=user_id,
                price=item_data.get('price'),
                pricing_type=item_data.get('pricing_type'),
                vendor=item_data.get('vendor'),
                sku=item_data.get('sku'),
                product_url=item_data.get('product_url'),
                metadata=item_data.get('metadata')
            )
            print(f"✅ Created catalog item: {item['name']}")
        except Exception as e:
            print(f"❌ Failed to create {item_data['name']}: {e}")


def main():
    """Main seed function."""
    print("🌱 Seeding database with test data...")

    # Create organization
    org = seed_organization()
    if not org:
        print("❌ Failed to create organization. Exiting.")
        return

    # Note: In a real setup, you would create a test user via Supabase Auth
    # For now, we'll use a placeholder user_id
    # You should replace this with an actual user ID from Supabase Auth
    print("\n⚠️  MANUAL STEP REQUIRED:")
    print("1. Go to your Supabase dashboard")
    print("2. Create a test user in Authentication")
    print("3. Add them to org_memberships table:")
    print(f"   INSERT INTO org_memberships (org_id, user_id, role) VALUES ('{org['id']}', '<USER_ID>', 'admin');")
    print()

    # Ask if user wants to proceed with seeding catalog items
    response = input("Do you have a user_id ready? (y/n): ")
    if response.lower() == 'y':
        user_id = input("Enter user_id: ").strip()
        if user_id:
            seed_catalog_items(org['id'], user_id)
            print("\n✅ Database seeding complete!")
            print(f"📋 Organization ID: {org['id']}")
        else:
            print("❌ No user_id provided. Skipping catalog items.")
    else:
        print("\n✅ Organization created. Complete the manual steps above, then run this script again with catalog seeding.")
        print(f"📋 Organization ID: {org['id']}")


if __name__ == '__main__':
    main()
