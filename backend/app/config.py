from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    AWABABY_API_KEY: str
    AWABABY_API_URL: str
    MAX_FILE_SIZE_MB: int = 500
    STORAGE_PATH: str = "./storage"
    ML_MODEL_PATH: str = "./ml_models/cry_detector_v1.pth"
    ALLOWED_ORIGINS: str

    class Config:
        env_file = ".env"

settings = Settings()
