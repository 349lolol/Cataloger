#!/usr/bin/env python3
"""
Setup verification script for CatalogAI.
Checks that all dependencies and configuration are correct.
"""
import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists and has required variables."""
    print("Checking .env file...")
    env_path = Path('.env')

    if not env_path.exists():
        print("  ❌ .env file not found!")
        print("  → Run: cp .env.example .env")
        print("  → Then edit .env with your Supabase credentials")
        return False

    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'FLASK_SECRET_KEY'
    ]

    with open(env_path) as f:
        env_content = f.read()

    missing = []
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=your-" in env_content:
            missing.append(var)

    if missing:
        print(f"  ⚠️  Missing or unconfigured variables: {', '.join(missing)}")
        print("  → Edit .env and add your actual Supabase credentials")
        return False

    print("  ✅ .env file configured")
    return True


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\nChecking Python dependencies...")

    required_packages = [
        'flask',
        'supabase',
        'sentence_transformers',
        'pydantic',
        'httpx'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"  ❌ Missing packages: {', '.join(missing)}")
        print("  → Run: pip install -r requirements.txt")
        return False

    print("  ✅ All dependencies installed")
    return True


def check_supabase_connection():
    """Check if we can connect to Supabase."""
    print("\nChecking Supabase connection...")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        from supabase import create_client

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        if not url or not key:
            print("  ❌ SUPABASE_URL or SUPABASE_KEY not set")
            return False

        client = create_client(url, key)
        # Try a simple query to test connection
        client.table('orgs').select('id').limit(1).execute()

        print("  ✅ Connected to Supabase")
        return True
    except Exception as e:
        print(f"  ❌ Supabase connection failed: {e}")
        print("  → Check your SUPABASE_URL and SUPABASE_KEY in .env")
        print("  → Make sure you've run the database migrations")
        return False


def check_embedding_model():
    """Check if embedding model can be loaded."""
    print("\nChecking embedding model...")

    try:
        from sentence_transformers import SentenceTransformer
        print("  ⏳ Loading model (this may take a minute on first run)...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("  ✅ Embedding model loaded successfully")
        return True
    except Exception as e:
        print(f"  ❌ Failed to load embedding model: {e}")
        return False


def check_docker():
    """Check if Docker is available (for MCP sandbox)."""
    print("\nChecking Docker (for MCP integration)...")

    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("  ✅ Docker is running")

        # Check if sandbox image exists
        try:
            client.images.get('catalogai-sandbox:latest')
            print("  ✅ Sandbox Docker image found")
        except docker.errors.ImageNotFound:
            print("  ⚠️  Sandbox image not built yet")
            print("  → Run: docker build -f catalogai_mcp/sandbox.Dockerfile -t catalogai-sandbox:latest .")

        return True
    except Exception as e:
        print(f"  ⚠️  Docker not available: {e}")
        print("  → Docker is only needed for MCP code execution (Part C)")
        print("  → You can skip this for basic API usage")
        return True  # Not critical


def main():
    """Run all checks."""
    print("=" * 60)
    print("CatalogAI Setup Verification")
    print("=" * 60)

    checks = [
        check_env_file(),
        check_dependencies(),
        check_supabase_connection(),
        check_embedding_model(),
        check_docker()
    ]

    print("\n" + "=" * 60)

    if all(checks[:4]):  # First 4 are critical
        print("✅ All critical checks passed!")
        print("\nYou can now run: python run.py")
        print("API will be available at http://localhost:5000")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
