#!/usr/bin/env python3
"""
Quick test script to verify MCP server setup.

This script checks:
1. All required dependencies are installed
2. Environment variables are set
3. Can authenticate with Supabase
4. Can make API calls

Run before configuring Claude Desktop to catch issues early.
"""
import os
import sys

def check_imports():
    """Check that all required packages are installed."""
    print("Checking dependencies...")
    try:
        import httpx
        print("  ✓ httpx installed")
    except ImportError:
        print("  ✗ httpx not installed - run: pip install httpx")
        return False

    try:
        from mcp.server.fastmcp import FastMCP
        print("  ✓ mcp installed")
    except ImportError:
        print("  ✗ mcp not installed - run: pip install -e .")
        return False

    return True


def check_env_vars():
    """Check that required environment variables are set."""
    print("\nChecking environment variables...")
    required = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'USER_EMAIL',
        'USER_PASSWORD',
    ]

    optional = {
        'API_URL': 'http://localhost:5000',
    }

    missing = []
    for var in required:
        if os.getenv(var):
            print(f"  ✓ {var} is set")
        else:
            print(f"  ✗ {var} is NOT set")
            missing.append(var)

    for var, default in optional.items():
        value = os.getenv(var, default)
        print(f"  ℹ {var} = {value}")

    return len(missing) == 0


def test_authentication():
    """Test authentication with Supabase."""
    print("\nTesting Supabase authentication...")

    import httpx

    supabase_url = os.getenv('SUPABASE_URL')
    user_email = os.getenv('USER_EMAIL')
    user_password = os.getenv('USER_PASSWORD')
    supabase_key = os.getenv('SUPABASE_KEY')

    auth_url = f"{supabase_url}/auth/v1/token?grant_type=password"

    try:
        response = httpx.post(
            auth_url,
            json={"email": user_email, "password": user_password},
            headers={"apikey": supabase_key},
            timeout=10.0
        )
        response.raise_for_status()

        data = response.json()
        access_token = data.get('access_token')
        user = data.get('user', {})

        if access_token:
            print(f"  ✓ Authentication successful")
            print(f"  ✓ User ID: {user.get('id')}")
            print(f"  ✓ Email: {user.get('email')}")
            return True
        else:
            print("  ✗ No access token in response")
            return False

    except httpx.HTTPStatusError as e:
        print(f"  ✗ HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def test_api_connection():
    """Test connection to CatalogAI API."""
    print("\nTesting API connection...")

    import httpx

    api_url = os.getenv('API_URL', 'http://localhost:5000')

    try:
        response = httpx.get(f"{api_url}/api/health", timeout=5.0)
        response.raise_for_status()

        print(f"  ✓ API is reachable at {api_url}")
        print(f"  ✓ Health check: {response.json()}")
        return True

    except httpx.ConnectError:
        print(f"  ✗ Cannot connect to API at {api_url}")
        print(f"    Make sure the Flask API is running: python run.py")
        return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("CatalogAI MCP Server Setup Verification")
    print("=" * 60)

    checks = [
        ("Dependencies", check_imports),
        ("Environment", check_env_vars),
        ("Authentication", test_authentication),
        ("API Connection", test_api_connection),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check failed with error: {str(e)}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✅ All checks passed! MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Configure Claude Desktop with catalogai_mcp/claude_desktop_config.json")
        print("2. Restart Claude Desktop")
        print("3. Test with: 'Search the catalog for laptops'")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
