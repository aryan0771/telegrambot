import os
from dotenv import load_dotenv, set_key

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

class Settings:
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    SESSION = os.getenv("SESSION", "mirror_session")
    
    SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
    DESTINATION_CHANNEL = os.getenv("DESTINATION_CHANNEL")
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    WEB_PASSWORD = os.getenv("WEB_PASSWORD", "admin")  # Default password for web UI

    @classmethod
    def validate(cls):
        missing = []
        if not cls.API_ID:
            missing.append("API_ID")
        if not cls.API_HASH:
            missing.append("API_HASH")
        if not cls.SOURCE_CHANNEL:
            missing.append("SOURCE_CHANNEL")
        if not cls.DESTINATION_CHANNEL:
            missing.append("DESTINATION_CHANNEL")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        try:
            cls.SOURCE_CHANNEL = int(cls.SOURCE_CHANNEL)
        except (ValueError, TypeError):
            pass
            
        try:
            cls.DESTINATION_CHANNEL = int(cls.DESTINATION_CHANNEL)
        except (ValueError, TypeError):
            pass

    @classmethod
    def update_env(cls, key: str, value: str):
        set_key(env_path, key, str(value))
        setattr(cls, key, value)
        
settings = Settings()
