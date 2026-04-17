import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("OLLAMA_BASE_URL")

if not BASE_URL:
    raise ValueError("OLLAMA_BASE_URL not found in .env")

try:
    # Normalize URL for native API calls (strip trailing slash and /v1)
    api_url = BASE_URL.rstrip("/")
    if api_url.endswith("/v1"):
        api_url = api_url[:-3].rstrip("/")
    
    # Check models endpoint
    response = requests.get(f"{api_url}/api/tags", timeout=5)

    if response.status_code == 200:
        print("✅ Ollama connection successful!\n")
        print("Available Models:")

        data = response.json()
        for model in data.get("models", []):
            print("-", model["name"])

    else:
        print(f"⚠️ Connected but got status code: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Connection failed!")
    print("Check if Ollama is running or URL is correct.")

except requests.exceptions.Timeout:
    print("❌ Request timed out!")
    print("Check network or server load.")

except Exception as e:
    print("❌ Error:", str(e))