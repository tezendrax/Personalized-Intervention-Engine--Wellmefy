import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personalized Intervention Engine (PIE)"
    DATABASE_URL: str = "sqlite:///pie.db"
    SDT_DATABASE_URL: str = "sqlite:///../Digital Twin/sdt.db"
    PORT: int = 8004
    HOST: str = "0.0.0.0"
    ALPHA_EXPLORE: float = 1.0  # LinUCB exploration parameter
    GITHUB_TOKEN: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()

def get_absolute_db_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        relative_path = url.replace("sqlite:///", "")
        if not os.path.isabs(relative_path):
            # Resolve relative to the parent of the 'pie' package (workspace root)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            abs_path = os.path.normpath(os.path.join(base_dir, relative_path))
            return f"sqlite:///{abs_path}"
    return url

settings.DATABASE_URL = get_absolute_db_url(settings.DATABASE_URL)
settings.SDT_DATABASE_URL = get_absolute_db_url(settings.SDT_DATABASE_URL)
