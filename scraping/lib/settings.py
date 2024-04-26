import os

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE_PATH = os.getenv("ENV_FILE_PATH", "./scraping/.env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, env_file_encoding="utf-8", extra="ignore"
    )

    ## logging.py
    logging_level: str = "INFO"

    ## web_scrapper.py
    x_api_key: str
    x_api_secret: str


APP_SETTINGS = Settings()
