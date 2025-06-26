import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL och SUPABASE_SERVICE_KEY måste vara satta i miljön.")

supabase: Client = create_client(url, key)
