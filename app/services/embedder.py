import hashlib
from abc import ABC, abstractmethod
from typing import List, Optional

from sentence_transformers import SentenceTransformer

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


class HashEmbedder(BaseEmbedder):
    """
    Lightweight deterministic fallback embedder.
    Useful for local tests / CI where downloading embedding models is expensive.
    """

    def __init__(self, dim: int = 256):
        self.dim = max(32, dim)

    def encode(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        out = [0.0] * self.dim
        for i in range(self.dim):
            byte = digest[i % len(digest)]
            out[i] = (byte / 255.0) * 2.0 - 1.0
        return out


embedder: Optional[BaseEmbedder] = None


def reset_embedder() -> None:
    global embedder
    embedder = None


def get_embedder() -> BaseEmbedder:
    global embedder
    if embedder is not None:
        return embedder

    provider = settings.EMBEDDING_PROVIDER.strip().lower()
    if provider == "hash":
        embedder = HashEmbedder(settings.HASH_EMBEDDING_DIM)
    else:
        embedder = LocalEmbedder(settings.EMBEDDING_MODEL_NAME)
    return embedder
