from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DIRECT_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    JWT_SECRET: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()