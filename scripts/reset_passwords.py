import os
import sys
import secrets
import string
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app.extensions import get_supabase_admin

# Test users from seed_data.py
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


def generate_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(alphabet) for _ in range(16))


def reset_user_password(email, new_password):
    supabase = get_supabase_admin()

    try:
        users = supabase.auth.admin.list_users()
        user = next((u for u in users if u.email == email), None)

        if not user:
            print(f"   User not found: {email}")
            return False

        supabase.auth.admin.update_user_by_id(user.id, {"password": new_password})
        return True

    except Exception as e:
        print(f"   Failed to reset password for {email}: {str(e)}")
        return False


def main():
    print("=" * 70)
    print("CatalogAI Password Reset")
    print("=" * 70)

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("\nERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    print(f"\nResetting passwords for {len(TEST_USERS)} users...")

    success_count = 0
    credentials = []

    for email, role, full_name in TEST_USERS:
        new_password = generate_password()

        print(f"\nResetting: {full_name} ({email}) - {role.upper()}")

        if reset_user_password(email, new_password):
            print("   OK")
            success_count += 1
            credentials.append({
                'email': email,
                'password': new_password,
                'role': role,
                'name': full_name
            })
        else:
            print("   Skipped (user may not exist)")

    print("\n" + "=" * 70)
    print("PASSWORD RESET COMPLETE")
    print("=" * 70)
    print(f"\nReset {success_count}/{len(TEST_USERS)} passwords")

    if credentials:
        print("\nNEW CREDENTIALS:")
        print("=" * 70)

        for role_name in ['admin', 'reviewer', 'requester']:
            role_users = [c for c in credentials if c['role'] == role_name]
            if role_users:
                print(f"\n{role_name.upper()}S:")
                print("-" * 70)
                for cred in role_users:
                    print(f"\n  Name:     {cred['name']}")
                    print(f"  Email:    {cred['email']}")
                    print(f"  Password: {cred['password']}")

        print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
