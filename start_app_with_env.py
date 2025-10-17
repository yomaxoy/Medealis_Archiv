"""
Helper script to load .env file and start Streamlit app
This ensures environment variables are set before any imports
"""
import os
import sys
from pathlib import Path

# Load .env file FIRST
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"[OK] Loaded .env file")

        # Verify API key is set
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            print(f"[OK] ANTHROPIC_API_KEY is set ({len(api_key)} chars)")
        else:
            print("[WARNING] ANTHROPIC_API_KEY not found in .env!")
    else:
        print(f"[WARNING] .env file not found at: {env_file}")
except Exception as e:
    print(f"[ERROR] Failed to load .env: {e}")
    sys.exit(1)

# Now start Streamlit
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python start_app_with_env.py <app_file> [streamlit_args...]")
        sys.exit(1)

    app_file = sys.argv[1]
    streamlit_args = sys.argv[2:] if len(sys.argv) > 2 else []

    # Import streamlit and run
    from streamlit.web import cli as stcli

    # Build command line args for streamlit
    sys.argv = ["streamlit", "run", app_file] + streamlit_args

    print(f"[OK] Starting Streamlit: {' '.join(sys.argv)}")
    sys.exit(stcli.main())
