from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CHROMA_DB_PATH: str = "./chroma_db"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    API_TITLE: str = "StateLock Engine API"
    API_VERSION: str = "0.2.0"

    class Config:
        env_file = ".env"

settings = Settings()
