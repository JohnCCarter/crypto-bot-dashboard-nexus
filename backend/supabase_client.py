from supabase import create_client, Client
import os

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise ValueError(
        "SUPABASE_URL och SUPABASE_SERVICE_KEY måste vara satta i miljön."
    )

supabase: Client = create_client(url, key) 