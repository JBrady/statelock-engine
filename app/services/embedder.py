from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer
from typing import List
from app.core.config import settings

class BaseEmbedder(ABC):
    @abstractmethod
    def encode(self, text: str) -> List[float]:
        pass

class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

# Singleton instance
embedder = LocalEmbedder(settings.EMBEDDING_MODEL_NAME)

def get_embedder() -> BaseEmbedder:
    return embedder
