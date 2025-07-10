import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Bygg absolut sökväg till .env-filen i projektroten
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
print("DEBUG ENV_PATH:", env_path)
load_dotenv(env_path)

# Hämta Supabase-URL och API-nyckel från miljövariabler
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv(
    "SUPABASE_ANON_KEY"
)  # Använd SUPABASE_ANON_KEY istället för SUPABASE_KEY

# DEBUG: Skriv ut vad som laddas
print("DEBUG SUPABASE_URL:", supabase_url)
print("DEBUG SUPABASE_ANON_KEY:", supabase_key)

# Kontrollera att miljövariablerna finns
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL och SUPABASE_ANON_KEY måste vara satta i .env-filen")

# Skapa Supabase-klienten
supabase: Client = create_client(supabase_url, supabase_key)
