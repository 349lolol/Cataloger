#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def check_env_file():
    print("Checking .env file...")
    env_path = Path('.env')

    if not env_path.exists():
        print("  FAIL: .env file not found")
        print("  Run: cp .env.example .env")
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
        print(f"  WARN: Missing or unconfigured: {', '.join(missing)}")
        return False

    print("  OK: .env configured")
    return True


def check_dependencies():
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
        print(f"  FAIL: Missing packages: {', '.join(missing)}")
        print("  Run: pip install -r requirements.txt")
        return False

    print("  OK: All dependencies installed")
    return True


def check_supabase_connection():
    print("\nChecking Supabase connection...")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        from supabase import create_client

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        if not url or not key:
            print("  FAIL: SUPABASE_URL or SUPABASE_KEY not set")
            return False

        client = create_client(url, key)
        client.table('orgs').select('id').limit(1).execute()

        print("  OK: Connected to Supabase")
        return True
    except Exception as e:
        print(f"  FAIL: Supabase connection failed: {e}")
        return False


def check_embedding_model():
    print("\nChecking embedding model...")

    try:
        from sentence_transformers import SentenceTransformer
        print("  Loading model...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("  OK: Embedding model loaded")
        return True
    except Exception as e:
        print(f"  FAIL: Failed to load embedding model: {e}")
        return False


def check_docker():
    print("\nChecking Docker...")

    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("  OK: Docker is running")

        try:
            client.images.get('catalogai-sandbox:latest')
            print("  OK: Sandbox Docker image found")
        except docker.errors.ImageNotFound:
            print("  WARN: Sandbox image not built")
            print("  Run: docker build -f catalogai_mcp/sandbox.Dockerfile -t catalogai-sandbox:latest .")

        return True
    except Exception as e:
        print(f"  WARN: Docker not available: {e}")
        return True


def main():
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

    if all(checks[:4]):
        print("All critical checks passed!")
        print("\nRun: python run.py")
        print("API: http://localhost:5000")
        return 0
    else:
        print("Some checks failed. Fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
