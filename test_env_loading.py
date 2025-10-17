"""Test script to check if .env file is loaded correctly"""
import os
from pathlib import Path

print("=" * 60)
print("Testing .env file loading")
print("=" * 60)

# Find .env file
current_dir = Path(__file__).parent
env_file = current_dir / ".env"

print(f"\nCurrent directory: {current_dir}")
print(f".env file path: {env_file}")
print(f".env file exists: {env_file.exists()}")

if env_file.exists():
    print(f"\n.env file size: {env_file.stat().st_size} bytes")
    print("\n--- .env file content (first 500 chars) ---")
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read(500)
        print(content)

print("\n" + "=" * 60)
print("BEFORE loading .env:")
print("=" * 60)
api_key_before = os.getenv("ANTHROPIC_API_KEY")
print(f"ANTHROPIC_API_KEY: {api_key_before}")

# Load .env
try:
    from dotenv import load_dotenv
    print("\n[OK] python-dotenv is available")

    result = load_dotenv(env_file)
    print(f"load_dotenv() returned: {result}")
except ImportError:
    print("\n[ERROR] python-dotenv not available")
except Exception as e:
    print(f"\n[ERROR] Failed to load .env: {e}")

print("\n" + "=" * 60)
print("AFTER loading .env:")
print("=" * 60)
api_key_after = os.getenv("ANTHROPIC_API_KEY")
print(f"ANTHROPIC_API_KEY: {api_key_after}")

if api_key_after:
    print(f"API Key length: {len(api_key_after)}")
    print(f"API Key starts with: {api_key_after[:20]}...")
else:
    print("[ERROR] API Key is still None!")

print("\n" + "=" * 60)
print("All environment variables containing 'ANTHROPIC':")
print("=" * 60)
for key, value in os.environ.items():
    if 'ANTHROPIC' in key.upper():
        print(f"{key}: {value[:30] if value else 'None'}...")
