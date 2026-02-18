from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CHROMA_DB_PATH: str = "./chroma_db"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_PROVIDER: str = "local"
    HASH_EMBEDDING_DIM: int = 256
    QUERY_CANDIDATE_MULTIPLIER: int = 5
    API_TITLE: str = "StateLock Engine API"
    API_VERSION: str = "0.3.0"
    API_PREFIX: str = "/memories"
    API_DEFAULT_PAGE_SIZE: int = 100
    API_MAX_PAGE_SIZE: int = 500

    class Config:
        env_file = ".env"


settings = Settings()
