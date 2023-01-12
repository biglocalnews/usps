import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False

    db_user: str = "postgres"
    db_pass: str = "pw"
    db_host: str = "localhost"
    db_name: str = "addresses"

    use_secure_cookies: bool = True

    class Config:
        secrets_dir = os.getenv("SECRETS_DIR", "/run/secrets")
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
