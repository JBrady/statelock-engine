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
    API_NAME_MAX_CHARS: int = 120
    API_SESSION_ID_MAX_CHARS: int = 160
    API_CONTENT_MAX_CHARS: int = 12000
    API_TAG_MAX_CHARS: int = 64
    API_TAG_MAX_COUNT: int = 20
    AUTH_REQUIRED: bool = False
    STATELOCK_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
