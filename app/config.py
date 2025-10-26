# app/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, PostgresDsn, AnyUrl


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_db: str

    gemini_api_key: str

    redis_url: AnyUrl = "redis://redis:6379/0"

    chrome_binary: str
    profile_dir: str
    profile_name: str
    driver_path: str

    pgadmin_default_email: str = "admin@admin.com"
    pgadmin_default_password: str = "admin"

    model_config = ConfigDict(env_file=".env")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
