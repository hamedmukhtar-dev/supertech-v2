from pydantic import BaseSettings

class Settings(BaseSettings):
    # AI
    OPENAI_API_KEY: str
    AI_MODEL: str = "gpt-4o-mini"

    # Database
    BANK_DB: str = "data/bank_core.db"
    LEDGER_DB: str = "data/ledger.db"

    # Security
    SESSION_SECRET: str = "change-me"
    JWT_SECRET: str = "change-me"
    ALGORITHM: str = "HS256"

    # Realtime
    REALTIME_SALT: str = "salt"

    # Payment
    PAYMENT_PROVIDER_TOKEN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = Settings()
