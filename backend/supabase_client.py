import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

# För utveckling: Skapa optional Supabase client
supabase = None

if url and key and not key.startswith("dummy"):
    try:
        from supabase import Client, create_client

        supabase: Client = create_client(url, key)
        print("✅ Supabase client initialiserad")
    except Exception as e:
        print(f"⚠️ Supabase client misslyckades: {e}")
        print("📝 Kör utan Supabase i utvecklingsläge")
        supabase = None
else:
    print("📝 Supabase disabled - använder dummy-nycklar för utveckling")
