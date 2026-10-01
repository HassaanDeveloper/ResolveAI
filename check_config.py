import sys
sys.path.insert(0, r'E:\ResolveAI\backend')
from app.core.config import settings
print(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
print(f"API_PREFIX: {settings.API_PREFIX}")
print(f"PORT: {settings.PORT}")
