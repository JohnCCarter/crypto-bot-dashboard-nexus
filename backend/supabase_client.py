import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Ladda miljövariabler från .env-filen
load_dotenv()

# Hämta Supabase-URL och API-nyckel från miljövariabler
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Skapa Supabase-klienten
supabase: Client = create_client(supabase_url, supabase_key)