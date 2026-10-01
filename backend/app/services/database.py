from supabase import create_client, Client
from app.core.config import settings
from app.core.logging import get_logger
import threading


logger = get_logger(__name__)

_supabase_client: Client = None
_client_lock = threading.Lock()


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        with _client_lock:
            if _supabase_client is None:
                if not settings.SUPABASE_URL or settings.SUPABASE_URL == "https://your-project.supabase.co":
                    raise ValueError("SUPABASE_URL not configured")
                if not settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_SERVICE_KEY == "your-supabase-service-key-here":
                    raise ValueError("SUPABASE_SERVICE_KEY not configured")
                
                logger.info("Initializing Supabase client")
                _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    return _supabase_client


def reset_supabase_client() -> None:
    global _supabase_client
    with _client_lock:
        _supabase_client = None