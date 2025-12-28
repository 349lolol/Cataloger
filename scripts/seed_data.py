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
from app.services.product_enrichment_service import enrich_product


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


def seed_catalog_items(org_id: str, user_id: str, use_ai: bool = True):
    """
    Create sample catalog items using AI enrichment pipeline.
    
    Args:
        org_id: Organization ID
        user_id: User ID for created_by
        use_ai: If True, use Gemini API to enrich products (default: True)
    """
    # Simple product names - AI will enrich with all details
    product_names = [
        'MacBook Pro 16 inch M3 Max',
        'Dell XPS 15 9530',
        'Logitech MX Master 3S',
        'Herman Miller Aeron Chair Size B',
        'HP OfficeJet Pro 9015e',
        'Staples Copy Paper 8.5x11',
        'Slack Business Plus',
        'GitHub Enterprise Cloud',
        'AWS EC2 t3.medium us-east-1',
        'Zoom Workspace Pro'
    ]

    print(f"\n{'🤖 AI-Powered' if use_ai else '📝 Manual'} Catalog Seeding")
    print(f"Creating {len(product_names)} catalog items...")

    for product_name in product_names:
        try:
            if use_ai:
                print(f"\n🔍 Enriching: {product_name}")
                
                # Use Gemini to get full product details
                enriched = enrich_product(product_name=product_name)
                
                print(f"   ├─ Vendor: {enriched.get('vendor', 'N/A')}")
                print(f"   ├─ Price: ${enriched.get('price', 0):.2f}")
                print(f"   └─ Confidence: {enriched.get('confidence', 'unknown')}")
                
                # Create catalog item with enriched data
                item = create_item(
                    org_id=org_id,
                    name=enriched.get('name', product_name),
                    description=enriched.get('description', ''),
                    category=enriched.get('category', ''),
                    created_by=user_id,
                    price=enriched.get('price'),
                    pricing_type=enriched.get('pricing_type'),
                    vendor=enriched.get('vendor'),
                    sku=enriched.get('sku'),
                    product_url=enriched.get('product_url'),
                    metadata={
                        **enriched.get('metadata', {}),
                        'ai_enriched': True,
                        'ai_confidence': enriched.get('confidence', 'unknown')
                    }
                )
                print(f"✅ Created: {item['name']}")
                
            else:
                # Fallback: create with minimal data
                item = create_item(
                    org_id=org_id,
                    name=product_name,
                    description='',
                    category='Uncategorized',
                    created_by=user_id,
                    metadata={'ai_enriched': False}
                )
                print(f"✅ Created: {item['name']} (minimal data)")
                
        except Exception as e:
            print(f"❌ Failed to create {product_name}: {e}")


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
            # Ask if user wants to use AI enrichment
            ai_response = input("Use AI enrichment (requires GEMINI_API_KEY)? (y/n, default=y): ").strip().lower()
            use_ai = ai_response != 'n'  # Default to True unless explicitly 'n'
            
            if use_ai:
                gemini_key = os.getenv('GEMINI_API_KEY')
                if not gemini_key:
                    print("⚠️  Warning: GEMINI_API_KEY not found in environment")
                    print("Falling back to manual seeding...")
                    use_ai = False
            
            seed_catalog_items(org['id'], user_id, use_ai=use_ai)
            print("\n✅ Database seeding complete!")
            print(f"📋 Organization ID: {org['id']}")
        else:
            print("❌ No user_id provided. Skipping catalog items.")
    else:
        print("\n✅ Organization created. Complete the manual steps above, then run this script again with catalog seeding.")
        print(f"📋 Organization ID: {org['id']}")


if __name__ == '__main__':
    main()
