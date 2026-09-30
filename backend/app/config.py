import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "DealRadar API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dealradar.db")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_service_account.json")
    TRACKING_INTERVAL_MINUTES: int = int(os.getenv("TRACKING_INTERVAL_MINUTES", "30"))
    
    # Affiliate tags (optional)
    AMAZON_AFFILIATE_TAG: str = os.getenv("AMAZON_AFFILIATE_TAG", "")
    MERCADOLIBRE_AFFILIATE_TAG: str = os.getenv("MERCADOLIBRE_AFFILIATE_TAG", "")

settings = Settings()
