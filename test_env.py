"""Test-Skript um zu prüfen, ob Umgebungsvariablen geladen werden."""
import os
import sys
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv

    env_file = Path(__file__).parent / ".env"
    print(f"Suche .env Datei: {env_file}")
    print(f"Existiert: {env_file.exists()}")

    if env_file.exists():
        load_dotenv(env_file, override=True)
        print("✓ .env Datei geladen")
    else:
        print("✗ .env Datei nicht gefunden!")
except ImportError:
    print("✗ python-dotenv nicht installiert")
except Exception as e:
    print(f"✗ Fehler beim Laden: {e}")

# Check Anthropic API Key
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    print(f"✓ ANTHROPIC_API_KEY gefunden: {anthropic_key[:20]}...")
else:
    print("✗ ANTHROPIC_API_KEY nicht gefunden")

# Check Tesseract
tesseract_path = os.getenv("TESSERACT_PATH")
if tesseract_path:
    print(f"✓ TESSERACT_PATH: {tesseract_path}")
    if Path(tesseract_path).exists():
        print("✓ Tesseract existiert")
    else:
        print("✗ Tesseract Datei nicht gefunden")
else:
    print("✗ TESSERACT_PATH nicht gesetzt")

# Check pytesseract
try:
    import pytesseract

    print(f"✓ pytesseract installiert")

    # Set tesseract path if available
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # Try to get version
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract Version: {version}")
    except Exception as e:
        print(f"✗ Kann Tesseract nicht ausführen: {e}")
except ImportError:
    print("✗ pytesseract nicht installiert")

# Check Anthropic
try:
    import anthropic

    print(f"✓ anthropic SDK installiert")

    # Try to create client
    if anthropic_key:
        try:
            client = anthropic.Anthropic(api_key=anthropic_key)
            print("✓ Anthropic Client erfolgreich erstellt")
        except Exception as e:
            print(f"✗ Fehler beim Erstellen des Clients: {e}")
    else:
        print("✗ Kann Client nicht erstellen - API Key fehlt")
except ImportError:
    print("✗ anthropic SDK nicht installiert")
