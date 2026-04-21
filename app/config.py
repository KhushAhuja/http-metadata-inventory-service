from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "metadata_inventory"
    request_timeout: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
