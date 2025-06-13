from backend.supabase_client import supabase


def test_supabase_connection():
    # Försök hämta data från tabellen 'orders' (byt till en existerande tabell)
    response = supabase.table('orders').select('*').limit(1).execute()
    # Kontrollera att anropet lyckades (data eller error är None)
    assert response.data is not None or response.error is None 