"""Test if API key is available after imports like in the real app"""
import sys
import os
from pathlib import Path

# Same structure as in main_user_app.py
current_dir = Path(__file__).parent
src_dir = current_dir
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

# Load .env file
if "ENV_LOADED" not in os.environ:
    try:
        from dotenv import load_dotenv
        env_file = src_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            os.environ["ENV_LOADED"] = "true"
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                print(f"[OK] .env loaded - API Key found ({len(api_key)} chars)")
            else:
                print("[ERROR] .env loaded but ANTHROPIC_API_KEY not found!")
    except Exception as e:
        print(f"[ERROR] {e}")

# Now test if claude_api_client can see it
print("\n" + "="*60)
print("Testing claude_api_client import...")
print("="*60)

try:
    from src.warehouse.application.services.document_processing.claude_api_client import ClaudeAPIClient

    client = ClaudeAPIClient()
    print(f"Claude client initialized: {client.client is not None}")
    print(f"Claude available: {client.is_available()}")

    # Check what the client sees
    api_key_in_client = os.getenv("ANTHROPIC_API_KEY")
    if api_key_in_client:
        print(f"[OK] API Key visible in client context: {api_key_in_client[:20]}... ({len(api_key_in_client)} chars)")
    else:
        print("[ERROR] API Key NOT visible in client context!")

except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
