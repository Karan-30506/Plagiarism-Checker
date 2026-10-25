from supabase import create_client, Client
from app.config import settings

# Programmatically sanitize SUPABASE_URL (strips /rest/v1 and trailing slashes)
clean_url = settings.SUPABASE_URL.replace("/rest/v1", "").rstrip("/")

# Client for standard authentication operations
supabase: Client = create_client(clean_url, settings.SUPABASE_KEY)

# Admin Client (bypasses RLS) for file storage management
supabase_admin: Client = create_client(clean_url, settings.SUPABASE_SERVICE_KEY)