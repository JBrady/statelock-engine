import chromadb

from app.core.config import settings


class Database:
    _client = None
    _collection = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        return cls._client

    @classmethod
    def get_collection(cls):
        if cls._collection is None:
            client = cls.get_client()
            cls._collection = client.get_or_create_collection(name="memory_blocks")
        return cls._collection

def get_db_collection():
    return Database.get_collection()
