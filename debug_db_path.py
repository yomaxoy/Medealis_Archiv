"""Debug script to check database path resolution"""
import os
from pathlib import Path

print("=" * 80)
print("DATABASE PATH DEBUG")
print("=" * 80)

# 1. Check .env loading
print("\n1. CHECKING .ENV FILE:")
print("-" * 80)

env_file = Path(__file__).parent / ".env"
print(f"   .env path: {env_file}")
print(f"   .env exists: {env_file.exists()}")

if env_file.exists():
    print(f"   .env size: {env_file.stat().st_size} bytes")

# 2. Load .env
print("\n2. LOADING .ENV:")
print("-" * 80)
try:
    from dotenv import load_dotenv
    result = load_dotenv(env_file, override=True)
    print(f"   [OK] load_dotenv() returned: {result}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# 3. Check environment variable
print("\n3. ENVIRONMENT VARIABLE:")
print("-" * 80)
use_server = os.getenv("USE_SERVER_STORAGE")
print(f"   USE_SERVER_STORAGE = {use_server}")
print(f"   Type: {type(use_server)}")
print(f"   As bool: {str(use_server).lower() == 'true'}")

# 4. Check settings.py
print("\n4. SETTINGS.PY:")
print("-" * 80)
try:
    from config.settings import Settings
    print(f"   ✓ Settings imported")
    print(f"   Settings._get_use_server_storage() = {Settings._get_use_server_storage()}")
    print(f"   Settings.SERVER_BASE_PATH = {Settings.SERVER_BASE_PATH}")

    # Check if server path exists
    print(f"\n   Server base path exists: {Settings.SERVER_BASE_PATH.exists()}")

    if Settings.SERVER_BASE_PATH.exists():
        db_dir = Settings.SERVER_BASE_PATH / "database"
        print(f"   Database dir would be: {db_dir}")
        print(f"   Database dir exists: {db_dir.exists()}")

        # Try to create it
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ Database dir created/exists")

            # Test write access
            test_file = db_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            print(f"   ✓ Write access confirmed")
        except Exception as e:
            print(f"   ✗ Error creating/writing: {e}")

    # Get actual database path
    print(f"\n5. ACTUAL DATABASE PATH:")
    print("-" * 80)
    db_path = Settings._get_database_path()
    print(f"   Database directory: {db_path}")
    print(f"   Full DB path: {db_path / Settings.DATABASE_NAME}")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 6. Check connection.py behavior
print("\n6. CONNECTION.PY SIMULATION:")
print("-" * 80)
database_url = os.getenv("DATABASE_URL")
print(f"   DATABASE_URL env var: {database_url}")

if not database_url:
    print("   DATABASE_URL not set, will use fallback")
    try:
        from config.settings import Settings
        Settings.DATABASE_DIR = None
        Settings.DATABASE_PATH = None
        Settings.ensure_directories()
        database_path = Settings.get_database_path()
        database_url = f"sqlite:///{database_path}"
        print(f"   Fallback DB URL: {database_url}")
    except Exception as e:
        print(f"   Error in fallback: {e}")

print("\n" + "=" * 80)
